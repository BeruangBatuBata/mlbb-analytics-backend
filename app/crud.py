# In app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case, select, and_
from . import models
from typing import List, Optional

def update_match(db: Session, match_data: dict):
    """
    Final definitive version. This version adds a guard clause to reject
    any match from the API that is missing a team name.
    """
    try:
        # Step 1: Resolve dependencies (Teams, Tournament)
        team1_name, team2_name = None, None
        if 'match2opponents' in match_data and len(match_data['match2opponents']) >= 2:
            team1_name = match_data['match2opponents'][0].get('name')
            team2_name = match_data['match2opponents'][1].get('name')

        # --- THIS IS THE CRITICAL FIX ---
        # If either team name is missing (None or empty string), skip this match.
        if not team1_name or not team2_name:
            print(f"  - WARNING: Skipping match with Liquipedia ID {match_data.get('pageid', 'N/A')} due to missing team name.")
            return None
        # --------------------------------

        team1 = db.query(models.Team).filter_by(name=team1_name).first()
        if not team1: team1 = models.Team(name=team1_name); db.add(team1)
        
        team2 = db.query(models.Team).filter_by(name=team2_name).first()
        if not team2: team2 = models.Team(name=team2_name); db.add(team2)

        tournament_name = match_data.get('tournament', 'Unknown Tournament')
        tournament = db.query(models.Tournament).filter_by(name=tournament_name).first()
        if not tournament:
            tournament = models.Tournament(name=tournament_name)
            db.add(tournament)
        
        db.flush()

        # Step 2: Find or create the match
        match = db.query(models.Match).filter(and_(models.Match.team1_id == team1.id, models.Match.team2_id == team2.id, models.Match.match_date == match_data.get('date'))).first()
        series_winner = team1 if match_data.get('winner') == '1' else team2 if match_data.get('winner') == '2' else None
        if not match:
            match = models.Match(liquipedia_id=match_data['pageid'], tournament_id=tournament.id, team1_id=team1.id, team2_id=team2.id, winner_id=series_winner.id if series_winner else None, team1_score=match_data.get('team1score'), team2_score=match_data.get('team2score'), match_date=match_data.get('date'), details=match_data)
            db.add(match)
        else:
            match.winner_id = series_winner.id if series_winner else None; match.team1_score = match_data.get('team1score'); match.team2_score = match_data.get('team2score'); match.details = match_data
        db.flush()

        # Step 3: Process heroes and game data
        db.query(models.MatchHero).filter(models.MatchHero.match_id == match.id).delete(synchronize_session=False)
        all_hero_names = {extradata[f'team{tn}ban{i}'] for game in match_data.get('match2games', []) if isinstance(game, dict) for extradata in [game.get('extradata', {})] if isinstance(extradata, dict) for i in range(1, 6) for tn in [1, 2] if extradata.get(f'team{tn}ban{i}')}
        all_hero_names.update({p_data['champion'] for game in match_data.get('match2games', []) if isinstance(game, dict) for p_data in game.get('participants', {}).values() if isinstance(p_data, dict) and p_data.get('champion')})
        hero_map = {h.name: h for h in db.query(models.Hero).filter(models.Hero.name.in_(all_hero_names)).all()}
        for name in all_hero_names:
            if name not in hero_map: db.add(models.Hero(name=name))
        db.flush()
        hero_map = {h.name: h for h in db.query(models.Hero).filter(models.Hero.name.in_(all_hero_names)).all()}

        unique_hero_actions = set()
        for game_index, game in enumerate(match_data.get('match2games', [])):
            game_num = game_index + 1
            if not isinstance(game, dict): continue
            
            game_winner_team = team1 if game.get('winner') == '1' else team2 if game.get('winner') == '2' else None
            extradata = game.get('extradata', {})
            blue_team = team1 if extradata.get('team1side') == 'blue' else team2 if extradata.get('team2side') == 'blue' else None
            red_team = team1 if extradata.get('team1side') == 'red' else team2 if extradata.get('team2side') == 'red' else None
            
            if isinstance(extradata, dict):
                for i in range(1, 6):
                    for team_num in [1, 2]:
                        ban_key = f'team{team_num}ban{i}'
                        if extradata.get(ban_key) and extradata[ban_key] in hero_map:
                            hero_id = hero_map[extradata[ban_key]].id
                            team_id = team1.id if team_num == 1 else team2.id
                            unique_hero_actions.add((hero_id, team_id, 'ban', game_num, None, None))

            participants = game.get('participants', {})
            if isinstance(participants, dict):
                for key, data in participants.items():
                    if isinstance(data, dict) and data.get('champion') and data['champion'] in hero_map:
                        team_num_str, _ = key.split('_')
                        picking_team = team1 if int(team_num_str) == 1 else team2
                        is_win = (picking_team == game_winner_team) if game_winner_team else None
                        side = 'blue' if picking_team == blue_team else 'red' if picking_team == red_team else None
                        hero_id = hero_map[data['champion']].id
                        unique_hero_actions.add((hero_id, picking_team.id, 'pick', game_num, is_win, side))
        
        for hero_id, team_id, action_type, game_num, is_win_flag, side_flag in unique_hero_actions:
            db.add(models.MatchHero(
                match_id=match.id, hero_id=hero_id, team_id=team_id, 
                type=action_type, game_number=game_num, is_win=is_win_flag, side=side_flag
            ))
        
        db.commit()
    except Exception as e:
        db.rollback(); raise
    return match

