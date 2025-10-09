# --- SHARED DATA PROCESSING LOGIC ---

TEAM_NORMALIZATION = {
    "AP.Bren": "Falcons AP.Bren",
    "Falcons AP.Bren": "Falcons AP.Bren",
    "ECHO": "Team Liquid PH",
    "Team Liquid PH": "Team Liquid PH",
}

def normalize_team(n):
    return TEAM_NORMALIZATION.get((n or "").strip(), (n or "").strip())

def get_stage_info(pagename, section):
    source_string = section if '/' in section else pagename
    stage_type = source_string.split('/')[-1].replace('_', ' ').strip()
    stage_type_lower = stage_type.lower()
    
    if "playoffs" in stage_type_lower or "finals" in stage_type_lower or "knockout" in stage_type_lower:
        stage_priority = 40
    elif "rumble" in stage_type_lower or "play-in" in stage_type_lower:
        stage_priority = 30
    elif "stage 2" in stage_type_lower:
        stage_priority = 20
    elif "regular season" in stage_type_lower or "group" in stage_type_lower or "swiss" in stage_type_lower or "week" in stage_type_lower or "stage 1" in stage_type_lower:
        stage_priority = 10
    else:
        stage_priority = 99
        
    return stage_type if stage_type else "Uncategorized", stage_priority

def parse_and_enrich_matches(matches_raw, tournament_name):
    enriched_matches = []
    for m in matches_raw:
        if not isinstance(m, dict):
            continue
        
        m['tournament'] = tournament_name
        
        if "match2opponents" in m:
            for opp in m["match2opponents"]:
                opp["name"] = normalize_team(opp.get("name"))

        stage_type, stage_priority = get_stage_info(m.get("pagename", ""), m.get("section", ""))
        m['stage_type'] = stage_type
        m['stage_priority'] = stage_priority
        
        enriched_matches.append(m)
    return enriched_matches