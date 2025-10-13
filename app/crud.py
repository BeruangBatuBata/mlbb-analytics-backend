# In app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case, select, and_, or_
from . import models
from typing import Dict, List, Any, Optional

def update_tournament_and_match(db: Session, match_data: dict, region: str, split: str):
    """
    Creates or updates a tournament and processes the associated match data.
    (This is the complete, corrected version with hero processing)
    """
    try:
        # Step 1: Find or create the tournament
        tournament_name = match_data.get('tournament', 'Unknown Tournament')
        tournament = db.query(models.Tournament).filter_by(name=tournament_name).first()
        if not tournament:
            tournament = models.Tournament(name=tournament_name, region=region, split=split)
            db.add(tournament)
            db.flush()
        
        # Step 2: Find or create the teams
        team1_name, team2_name = None, None
        if 'match2opponents' in match_data and len(match_data['match2opponents']) >= 2:
            team1_name = match_data['match2opponents'][0].get('name')
            team2_name = match_data['match2opponents'][1].get('name')

        if not team1_name or not team2_name: return None

        team1 = db.query(models.Team).filter_by(name=team1_name).first()
        if not team1: team1 = models.Team(name=team1_name); db.add(team1)
        
        team2 = db.query(models.Team).filter_by(name=team2_name).first()
        if not team2: team2 = models.Team(name=team2_name); db.add(team2)
        
        db.flush()

        # Step 3: Find or create the match
        match = db.query(models.Match).filter(and_(models.Match.team1_id == team1.id, models.Match.team2_id == team2.id, models.Match.match_date == match_data.get('date'))).first()
        series_winner = team1 if match_data.get('winner') == '1' else team2 if match_data.get('winner') == '2' else None
        
        if not match:
            match = models.Match(liquipedia_id=match_data.get('pageid', 'N/A'), tournament_id=tournament.id, team1_id=team1.id, team2_id=team2.id, winner_id=series_winner.id if series_winner else None, team1_score=match_data.get('team1score'), team2_score=match_data.get('team2score'), match_date=match_data.get('date'), details=match_data)
            db.add(match)
        else:
            match.winner_id = series_winner.id if series_winner else None; match.team1_score = match_data.get('team1score'); match.team2_score = match_data.get('team2score'); match.details = match_data
        
        db.flush()

        # --- THIS IS THE MISSING LOGIC ---
        # Step 4: Process heroes and game data (picks/bans)
        
        # Clear old hero data for this match to prevent duplicates on re-runs
        db.query(models.MatchHero).filter(models.MatchHero.match_id == match.id).delete(synchronize_session=False)

        # Gather all unique hero names from picks and bans in the match data
        all_hero_names = set()
        for game in match_data.get('match2games', []):
            if not isinstance(game, dict): continue
            extradata = game.get('extradata', {})
            if isinstance(extradata, dict):
                for i in range(1, 6):
                    for team_num_str in ['1', '2']:
                        ban_hero = extradata.get(f'team{team_num_str}ban{i}')
                        if ban_hero: all_hero_names.add(ban_hero)
            
            for opp_data in game.get('opponents', []):
                for p in opp_data.get('players', []):
                    if isinstance(p, dict) and "champion" in p:
                        all_hero_names.add(p['champion'])
        
        # Ensure all heroes exist in the 'heroes' table, creating them if necessary
        existing_heroes = {h.name for h in db.query(models.Hero).filter(models.Hero.name.in_(all_hero_names)).all()}
        for name in all_hero_names:
            if name not in existing_heroes:
                db.add(models.Hero(name=name))
        if all_hero_names - existing_heroes:
             db.flush()

        hero_map = {h.name: h for h in db.query(models.Hero).filter(models.Hero.name.in_(all_hero_names)).all()}

        # Process each game in the match to save pick/ban data
        unique_hero_actions = set()
        for game_index, game in enumerate(match_data.get('match2games', [])):
            game_num = game_index + 1
            if not isinstance(game, dict): continue
            
            game_winner_team = team1 if game.get('winner') == '1' else team2 if game.get('winner') == '2' else None
            extradata = game.get('extradata', {})
            blue_team = team1 if extradata.get('team1side') == 'blue' else team2 if extradata.get('team2side') == 'blue' else None
            
            # Bans
            if isinstance(extradata, dict):
                for i in range(1, 6):
                    for team_num, team_obj in [('1', team1), ('2', team2)]:
                        ban_hero_name = extradata.get(f'team{team_num}ban{i}')
                        if ban_hero_name in hero_map:
                            hero_id = hero_map[ban_hero_name].id
                            unique_hero_actions.add((hero_id, team_obj.id, 'ban', game_num, None, None))

            # Picks
            for idx, opp_data in enumerate(game.get('opponents', [])):
                picking_team = team1 if idx == 0 else team2
                is_win = (picking_team == game_winner_team) if game_winner_team else None
                side = 'blue' if picking_team == blue_team else 'red'
                
                for p in opp_data.get('players', []):
                    if isinstance(p, dict) and p.get('champion') in hero_map:
                        hero_id = hero_map[p['champion']].id
                        unique_hero_actions.add((hero_id, picking_team.id, 'pick', game_num, is_win, side))

        # Add all unique actions to the session
        for hero_id, team_id, action_type, game_num, is_win_flag, side_flag in unique_hero_actions:
            db.add(models.MatchHero(match_id=match.id, hero_id=hero_id, team_id=team_id, type=action_type, game_number=game_num, is_win=is_win_flag, side=side_flag))
        # --- END OF MISSING LOGIC ---

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

