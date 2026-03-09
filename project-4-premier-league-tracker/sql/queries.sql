-- ============================================================
-- Premier League Performance Tracker - SQL Queries
-- ============================================================

-- 1. FULL LEAGUE TABLE
SELECT 
    team, played, won, drawn, lost, 
    goals_for, goals_against, goal_difference,
    ROUND(xg_for, 1) as xg_for, ROUND(xg_against, 1) as xg_against,
    points
FROM league_table
ORDER BY points DESC, goal_difference DESC;

-- 2. TOP SCORERS BY MATCH (highest scoring games)
SELECT 
    date, home_team, away_team,
    home_goals || ' - ' || away_goals AS score,
    home_goals + away_goals AS total_goals,
    ROUND(home_xg, 2) AS home_xg,
    ROUND(away_xg, 2) AS away_xg,
    referee
FROM matches
ORDER BY total_goals DESC
LIMIT 15;

-- 3. HOME ADVANTAGE ANALYSIS
SELECT 
    home_team AS team,
    COUNT(*) AS home_matches,
    SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) AS home_wins,
    ROUND(CAST(SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) AS home_win_pct,
    SUM(home_goals) AS home_goals_scored,
    ROUND(AVG(home_possession), 1) AS avg_possession,
    ROUND(AVG(attendance), 0) AS avg_attendance
FROM matches
GROUP BY home_team
ORDER BY home_win_pct DESC;

-- 4. xG EFFICIENCY: WHO CONVERTS CHANCES BEST?
SELECT 
    team,
    goals_for,
    ROUND(xg_for, 1) AS xg_for,
    goals_for - ROUND(xg_for) AS goals_vs_xg,
    ROUND(CAST(goals_for AS FLOAT) / xg_for, 2) AS conversion_ratio
FROM league_table
ORDER BY conversion_ratio DESC;

-- 5. REFEREE IMPACT ON RESULTS
SELECT 
    referee,
    COUNT(*) AS matches_officiated,
    ROUND(AVG(home_goals + away_goals), 2) AS avg_goals_per_match,
    ROUND(AVG(home_fouls + away_fouls), 1) AS avg_fouls,
    ROUND(CAST(SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) AS home_win_pct,
    ROUND(CAST(SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) AS draw_pct
FROM matches
GROUP BY referee
ORDER BY matches_officiated DESC;

-- 6. FORM TABLE (LAST 10 GAMEWEEKS)
WITH recent AS (
    SELECT * FROM matches WHERE gameweek > 28
)
SELECT 
    team,
    SUM(pts) AS points_last10,
    SUM(gf) AS goals_for,
    SUM(ga) AS goals_against
FROM (
    SELECT home_team AS team, 
           CASE WHEN result='H' THEN 3 WHEN result='D' THEN 1 ELSE 0 END AS pts,
           home_goals AS gf, away_goals AS ga
    FROM recent
    UNION ALL
    SELECT away_team AS team,
           CASE WHEN result='A' THEN 3 WHEN result='D' THEN 1 ELSE 0 END AS pts,
           away_goals AS gf, home_goals AS ga
    FROM recent
)
GROUP BY team
ORDER BY points_last10 DESC;