def get_hero_stats(db: Session, tournament_names: Optional[List[str]] = None):
    matches_query = db.query(models.Match)
    matches_query = matches_query.filter(models.Match.winner_id != None)
    if tournament_names:
        matches_query = matches_query.join(models.Tournament).filter(models.Tournament.name.in_(tournament_names))
    total_matches = matches_query.count()
    if total_matches == 0:
        return {"summary": {}, "heroes": []}
    filtered_matches_subquery = matches_query.with_entities(models.Match.id).subquery()
    distinct_games_query = select(models.MatchHero.match_id, models.MatchHero.game_number).filter(models.MatchHero.match_id.in_(select(filtered_matches_subquery))).distinct()
    total_games = db.execute(select(func.count()).select_from(distinct_games_query.subquery())).scalar_one_or_none() or 0
    if total_games == 0:
        return {"summary": {"total_matches": total_matches, "total_games": 0}, "heroes": []}

    results = (
        db.query(
            models.Hero.name,
            func.sum(case((models.MatchHero.type == 'pick', 1), else_=0)).label("picks"),
            func.sum(case((models.MatchHero.type == 'ban', 1), else_=0)).label("bans"),
            func.sum(case((models.MatchHero.is_win == True, 1), else_=0)).label("wins"),
            func.sum(case((models.MatchHero.side == 'blue', 1), else_=0)).label("blue_picks"),
            func.sum(case(((models.MatchHero.side == 'blue') & (models.MatchHero.is_win == True), 1), else_=0)).label("blue_wins"),
            func.sum(case((models.MatchHero.side == 'red', 1), else_=0)).label("red_picks"),
            func.sum(case(((models.MatchHero.side == 'red') & (models.MatchHero.is_win == True), 1), else_=0)).label("red_wins")
        )
        .join(models.MatchHero, models.Hero.id == models.MatchHero.hero_id)
        .filter(models.MatchHero.match_id.in_(select(filtered_matches_subquery)))
        .group_by(models.Hero.name)
        .all()
    )
    
    hero_stats = []
    for row in results:
        hero_name, picks, bans, wins, blue_picks, blue_wins, red_picks, red_wins = row
        picks, bans, wins, blue_picks, blue_wins, red_picks, red_wins = picks or 0, bans or 0, wins or 0, blue_picks or 0, blue_wins or 0, red_picks or 0, red_wins or 0
        
        hero_stats.append({
            "hero_name": hero_name, "picks": picks, "bans": bans, "wins": wins,
            "losses": picks - wins,
            "win_rate": (wins / picks * 100) if picks > 0 else 0,
            "pick_rate": (picks / total_games * 100) if total_games > 0 else 0,
            "ban_rate": (bans / total_games * 100) if total_games > 0 else 0,
            "presence": ((picks + bans) / total_games * 100) if total_games > 0 else 0,
            "blue_picks": blue_picks, "blue_wins": blue_wins,
            "red_picks": red_picks, "red_wins": red_wins,
        })
    
    summary = { "total_matches": total_matches, "total_games": total_games, "total_heroes": len(hero_stats), "most_picked": max(hero_stats, key=lambda x: x['picks']) if hero_stats else None, "highest_win_rate": max([h for h in hero_stats if h['picks'] >= 5], key=lambda x: x['win_rate']) if any(h['picks'] >= 5 for h in hero_stats) else None, }
    return {"summary": summary, "heroes": hero_stats}