def get_all_tournaments_grouped(db: Session, group_by: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves all tournaments, grouped by either 'split' or 'region'.
    """
    if group_by not in ['split', 'region']:
        group_by = 'split' # Default safely

    tournaments = db.query(models.Tournament).order_by(
        getattr(models.Tournament, group_by).desc(), 
        models.Tournament.name
    ).all()

    grouped_tournaments = {}
    for t in tournaments:
        key = getattr(t, group_by) or "Uncategorized"
        if key not in grouped_tournaments:
            grouped_tournaments[key] = []
        grouped_tournaments[key].append({"id": t.id, "name": t.name})
    
    return grouped_tournaments

def get_all_teams(
    db: Session, 
    tournament_names: Optional[List[str]] = None,
    hero_name: Optional[str] = None
):
    """
    Retrieves teams that have played in at least one completed match.
    Can be filtered by tournaments or by a hero.
    """
    # --- THIS IS THE CRITICAL FIX ---
    # The base query now joins with the matches table and filters for completed matches,
    # ensuring we only ever return teams that have actually played.
    query = (
        db.query(models.Team)
        .join(
            models.Match,
            or_(models.Team.id == models.Match.team1_id, models.Team.id == models.Match.team2_id)
        )
        .filter(models.Match.winner_id != None)
        .distinct()
    )
    # --- END OF FIX ---

    if hero_name:
        # If a hero name is provided, find teams that have picked that hero
        hero = db.query(models.Hero).filter(models.Hero.name == hero_name).first()
        if hero:
            team_ids_with_hero = (
                db.query(models.MatchHero.team_id)
                .filter(models.MatchHero.hero_id == hero.id)
                .filter(models.MatchHero.type == 'pick')
                .distinct()
            )
            # Further filter the base query
            query = query.filter(models.Team.id.in_([t[0] for t in team_ids_with_hero.all()]))
    
    elif tournament_names:
        # Further filter the base query by tournament
        query = query.join(
            models.Tournament, 
            models.Match.tournament_id == models.Tournament.id
        ).filter(models.Tournament.name.in_(tournament_names))

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

def get_hero_details(
    db: Session,
    hero_name: str,
    tournament_names: Optional[List[str]] = None,
    stage_names: Optional[List[str]] = None,
    team_names: Optional[List[str]] = None
):
    """
    Retrieves detailed statistics for a specific hero. (CORRECTED with team filter fix)
    """
    # --- THIS IS THE CRITICAL FIX ---
    # We need to get the team_ids early to use them in two places.
    team_ids = []
    if team_names:
        team_ids_query = db.query(models.Team.id).filter(models.Team.name.in_(team_names))
        team_ids = [id_tuple[0] for id_tuple in team_ids_query.all()]
    # --- END OF FIX ---

    # Base query for filtering matches based on user selection
    matches_query = db.query(models.Match.id).filter(models.Match.winner_id != None)
    if tournament_names:
        matches_query = matches_query.join(models.Tournament).filter(models.Tournament.name.in_(tournament_names))
    if stage_names:
        matches_query = matches_query.filter(models.Match.details['stage_type'].as_string().in_(stage_names))
    
    # Filter matches by the selected teams
    if team_ids:
        matches_query = matches_query.filter(or_(models.Match.team1_id.in_(team_ids), models.Match.team2_id.in_(team_ids)))
    
    filtered_matches_subquery = matches_query.subquery()

    hero = db.query(models.Hero).filter(models.Hero.name == hero_name).first()
    if not hero:
        return {"by_team": [], "vs_opponents": []}

    # Query 1: Performance by Team
    team_perf_query = (
        db.query(
            models.Team.name,
            func.count(models.MatchHero.hero_id).label("games_played"),
            func.sum(case((models.MatchHero.is_win == True, 1), else_=0)).label("wins")
        )
        .join(models.MatchHero, models.Team.id == models.MatchHero.team_id)
        .filter(models.MatchHero.match_id.in_(select(filtered_matches_subquery)))
        .filter(models.MatchHero.hero_id == hero.id)
        .filter(models.MatchHero.type == 'pick')
    )

    # --- THIS IS THE CRITICAL FIX ---
    # Apply the team filter to the final aggregation as well.
    if team_ids:
        team_perf_query = team_perf_query.filter(models.Team.id.in_(team_ids))
    # --- END OF FIX ---

    team_performance_results = team_perf_query.group_by(models.Team.name).order_by(func.count(models.MatchHero.hero_id).desc()).all()

    by_team_stats = [
        {"team_name": name, "games_played": games, "wins": wins, "win_rate": (wins / games * 100) if games > 0 else 0}
        for name, games, wins in team_performance_results
    ]

    # Query 2: Performance vs. Opponents (remains the same)
    HeroPick = models.MatchHero.__table__.alias('hero_pick')
    OpponentPick = models.MatchHero.__table__.alias('opponent_pick')
    hero_games = (
        select(HeroPick.c.match_id, HeroPick.c.game_number, HeroPick.c.team_id, HeroPick.c.is_win)
        .where(HeroPick.c.hero_id == hero.id)
        .where(HeroPick.c.type == 'pick')
        .where(HeroPick.c.match_id.in_(select(filtered_matches_subquery)))
        .subquery()
    )
    matchups = (
        db.query(
            models.Hero.name,
            func.count(OpponentPick.c.hero_id).label("games_faced"),
            func.sum(case((hero_games.c.is_win == True, 1), else_=0)).label("wins_against")
        )
        .join(OpponentPick, models.Hero.id == OpponentPick.c.hero_id)
        .join(
            hero_games,
            and_(
                OpponentPick.c.match_id == hero_games.c.match_id,
                OpponentPick.c.game_number == hero_games.c.game_number,
                OpponentPick.c.team_id != hero_games.c.team_id
            )
        )
        .filter(OpponentPick.c.type == 'pick')
        .group_by(models.Hero.name)
        .order_by(func.count(OpponentPick.c.hero_id).desc())
        .all()
    )
    vs_opponents_stats = [
        {"opponent_hero_name": name, "games_faced": games, "wins_against": wins, "win_rate_vs": (wins / games * 100) if games > 0 else 0}
        for name, games, wins in matchups
    ]

    return {"by_team": by_team_stats, "vs_opponents": vs_opponents_stats}

def get_all_hero_names(db: Session):
    """Retrieves a list of all hero names, sorted alphabetically."""
    return db.query(models.Hero.name).order_by(models.Hero.name).all()