-- H3: Deploying interceptors in the top 5 unaddressed rivers could reduce ocean plastic input by 25%
USE source_to_sea;

WITH UnaddressedRivers AS (
    SELECT 
        r.river_name,
        r.emission_tons_year
    FROM 
        rivers r
    WHERE 
        r.river_id NOT IN (
            SELECT DISTINCT source_url 
            FROM ocean_cleanup_efforts 
            WHERE source_url IS NOT NULL
        )
		AND r.river_name != 'Klang'  -- Exclude 'Klang' because it is number 4 on the list but has an interceptor)
),
RankedRivers AS (
    SELECT 
        river_name,
        emission_tons_year,
        (emission_tons_year / 1005984.0) * 100 as individual_pct
    FROM 
        UnaddressedRivers
    ORDER BY 
        emission_tons_year DESC
    LIMIT 5
),
FinalCalc AS (
    SELECT 
        river_name,
        emission_tons_year,
        individual_pct,
        SUM(individual_pct) OVER (ORDER BY emission_tons_year DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as accumulated_pct
    FROM 
        RankedRivers
)
SELECT 
    river_name,
    emission_tons_year,
    ROUND(individual_pct, 2) as pct_of_global,
    ROUND(accumulated_pct, 2) as accumulated_pct
FROM 
    FinalCalc;