def get_hero_stats(
    db: Session, 
    tournament_names: Optional[List[str]] = None,
    stage_names: Optional[List[str]] = None,
    team_names: Optional[List[str]] = None
):
    """
    Calculates comprehensive statistics, with a corrected JSON filter.
    """
    matches_query = db.query(models.Match)

    # --- THIS IS THE CRITICAL FIX ---
    # Only consider matches that have a recorded winner.
    matches_query = matches_query.filter(models.Match.winner_id != None)
    # --------------------------------

    # Apply user filters
    if tournament_names:
        matches_query = matches_query.join(models.Tournament).filter(models.Tournament.name.in_(tournament_names))
    if stage_names:
        matches_query = matches_query.filter(models.Match.details['stage_type'].as_string().in_(stage_names))
    if team_names:
        team_ids_query = db.query(models.Team.id).filter(models.Team.name.in_(team_names))
        team_ids = [id_tuple[0] for id_tuple in team_ids_query.all()]
        if team_ids:
            matches_query = matches_query.filter(
                (models.Match.team1_id.in_(team_ids)) | (models.Match.team2_id.in_(team_ids))
            )

    total_matches = matches_query.count()
    if total_matches == 0:
        return {"summary": {"total_matches": 0, "total_games": 0, "total_heroes": 0}, "heroes": []}

    # (The rest of the function remains the same as our last correct version)
    # It correctly uses the filtered matches_query to calculate all stats.
    filtered_matches_subquery = matches_query.with_entities(models.Match.id).subquery()
    distinct_games_query = select(models.MatchHero.match_id, models.MatchHero.game_number).filter(models.MatchHero.match_id.in_(select(filtered_matches_subquery))).distinct()
    total_games = db.execute(select(func.count()).select_from(distinct_games_query.subquery())).scalar_one_or_none() or 0
    if total_games == 0:
        return {"summary": {"total_matches": total_matches, "total_games": 0, "total_heroes": 0}, "heroes": []}

    results = (
        db.query(
            models.Hero.name,
            func.sum(case((models.MatchHero.type == 'pick', 1), else_=0)).label("picks"),
            func.sum(case((models.MatchHero.type == 'ban', 1), else_=0)).label("bans"),
            func.sum(case((models.MatchHero.is_win == True, 1), else_=0)).label("wins"),
            func.sum(case((models.MatchHero.side == 'blue', 1), else_=0)).label("blue_picks"),
            func.sum(case(((models.MatchHero.side == 'blue') & (models.MatchHero.is_win == True), 1), else_=0)).label("blue_wins"),
            func.sum(case((models.MatchHero.side == 'red', 1), else_=0)).label("red_picks"),
            func.sum(case(((models.MatchHero.side == 'red') & (models.MatchHero.is_win == True), 1), else_=0)).label("red_wins")
        )
        .join(models.MatchHero, models.Hero.id == models.MatchHero.hero_id)
        .filter(models.MatchHero.match_id.in_(select(filtered_matches_subquery)))
        .group_by(models.Hero.name)
        .all()
    )
    
    # (The processing loop at the end of the function is unchanged, so it is abridged)
    hero_stats = []
    for row in results:
        hero_name, picks, bans, wins, blue_picks, blue_wins, red_picks, red_wins = row
        picks, bans, wins, blue_picks, blue_wins, red_picks, red_wins = picks or 0, bans or 0, wins or 0, blue_picks or 0, blue_wins or 0, red_picks or 0, red_wins or 0
        
        hero_stats.append({
            "hero_name": hero_name, "picks": picks, "bans": bans, "wins": wins,
            "losses": picks - wins,
            "win_rate": (wins / picks * 100) if picks > 0 else 0,
            "pick_rate": (picks / total_games * 100) if total_games > 0 else 0,
            "ban_rate": (bans / total_games * 100) if total_games > 0 else 0,
            "presence": ((picks + bans) / total_games * 100) if total_games > 0 else 0,
            "blue_picks": blue_picks, "blue_wins": blue_wins,
            "red_picks": red_picks, "red_wins": red_wins,
        })
    
    summary = { "total_matches": total_matches, "total_games": total_games, "total_heroes": len(hero_stats), "most_picked": max(hero_stats, key=lambda x: x['picks']) if hero_stats else None, "highest_win_rate": max([h for h in hero_stats if h['picks'] >= 5], key=lambda x: x['win_rate']) if any(h['picks'] >= 5 for h in hero_stats) else None, }
    return {"summary": summary, "heroes": hero_stats}

def get_all_tournaments(db: Session):
    return db.query(models.Tournament).order_by(models.Tournament.name).all()

def get_all_teams(db: Session, tournament_names: Optional[List[str]] = None):
    """
    Retrieves teams. If tournament_names are provided, it returns only the teams
    that played in those tournaments. Otherwise, it returns all teams.
    """
    query = db.query(models.Team)
    if tournament_names:
        # Find matches in the selected tournaments
        matches_in_tournaments = (
            db.query(models.Match.id)
            .join(models.Tournament)
            .filter(models.Tournament.name.in_(tournament_names))
            .subquery()
        )
        # Find unique team IDs from those matches
        team1_ids = db.query(models.Match.team1_id).filter(models.Match.id.in_(select(matches_in_tournaments)))
        team2_ids = db.query(models.Match.team2_id).filter(models.Match.id.in_(select(matches_in_tournaments)))
        all_team_ids = team1_ids.union(team2_ids).distinct()
        
        query = query.filter(models.Team.id.in_([t[0] for t in all_team_ids.all()]))

    return query.order_by(models.Team.name).all()

def get_all_stages(db: Session, tournament_names: Optional[List[str]] = None):
    """
    Retrieves stages. If tournament_names are provided, it returns only the stages
    that exist within those tournaments. Otherwise, it returns all unique stages.
    """
    query = db.query(models.Match.details['stage_type'].as_string().label("stage"))
    
    if tournament_names:
        query = query.join(models.Tournament).filter(models.Tournament.name.in_(tournament_names))
        
    distinct_stages = query.distinct().order_by("stage")
    return [row.stage for row in distinct_stages if row.stage]