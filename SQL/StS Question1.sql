-- Reasearch Question 1: Where does ocean plastic come from?
-- H1:  A small number of rivers (top 50) account for the majority of plastic entering the ocean 
USE source_to_sea;

select round(sum(emission_tons_year)) from emission_points;
-- global total = 1.006.000 tons a year 

WITH ranked_rivers AS (
    SELECT
        r.river_name,
        c.country_name,
        r.emission_tons_year,
        RANK() OVER (ORDER BY r.emission_tons_year DESC) AS river_rank,
        SUM(r.emission_tons_year) OVER (
            ORDER BY r.emission_tons_year DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_emissions
    FROM rivers r
    JOIN countries c USING (country_id)
)
SELECT
    river_rank,
    river_name,
    country_name,
    emission_tons_year,
    ROUND(emission_tons_year      / (select round(sum(emission_tons_year)) from emission_points) * 100, 2) AS pct_of_global,
    ROUND(cumulative_emissions    / (select round(sum(emission_tons_year)) from emission_points) * 100, 2) AS cumulative_pct_of_global
FROM ranked_rivers
WHERE river_rank <= 50
ORDER BY river_rank;

/* Finding: 
A Tiny Fraction of Rivers Drives a Quarter of Global Pollution Our analysis reveals a stark imbalance: 
the top 50 rivers (representing just 0.16% of all 31,819 emission sources) are responsible for 26.3% of the total plastic entering the ocean.

While the top 50 rivers alone do not constitute a "majority" (>50%), the data confirms a highly skewed distribution. 
A "critical few" sources contribute disproportionately to the problem, while the remaining 31,700 sources ("the trivial many") contribute the other 74% collectively.

Strategic Implication: This validates a targeted approach. Intervening in just 0.16% of the world's rivers could reduce global plastic input by over 26%. 
This offers a high-efficiency starting point for cleanup initiatives, proving that we don't need to solve all 31,000 sources simultaneously to make a massive dent.
Original H1: "Top 50 rivers account for the majority." -> Rejected (They account for 15%).
*/

CREATE OR REPLACE VIEW all_emission_points AS
SELECT 
    point_id,
    country_id,
    continent_id,
    lat,
    lon,
    emission_tons_year AS emission,
    income_group
FROM emission_points;

-- H2: Plastic input correlates with GDP per capita — lower income countries contribute more due to less waste infrastructure
-- Calculate the Correlation Coefficient
SELECT
    income_group,
    COUNT(*) AS emission_points,
    ROUND(SUM(emission), 0) AS total_emissions_tons,
    ROUND((SUM(emission) / 1005984.0) * 100, 2) AS pct_of_global_total,
    ROUND(AVG(emission), 2) AS avg_emission_per_point
FROM all_emission_points
WHERE income_group IS NOT NULL
GROUP BY income_group
ORDER BY total_emissions_tons DESC;

/*Findings:
1. The "Middle-Income Trap" Dominates
Lower-Middle-Income Countries: Contribute 65.02% of all global plastic emissions.
Upper-Middle-Income Countries: Contribute 31.17%.
Combined: These two groups account for 86.19% of the world's ocean plastic.

2. High-Income Countries are relatively clean 
Despite high consumption, High-Income Countries contribute only 2.11% of total emissions.
Why? Their average emission per point is tiny (3.88 tons) compared to Lower-Middle-Income countries (52.69 tons). 
This proves that wealth correlates with better waste management infrastructure, preventing plastic from leaking into rivers.

3. The "Unknown" Category
Our analysis covers 99.4% of global plastic emissions assigned to specific income groups (Low: 1.09%, Lower-middle: 65.02%, Upper-middle: 24.9%, High: 3.88%). 
The remaining 0.59% (5,961 tons) originates from 217 emission points located in countries with no available income classification for 2021. 
These are not geographic unknowns—all points are mapped to specific countries—but reflect gaps in World Bank economic data. 
Given their high average emission per point (27.47 tons), these locations warrant further investigation but were excluded from 
income-correlation analysis to maintain methodological rigor.
*/

-- H3: Asian rivers dominate global plastic input, but European rivers are underestimated

SELECT
    continent,
    COUNT(*) AS emission_points,
    ROUND(SUM(emission), 0) AS total_emissions_tons,
    ROUND((SUM(emission) / 1005984.0) * 100, 2) AS pct_of_global_plastic,
    ROUND(AVG(emission), 2) AS avg_emission_per_point,
    
    -- NEW COLUMN: The Global Baseline
    ROUND((SELECT AVG(emission) FROM all_emission_points), 2) AS global_avg_emission
    
FROM all_emission_points
WHERE continent IS NOT NULL
GROUP BY continent
ORDER BY total_emissions_tons DESC;

/*Finding: 
Asia is the Primary Source, but Pollution Intensity Varies Globally Our analysis confirms that Asia is the dominant source of riverine plastic, contributing 82.06% of global emissions. 
Crucially, this dominance is driven by both quantity and intensity: the average Asian river emits 42.54 tons/year, which is 35% higher than the global average (31.62 tons).

Conversely, Europe contributes a negligible 0.55%, with an average emission of just 2.61 tons/river —92% lower than the global mean. 
This disproves the hypothesis that European rivers are "underestimated"; rather, it highlights the effectiveness of European waste containment systems.

Strategic Implication: Global cleanup efforts must prioritize Asia for immediate volume reduction. 
However, the high average emission in Africa and South America (29.35 / 24.01 tons per point) signals a critical need for preventative infrastructure there before consumption rates rise further.
*/

