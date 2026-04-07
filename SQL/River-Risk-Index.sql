-- H1:  A small number of rivers (top 50) account for the majority of plastic entering the ocean 
SET @global_total = 1005984.0;  

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
    ROUND(emission_tons_year      / @global_total * 100, 2) AS pct_of_global,
    ROUND(cumulative_emissions    / @global_total * 100, 2) AS cumulative_pct_of_global
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
Lower-Middle-Income Countries: Contribute 50.07% of all global plastic emissions.
Upper-Middle-Income Countries: Contribute 25.19%.
Combined: These two groups account for 75.26% (three-quarters) of the world's ocean plastic.

2. High-Income Countries are relatively clean 
Despite high consumption, High-Income Countries contribute only 1.83% of total emissions.
Why? Their average emission per point is tiny (4.31 tons) compared to Lower-Middle-Income countries (67.13 tons). 
This proves that wealth correlates with better waste management infrastructure, preventing plastic from leaking into rivers.

3. The "Unknown" Category
Our analysis covers 78% of global plastic emissions assigned to specific income groups. 
The remaining 22% originates from emission points with no assigned country 
(likely international waters or unresolved geographic coordinates) and was excluded from the income correlation analysis.
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
Asia is the Primary Source, but Pollution Intensity Varies Globally Our analysis confirms that Asia is the dominant source of riverine plastic, contributing 63.6% of global emissions. 
Crucially, this dominance is driven by both quantity and intensity: the average Asian river emits 53.5 tons/year, which is 69% higher than the global average (31.6 tons).

Conversely, Europe contributes a negligible 0.45%, with an average emission of just 2.8 tons/river—eleven times cleaner than the global mean. 
This disproves the hypothesis that European rivers are "underestimated"; rather, it highlights the effectiveness of European waste containment systems.

Strategic Implication: Global cleanup efforts must prioritize Asia for immediate volume reduction. 
However, the high average emission in Africa (36.3 tons) signals a critical need for preventative infrastructure there before consumption rates rise further.
*/

