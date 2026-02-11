"""
02_transform.py - Data Transformation & Aggregation

Reads cleaned match data (required) plus optional enrichment CSVs
(FPL players, xG data) and produces a single JSON file consumed
by the dashboard frontend.

If enrichment CSVs are missing, optional sections are set to null.
The dashboard handles this gracefully with fallback messages.

Run: python scripts/02_transform.py
"""

import os
import sys
import json
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("ERROR: pandas is required. Run: pip install pandas")
    sys.exit(1)

from config import ACTIVE_SEASONS, CURRENT_SEASON

# -- PATHS -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data')

FULL_SEASON_MATCHES = 380


def safe_int(val):
    """Convert numpy int to Python int for JSON serialization."""
    try:
        if pd.isna(val):
            return 0
    except (TypeError, ValueError):
        pass
    return int(val)


def safe_float(val, decimals=2):
    """Convert numpy float to Python float for JSON serialization."""
    try:
        if pd.isna(val):
            return 0.0
    except (TypeError, ValueError):
        pass
    return round(float(val), decimals)


def safe_str(val):
    """Convert value to string, returning empty string for NaN."""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val)


def sanitize_for_json(obj):
    """Recursively replace NaN/Infinity with JSON-safe values."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if pd.isna(obj) or obj != obj:
            return 0.0
        if obj == float('inf') or obj == float('-inf'):
            return 0.0
        return obj
    return obj


def main():
    # -- LOAD REQUIRED DATA ------------------------------------------------
    matches_path = os.path.join(CLEAN_DIR, 'matches_clean.csv')
    if not os.path.exists(matches_path):
        print("ERROR: matches_clean.csv not found. Run 01_clean.py first.")
        sys.exit(1)

    df = pd.read_csv(matches_path)
    print(f"Loaded match data: {len(df)} rows")

    # -- LOAD OPTIONAL ENRICHMENT DATA -------------------------------------
    has_fpl = False
    players_df = None
    try:
        players_df = pd.read_csv(os.path.join(CLEAN_DIR, 'players.csv'))
        has_fpl = True
        print(f"Loaded FPL player data: {len(players_df)} rows")
    except FileNotFoundError:
        print("FPL player data not available -- skipping player enrichment")

    has_xg = False
    xg_teams_df = None
    xg_players_df = None
    try:
        xg_teams_df = pd.read_csv(os.path.join(CLEAN_DIR, 'xg_teams.csv'))
        xg_players_df = pd.read_csv(os.path.join(CLEAN_DIR, 'xg_players.csv'))
        has_xg = True
        print(f"Loaded xG team data: {len(xg_teams_df)} rows")
        print(f"Loaded xG player data: {len(xg_players_df)} rows")
    except FileNotFoundError:
        print("xG data not available -- skipping xG enrichment")

    # -- CURRENT SEASON DATA -----------------------------------------------
    current = df[df['season'] == CURRENT_SEASON].copy()
    matches_played = len(current)
    print(f"\nCurrent season ({CURRENT_SEASON}): {matches_played} matches")

    # -- SEASON STATUS -----------------------------------------------------
    # Detect whether the season is complete or in progress.
    # Teams may have different games played due to postponements.
    home_counts = current.groupby('home_team').size()
    away_counts = current.groupby('away_team').size()
    games_per_team = home_counts.add(away_counts, fill_value=0)
    matchdays_played = safe_int(games_per_team.max())
    season_complete = matches_played >= FULL_SEASON_MATCHES

    last_date = current['date'].max() if len(current) > 0 else ""

    season_status = {
        "matches_played": safe_int(matches_played),
        "matches_total": FULL_SEASON_MATCHES,
        "matchdays_played": matchdays_played,
        "matchdays_total": 38,
        "is_complete": season_complete,
        "last_match_date": str(last_date),
    }

    # -- LEAGUE TABLE ------------------------------------------------------
    def build_team_stats(team_matches, team_name):
        home = team_matches[team_matches['home_team'] == team_name]
        away = team_matches[team_matches['away_team'] == team_name]

        hw = len(home[home['result'] == 'H'])
        hd = len(home[home['result'] == 'D'])
        hl = len(home[home['result'] == 'A'])
        aw = len(away[away['result'] == 'A'])
        ad = len(away[away['result'] == 'D'])
        al = len(away[away['result'] == 'H'])

        gf = safe_int(home['home_goals'].sum() + away['away_goals'].sum())
        ga = safe_int(home['away_goals'].sum() + away['home_goals'].sum())

        total_shots = safe_int(home['home_shots'].sum() + away['away_shots'].sum())
        total_sot = safe_int(home['home_shots_on_target'].sum()
                             + away['away_shots_on_target'].sum())
        shot_acc = safe_float(total_sot / total_shots * 100) if total_shots > 0 else 0.0

        # Clean sheets: matches where the team conceded 0 goals
        cs_home = len(home[home['away_goals'] == 0])
        cs_away = len(away[away['home_goals'] == 0])

        played = hw + hd + hl + aw + ad + al
        won = hw + aw
        drawn = hd + ad
        lost = hl + al
        pts = won * 3 + drawn

        return {
            "team": team_name,
            "played": played,
            "won": won,
            "drawn": drawn,
            "lost": lost,
            "goals_for": gf,
            "goals_against": ga,
            "goal_difference": gf - ga,
            "points": pts,
            "home_won": hw,
            "home_drawn": hd,
            "home_lost": hl,
            "away_won": aw,
            "away_drawn": ad,
            "away_lost": al,
            "clean_sheets": cs_home + cs_away,
            "total_shots": total_shots,
            "total_shots_on_target": total_sot,
            "shot_accuracy": shot_acc,
            "goals_per_game": safe_float(gf / played) if played > 0 else 0.0,
        }

    teams = sorted(set(current['home_team'].unique()) | set(current['away_team'].unique()))
    table_rows = [build_team_stats(current, t) for t in teams]

    # Sort: points desc, then goal difference desc, then goals scored desc
    table_rows.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))
    for i, row in enumerate(table_rows):
        row['position'] = i + 1

    # -- CUMULATIVE POINTS (for points race chart) -------------------------
    # Build matchday-by-matchday cumulative points for each team.
    current_sorted = current.sort_values('date')
    cumulative_points = {}

    for team in teams:
        home_matches = current_sorted[current_sorted['home_team'] == team].copy()
        away_matches = current_sorted[current_sorted['away_team'] == team].copy()

        home_matches = home_matches.assign(
            pts=home_matches['result'].map({'H': 3, 'D': 1, 'A': 0})
        )
        away_matches = away_matches.assign(
            pts=away_matches['result'].map({'A': 3, 'D': 1, 'H': 0})
        )

        all_matches = pd.concat([
            home_matches[['date', 'pts']],
            away_matches[['date', 'pts']]
        ]).sort_values('date').reset_index(drop=True)

        all_matches['cumulative'] = all_matches['pts'].cumsum()

        cumulative_points[team] = [
            {"matchday": i + 1, "points": safe_int(row['cumulative'])}
            for i, row in all_matches.iterrows()
        ]

    # -- MONTHLY TRENDS ----------------------------------------------------
    current_with_month = current.copy()
    current_with_month['month'] = current_with_month['date'].str[:7]

    monthly = current_with_month.groupby('month').agg(
        matches=('match_id', 'count'),
        total_goals=('total_goals', 'sum'),
        home_wins=('result', lambda x: (x == 'H').sum()),
        draws=('result', lambda x: (x == 'D').sum()),
        away_wins=('result', lambda x: (x == 'A').sum()),
    ).reset_index()

    monthly['avg_goals'] = (monthly['total_goals'] / monthly['matches']).round(2)
    monthly = monthly.sort_values('month')

    monthly_trends = [
        {
            "month": row['month'],
            "matches": safe_int(row['matches']),
            "total_goals": safe_int(row['total_goals']),
            "avg_goals": safe_float(row['avg_goals']),
            "home_wins": safe_int(row['home_wins']),
            "draws": safe_int(row['draws']),
            "away_wins": safe_int(row['away_wins']),
        }
        for _, row in monthly.iterrows()
    ]

    # -- HOME VS AWAY SPLIT ------------------------------------------------
    home_wins = safe_int((current['result'] == 'H').sum())
    draws = safe_int((current['result'] == 'D').sum())
    away_wins = safe_int((current['result'] == 'A').sum())
    total = matches_played if matches_played > 0 else 1

    home_away = {
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
        "home_goals_avg": safe_float(current['home_goals'].mean()),
        "away_goals_avg": safe_float(current['away_goals'].mean()),
        "total_matches": safe_int(matches_played),
        "home_win_pct": safe_float(home_wins / total * 100),
        "draw_pct": safe_float(draws / total * 100),
        "away_win_pct": safe_float(away_wins / total * 100),
    }

    # -- REFEREE STATS -----------------------------------------------------
    ref_groups = current.groupby('referee')
    ref_stats = []
    for ref, group in ref_groups:
        n = len(group)
        if n < 3:
            continue
        ref_stats.append({
            "referee": ref,
            "matches": safe_int(n),
            "avg_goals": safe_float(group['total_goals'].mean()),
            "avg_fouls": safe_float(group['total_fouls'].mean()),
            "avg_cards": safe_float(group['total_cards'].mean()),
            "total_reds": safe_int(group['home_reds'].sum() + group['away_reds'].sum()),
        })
    ref_stats.sort(key=lambda x: -x['avg_cards'])

    # -- SCORELINE FREQUENCY -----------------------------------------------
    current_scores = current.copy()
    current_scores['score'] = (current_scores['home_goals'].astype(str)
                               + '-' + current_scores['away_goals'].astype(str))
    score_counts = current_scores['score'].value_counts().head(10)
    scoreline_frequency = [
        {"score": score, "count": safe_int(count)}
        for score, count in score_counts.items()
    ]

    # -- SEASON COMPARISON -------------------------------------------------
    season_comparison = []
    for season_label in ACTIVE_SEASONS.keys():
        s = df[df['season'] == season_label]
        if len(s) == 0:
            continue
        season_comparison.append({
            "season": season_label,
            "matches": safe_int(len(s)),
            "avg_goals": safe_float(s['total_goals'].mean()),
            "avg_cards": safe_float(s['total_cards'].mean()),
            "home_win_pct": safe_float((s['result'] == 'H').sum() / len(s) * 100),
            "avg_fouls": safe_float(s['total_fouls'].mean()),
        })

    # -- CONDITIONAL: xG TABLE + SCATTER -----------------------------------
    xg_table = None
    xg_vs_actual = None
    shot_quality = None

    if has_xg and xg_teams_df is not None:
        xg_table_rows = []
        xg_scatter = []
        shot_quality_rows = []

        for _, row in xg_teams_df.iterrows():
            team = row['team']
            xg_for = safe_float(row.get('xg_for', 0))
            xg_against = safe_float(row.get('xg_against', 0))
            goals_for = safe_int(row.get('goals_for', 0))
            goals_against = safe_int(row.get('goals_against', 0))

            # xPoints estimation: 3 * xW + 1 * xD
            # Simplified: use xG difference as proxy
            xg_diff = xg_for - xg_against

            # Find actual points from league table
            actual_pts = 0
            for tr in table_rows:
                if tr['team'] == team:
                    actual_pts = tr['points']
                    break

            xg_table_rows.append({
                "team": team,
                "xg_for": xg_for,
                "xg_against": xg_against,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "xg_difference": safe_float(xg_diff),
                "actual_points": actual_pts,
            })

            xg_scatter.append({
                "team": team,
                "total_xg": xg_for,
                "actual_goals": goals_for,
                "difference": safe_float(goals_for - xg_for),
            })

            # Shot quality uses total shots from the league table for the denominator
            team_table = next((t for t in table_rows if t['team'] == team), None)
            if team_table and team_table['total_shots'] > 0:
                total_shots_team = team_table['total_shots']
                shot_quality_rows.append({
                    "team": team,
                    "total_shots": total_shots_team,
                    # 3 decimal places -- the range across teams is only ~0.10-0.15,
                    # so 2dp collapses half the league to the same value
                    "xg_per_shot": safe_float(xg_for / total_shots_team, 3),
                })

        xg_table_rows.sort(key=lambda x: -x['xg_difference'])
        xg_table = xg_table_rows
        xg_vs_actual = xg_scatter
        shot_quality_rows.sort(key=lambda x: -x['xg_per_shot'])
        shot_quality = shot_quality_rows

    # -- CONDITIONAL: TOP SCORERS ------------------------------------------
    top_scorers = None
    player_value = None

    if has_xg and xg_players_df is not None:
        xg_players_clean = xg_players_df.dropna(subset=['player_name'])
        scorers = xg_players_clean[xg_players_clean['goals'] > 0].copy()
        scorers = scorers.sort_values('goals', ascending=False).head(10)

        top_scorers = []
        for _, row in scorers.iterrows():
            goals = safe_int(row['goals'])
            xg_val = safe_float(row.get('xg', 0))
            top_scorers.append({
                "player_name": safe_str(row['player_name']),
                "team": safe_str(row['team']),
                "goals": goals,
                "assists": safe_int(row.get('assists', 0)),
                "xg": xg_val,
                "xa": safe_float(row.get('xa', 0)),
                "minutes": safe_int(row.get('minutes', 0)),
                "goals_minus_xg": safe_float(goals - xg_val),
                "position": str(row.get('position', '')),
            })

    if has_fpl and players_df is not None:
        value_df = players_df[players_df['goals'] > 0].copy()
        if 'price' in value_df.columns:
            value_df = value_df[value_df['price'] > 0]
            value_df['goals_per_million'] = (value_df['goals'] / value_df['price']).round(2)
            value_df = value_df.sort_values('goals_per_million', ascending=False).head(10)

            player_value = [
                {
                    "player_name": safe_str(row.get('player_name', '')),
                    "team": safe_str(row['team']),
                    "price": safe_float(row['price'], 1),
                    "goals": safe_int(row['goals']),
                    "goals_per_million": safe_float(row['goals_per_million']),
                }
                for _, row in value_df.iterrows()
            ]

    # -- CONDITIONAL: PLAYER LEADERBOARDS ----------------------------------
    # Comprehensive player stats from FPL data, enriched with xG where available
    player_leaderboards = None

    if has_fpl and players_df is not None:
        fpl = players_df.copy()

        def strip_accents(s):
            """Remove diacritics so Ekitiké matches Ekitike, etc."""
            nfkd = unicodedata.normalize('NFKD', s)
            return ''.join(c for c in nfkd if not unicodedata.combining(c))

        # Build multiple xG lookup indexes for robust name matching.
        # FPL uses short names (Haaland), Understat uses full names (Erling Haaland),
        # and transferred players have comma-separated teams in Understat.
        xg_by_name = {}       # (full_name, team) -> data
        xg_by_last = {}       # (last_name_normalized, team) -> data
        xg_by_team = {}       # team -> list of (name_normalized, data) for substring search
        if has_xg and xg_players_df is not None:
            for _, xr in xg_players_df.dropna(subset=['player_name']).iterrows():
                name = safe_str(xr['player_name'])
                teams_raw = safe_str(xr['team'])
                data = {
                    "xg": safe_float(xr.get('xg', 0)),
                    "xa": safe_float(xr.get('xa', 0)),
                    "shots": safe_int(xr.get('shots', 0)),
                    "key_passes": safe_int(xr.get('key_passes', 0)),
                    "npxg": safe_float(xr.get('npxg', 0)),
                }
                name_norm = strip_accents(name).lower()
                parts = name_norm.split()
                last = parts[-1] if parts else name_norm

                # Understat uses comma-separated teams for mid-season transfers
                teams = [t.strip() for t in teams_raw.split(',')]
                for team in teams:
                    xg_by_name[(name, team)] = data
                    xg_by_last[(last, team)] = data
                    if team not in xg_by_team:
                        xg_by_team[team] = []
                    xg_by_team[team].append((name_norm, data))

        def enrich(row):
            """Match FPL player to Understat xG data using multiple strategies."""
            pname = safe_str(row['player_name'])
            fname = safe_str(row.get('full_name', ''))
            team = safe_str(row['team'])

            # 1. Exact match on (short_name, team) -- covers single-name players
            result = xg_by_name.get((pname, team))
            if result:
                return result

            # 2. Exact match on (full_name, team) -- covers identical full names
            if fname:
                result = xg_by_name.get((fname, team))
                if result:
                    return result

            # 3. Last name match -- FPL "Haaland" matches last word of "Erling Haaland"
            pname_norm = strip_accents(pname).lower()
            result = xg_by_last.get((pname_norm, team))
            if result:
                return result

            # 4. Dot-split fallback -- FPL uses "B.Fernandes" or "Kroupi.Jr"
            # Try each dot-separated part as a last name match
            if '.' in pname:
                parts = [strip_accents(p).lower() for p in pname.split('.') if len(p) > 2]
                for part in parts:
                    result = xg_by_last.get((part, team))
                    if result:
                        return result

            # 5. Substring search -- handles "Enzo" matching "enzo fernandez"
            candidates = xg_by_team.get(team, [])
            clean = pname_norm.rstrip('.')
            for xg_name_norm, data in candidates:
                if clean in xg_name_norm:
                    return data

            return {}

        def per90(stat, minutes):
            """Calculate per-90-minute rate."""
            if minutes < 90:
                return 0
            return safe_float(stat / minutes * 90, 2)

        # -- GOAL SCORERS (top 20) --
        scorers_df = fpl[fpl['goals'] > 0].sort_values('goals', ascending=False).head(20)
        goal_scorers = []
        for _, row in scorers_df.iterrows():
            xg_data = enrich(row)
            mins = safe_int(row['minutes'])
            goals = safe_int(row['goals'])
            goal_scorers.append({
                "rank": len(goal_scorers) + 1,
                "player_name": safe_str(row['player_name']),
                "team": safe_str(row['team']),
                "position": safe_str(row['position']),
                "goals": goals,
                "assists": safe_int(row['assists']),
                "minutes": mins,
                "goals_per_90": per90(goals, mins),
                "price": safe_float(row.get('price', 0), 1),
                "xg": xg_data.get('xg'),
                "shots": xg_data.get('shots'),
            })

        # -- ASSIST LEADERS (top 15) --
        assists_df = fpl[fpl['assists'] > 0].sort_values('assists', ascending=False).head(15)
        assist_leaders = []
        for _, row in assists_df.iterrows():
            xg_data = enrich(row)
            mins = safe_int(row['minutes'])
            assists = safe_int(row['assists'])
            assist_leaders.append({
                "rank": len(assist_leaders) + 1,
                "player_name": safe_str(row['player_name']),
                "team": safe_str(row['team']),
                "position": safe_str(row['position']),
                "assists": assists,
                "goals": safe_int(row['goals']),
                "minutes": mins,
                "assists_per_90": per90(assists, mins),
                "xa": xg_data.get('xa'),
                "key_passes": xg_data.get('key_passes'),
                "price": safe_float(row.get('price', 0), 1),
            })

        # -- MINUTES IRON MEN (top player per team by minutes) --
        iron_men = []
        for team_name in sorted(fpl['team'].unique()):
            team_players = fpl[fpl['team'] == team_name]
            top_player = team_players.sort_values('minutes', ascending=False).iloc[0]
            mins = safe_int(top_player['minutes'])
            iron_men.append({
                "player_name": safe_str(top_player['player_name']),
                "team": team_name,
                "position": safe_str(top_player['position']),
                "minutes": mins,
                "games_equivalent": safe_float(mins / 90, 1),
                "goals": safe_int(top_player['goals']),
                "assists": safe_int(top_player['assists']),
            })
        iron_men.sort(key=lambda x: -x['minutes'])

        # -- GOALS BY POSITION --
        goals_by_pos = []
        for pos in ['FWD', 'MID', 'DEF', 'GK']:
            pos_df = fpl[fpl['position'] == pos]
            total_g = safe_int(pos_df['goals'].sum())
            total_a = safe_int(pos_df['assists'].sum())
            count = len(pos_df[pos_df['minutes'] > 0])
            goals_by_pos.append({
                "position": pos,
                "total_goals": total_g,
                "total_assists": total_a,
                "player_count": count,
                "avg_goals": safe_float(total_g / count if count > 0 else 0, 2),
            })

        # -- BEST VALUE (goals + assists per million) --
        active = fpl[(fpl['minutes'] >= 450) & (fpl['price'] > 0)].copy()
        active['ga'] = active['goals'] + active['assists']
        active['ga_per_million'] = (active['ga'] / active['price']).round(2)
        best_value = active.sort_values('ga_per_million', ascending=False).head(15)
        value_players = []
        for _, row in best_value.iterrows():
            value_players.append({
                "rank": len(value_players) + 1,
                "player_name": safe_str(row['player_name']),
                "team": safe_str(row['team']),
                "position": safe_str(row['position']),
                "price": safe_float(row['price'], 1),
                "goals": safe_int(row['goals']),
                "assists": safe_int(row['assists']),
                "ga_per_million": safe_float(row['ga_per_million']),
                "minutes": safe_int(row['minutes']),
            })

        # -- DISCIPLINARY (most cards) --
        fpl['total_cards'] = fpl['yellow_cards'] + fpl['red_cards']
        card_df = fpl[fpl['total_cards'] > 0].sort_values('total_cards', ascending=False).head(10)
        most_cards = []
        for _, row in card_df.iterrows():
            most_cards.append({
                "player_name": safe_str(row['player_name']),
                "team": safe_str(row['team']),
                "position": safe_str(row['position']),
                "yellows": safe_int(row['yellow_cards']),
                "reds": safe_int(row['red_cards']),
                "total_cards": safe_int(row['total_cards']),
                "minutes": safe_int(row['minutes']),
            })

        player_leaderboards = {
            "goal_scorers": goal_scorers,
            "assist_leaders": assist_leaders,
            "iron_men": iron_men,
            "goals_by_position": goals_by_pos,
            "best_value": value_players,
            "most_cards": most_cards,
        }
        print(f"Player leaderboards: {len(goal_scorers)} scorers, {len(assist_leaders)} assisters, {len(iron_men)} iron men")

    # -- CONDITIONAL: MONEY VS POINTS ---------------------------------------
    # The core thesis: does squad spending predict league position?
    # FPL player prices are a proxy for market value. Sum per team = squad value.
    money_vs_points = None

    if has_fpl and players_df is not None and 'price' in players_df.columns:
        squad_values = players_df.groupby('team')['price'].sum().reset_index()
        squad_values.columns = ['team', 'squad_value']

        money_rows = []
        for _, sv in squad_values.iterrows():
            team = sv['team']
            value = safe_float(sv['squad_value'], 1)
            # Find this team's points from league table
            team_row = next((t for t in table_rows if t['team'] == team), None)
            if not team_row:
                continue
            pts = team_row['points']
            played = team_row['played']

            money_rows.append({
                "team": team,
                "squad_value": value,
                "points": pts,
                "played": played,
                "points_per_match": safe_float(pts / played if played > 0 else 0),
            })

        if money_rows:
            # Compute expected points from a simple linear regression of value vs pts
            values = [r['squad_value'] for r in money_rows]
            points = [r['points'] for r in money_rows]
            n = len(values)
            mean_v = sum(values) / n
            mean_p = sum(points) / n
            cov = sum((v - mean_v) * (p - mean_p) for v, p in zip(values, points))
            var = sum((v - mean_v) ** 2 for v in values)
            slope = cov / var if var > 0 else 0
            intercept = mean_p - slope * mean_v

            for row in money_rows:
                expected = slope * row['squad_value'] + intercept
                row['expected_points'] = safe_float(expected)
                row['over_under'] = safe_float(row['points'] - expected)

            money_rows.sort(key=lambda x: -x['over_under'])

            money_vs_points = {
                "teams": money_rows,
                "regression": {
                    "slope": safe_float(slope, 4),
                    "intercept": safe_float(intercept),
                    "r_squared": safe_float(
                        (cov ** 2) / (var * sum((p - mean_p) ** 2 for p in points))
                        if var > 0 and sum((p - mean_p) ** 2 for p in points) > 0
                        else 0,
                        3
                    ),
                },
            }
            print(f"Money vs Points: R-squared = {money_vs_points['regression']['r_squared']}")

    # -- EXPORT ------------------------------------------------------------
    total_goals = safe_int(current['total_goals'].sum())

    output = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "season": CURRENT_SEASON,
        "source": "football-data.co.uk",
        "total_matches": safe_int(matches_played),
        "total_goals": total_goals,
        "goals_per_match": safe_float(total_goals / total if total > 0 else 0),
        "season_status": season_status,
        "league_table": table_rows,
        "cumulative_points": cumulative_points,
        "monthly_trends": monthly_trends,
        "home_away": home_away,
        "referee_stats": ref_stats,
        "scoreline_frequency": scoreline_frequency,
        "season_comparison": season_comparison,
        # Optional sections -- null when data unavailable
        "xg_table": xg_table,
        "xg_vs_actual": xg_vs_actual,
        "top_scorers": top_scorers,
        "shot_quality": shot_quality,
        "player_value": player_value,
        "player_leaderboards": player_leaderboards,
        "money_vs_points": money_vs_points,
    }

    # Scrub any lingering NaN/Infinity before serialization -- pandas can
    # produce these and Python's json module writes literal NaN which JS
    # cannot parse.
    output = sanitize_for_json(output)

    output_path = os.path.join(OUTPUT_DIR, 'dashboard_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved: {output_path}")
    sections = sum(1 for k, v in output.items()
                   if isinstance(v, (list, dict)) and v is not None
                   and k not in ('season_status',))
    print(f"Sections populated: {sections}")
    print("Transform complete.")


if __name__ == '__main__':
    main()
