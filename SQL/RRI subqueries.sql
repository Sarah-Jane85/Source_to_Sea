-- =============================================================================
-- Advanced SQL Challenge 1: Top 3 Polluted Countries per Continent
-- =============================================================================
-- Objective: 
--   Identify the top 3 countries with the highest riverine plastic emissions 
--   within each continent, demonstrating partitioned ranking logic.
--
-- Techniques Demonstrated:
--   1. CTE (Common Table Expression) to prepare aggregated data.
--   2. JOINs across 3 tables (emission_points, countries, continents).
--   3. Aggregation (SUM) to calculate total national emissions.
--   4. Window Function (RANK OVER PARTITION BY) to reset ranking per continent.
--   5. Outer Query Filtering to isolate the Top 3.
-- =============================================================================

SELECT 
    continent_name,
    country_name,
    total_emission,
    emission_rank
FROM (
    -- SUBQUERY: Calculate stats and assign ranks
    SELECT 
        cont.continent_name,
        coun.country_name,
        ROUND(SUM(e.emission_tons_year), 2) AS total_emission,
        RANK() OVER (PARTITION BY cont.continent_name ORDER BY SUM(e.emission_tons_year) DESC) AS emission_rank
    FROM emission_points e
    JOIN countries coun ON e.country_id = coun.country_id
    JOIN continents cont ON coun.continent_id = cont.continent_id
    GROUP BY cont.continent_name, coun.country_name
) AS ranked_countries
WHERE emission_rank <= 3
ORDER BY continent_name, emission_rank;

-- =============================================================================
-- Advanced SQL Challenge 2: Key Nations River Emission Ranking
-- =============================================================================
-- Objective: 
--   Determine the Global and Continental standing of specific key nations 
--   based on their total riverine plastic emission.
--
-- Techniques Demonstrated:
--   1. CTE (Common Table Expression) for modular logic.
--   2. JOINs across 3 tables (emission_points, countries, continents).
--   3. Aggregation (SUM) to calculate national totals.
--   4. Window Functions (RANK OVER) for Global and Partitioned (Continental) ranking.
--   5. Filtering (WHERE) to focus on specific countries of interest.
-- =============================================================================
WITH global_rankings AS (
    -- Calculate Global Rank for EVERY country
    SELECT 
        c.country_name,
        cont.continent_name,
        SUM(e.emission_tons_year) AS total_emission,
        RANK() OVER (ORDER BY SUM(e.emission_tons_year) DESC) AS global_rank,
        RANK() OVER (PARTITION BY cont.continent_name ORDER BY SUM(e.emission_tons_year) DESC) AS continent_rank
    FROM emission_points e
    JOIN countries c ON e.country_id = c.country_id
    JOIN continents cont ON c.continent_id = cont.continent_id
    GROUP BY c.country_name, cont.continent_name
)
-- Filter ONLY for the 6 countries of interest
SELECT 
    country_name,
    continent_name,
    ROUND(total_emission, 2) AS total_emission_tons,
    global_rank,
    continent_rank
FROM global_rankings
WHERE country_name IN ('Brazil', 'Spain', 'Portugal', 'Germany', 'Netherlands', 'United States')
ORDER BY global_rank;

SELECT COUNT(DISTINCT country_id) AS distinct_country_count
FROM emission_points;

-- 129 countries in total


-- Advanced SQL Challenge 3: Global Plastic Production Trend Analysis
-- Uses: CTE, LAG() Window Function, AVG() Window Function with Frame Clause, NULLIF()

-- =============================================================================
-- Advanced SQL Challenge 3: Macro-Plastic Trend Analysis (Nets Only)
-- =============================================================================
-- Objective: Analyze the historical trend of macro-plastic concentration
-- using only Net sampling data to ensure methodological consistency.
-- Techniques: CTE, Window Functions (LAG, AVG OVER), Filtering
-- =============================================================================

WITH yearly_net_stats AS (
    -- Step 1: Aggregate stats per year, filtering for Nets ONLY
    SELECT 
        year,
        ROUND(AVG(concentration), 6) AS avg_concentration,
        COUNT(*) AS sample_count
    FROM observed_plastic
    WHERE concentration > 0
      AND sampling_method LIKE '%net%'  -- 👈 Critical Filter for Consistency
    GROUP BY year
)

SELECT 
    year,
    sample_count,
    avg_concentration,
    
    -- Step 2: Get the previous year's average using LAG()
    LAG(avg_concentration, 1) OVER (ORDER BY year) AS prev_year_avg,
    
    -- Step 3: Calculate Year-Over-Year (YoY) Growth Percentage
    -- Formula: ((Current - Previous) / Previous) * 100
    -- NULLIF prevents division by zero errors
    ROUND(
        (avg_concentration - LAG(avg_concentration, 1) OVER (ORDER BY year)) / 
        NULLIF(LAG(avg_concentration, 1) OVER (ORDER BY year), 0) * 100, 
        2
    ) AS yoy_growth_pct,
    
    -- Step 4: Calculate 5-Year Moving Average
    -- "ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING" creates a 5-year window
    ROUND(
        AVG(avg_concentration) OVER (
            ORDER BY year 
            ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
        ), 
        6
    ) AS moving_avg_5yr

FROM yearly_net_stats
ORDER BY year;

/*a Note neets to be nade here to be aware of the sample counts per year.
The sample counts per year very and the coordinates of the sample counts vary
*/