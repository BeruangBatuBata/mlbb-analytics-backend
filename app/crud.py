# In app/crud.py
from sqlalchemy.orm import Session
from . import models

def update_match(db: Session, match_data: dict):
    """
    Creates or updates a match and all its hero picks/bans in a single,
    robust, and atomic database transaction. This is the definitive version.
    """
    try:
        # Step 1: Gather all unique hero names from the entire match payload first.
        all_hero_names = set()
        games = match_data.get('match2games', [])
        if not isinstance(games, list): games = []

        for game in games:
            if not isinstance(game, dict): continue
            
            # Gather from bans
            extradata = game.get('extradata', {})
            if isinstance(extradata, dict):
                for i in range(1, 6):
                    for team_num in [1, 2]:
                        ban_key = f'team{team_num}ban{i}'
                        if ban_key in extradata and extradata[ban_key]:
                            all_hero_names.add(extradata[ban_key])
            
            # Gather from picks
            participants = game.get('participants', {})
            if isinstance(participants, dict):
                for key, data in participants.items():
                    if isinstance(data, dict) and 'champion' in data and data['champion']:
                        all_hero_names.add(data['champion'])

        # Step 2: Efficiently get or create all necessary heroes in one batch.
        # First, find existing heroes.
        hero_map = {h.name: h for h in db.query(models.Hero).filter(models.Hero.name.in_(all_hero_names)).all()}
        # Then, create the ones that don't exist.
        for name in all_hero_names:
            if name not in hero_map:
                new_hero = models.Hero(name=name)
                db.add(new_hero)
                hero_map[name] = new_hero
        # Flush ONCE to get IDs for all newly created heroes.
        db.flush() 

        # Step 3: Get or create other related objects (Teams, Tournament).
        tournament = db.query(models.Tournament).filter_by(name=match_data.get('tournament', 'Unknown Tournament')).first()
        if not tournament:
            tournament = models.Tournament(name=match_data.get('tournament', 'Unknown Tournament'))
            db.add(tournament)
        
        team1_name, team2_name = "Unknown Team", "Unknown Team"
        if 'match2opponents' in match_data and len(match_data['match2opponents']) >= 2:
            team1_name = match_data['match2opponents'][0].get('name', 'Unknown Team')
            team2_name = match_data['match2opponents'][1].get('name', 'Unknown Team')
        
        team1 = db.query(models.Team).filter_by(name=team1_name).first()
        if not team1: team1 = models.Team(name=team1_name); db.add(team1)
        
        team2 = db.query(models.Team).filter_by(name=team2_name).first()
        if not team2: team2 = models.Team(name=team2_name); db.add(team2)
        
        db.flush() # Flush to get IDs for new teams/tournaments.

        winner = team1 if match_data.get('winner') == '1' else team2 if match_data.get('winner') == '2' else None
        
        # Step 4: Get or create the Match object.
        match = db.query(models.Match).filter_by(liquipedia_id=match_data['pageid']).first()
        if not match:
            match = models.Match(liquipedia_id=match_data['pageid'])
            db.add(match)
            db.flush() # Get the match ID before use.

        # Step 5: Update match details and delete old hero associations.
        match.tournament_id=tournament.id; match.team1_id=team1.id; match.team2_id=team2.id
        match.winner_id=winner.id if winner else None; match.team1_score=match_data.get('team1score')
        match.team2_score=match_data.get('team2score'); match.match_date=match_data.get('date')
        match.details=match_data
        
        db.query(models.MatchHero).filter(models.MatchHero.match_id == match.id).delete(synchronize_session=False)

        # Step 6: Create new MatchHero associations using the hero_map (which now has all IDs).
        for game in games:
            if not isinstance(game, dict): continue
            game_num = game.get('match2gameid', 0)
            
            extradata = game.get('extradata', {})
            if isinstance(extradata, dict):
                for i in range(1, 6):
                    for team_num in [1, 2]:
                        ban_key = f'team{team_num}ban{i}'
                        if ban_key in extradata and extradata[ban_key]:
                            hero = hero_map[extradata[ban_key]]
                            team = team1 if team_num == 1 else team2
                            db.add(models.MatchHero(match_id=match.id, hero_id=hero.id, team_id=team.id, type='ban', game_number=game_num))
            
            participants = game.get('participants', {})
            if isinstance(participants, dict):
                for key, data in participants.items():
                    if isinstance(data, dict) and 'champion' in data and data['champion']:
                        team_num_str, _ = key.split('_')
                        hero = hero_map[data['champion']]
                        team = team1 if int(team_num_str) == 1 else team2
                        db.add(models.MatchHero(match_id=match.id, hero_id=hero.id, team_id=team.id, type='pick', game_number=game_num))
        
        # Step 7: Commit the entire transaction.
        db.commit()
        print(f"Successfully processed and saved match: {team1.name} vs {team2.name}")

    except Exception as e:
        print(f"An error occurred during the database transaction: {e}")
        db.rollback()
        raise

    return match