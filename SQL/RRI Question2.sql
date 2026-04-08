-- Research Question 2: Where does plastic accumulate?
-- create marine_microplastic table


-- H1 The majority of floating plastic concentrates in 5 gyre systems, with the North Pacific being the largest
WITH real_zones AS (
    SELECT 
        lat,
        lng,
        concentration,
        CASE 
            WHEN lat BETWEEN 30 AND 65 AND (lng BETWEEN 140 AND 180 OR lng BETWEEN -180 AND -120) THEN 'North Pacific Gyre'
            WHEN lat BETWEEN -45 AND -15 AND lng BETWEEN -150 AND -70 THEN 'South Pacific Gyre'
            WHEN lat BETWEEN 30 AND 65 AND lng BETWEEN -70 AND -20 THEN 'North Atlantic Gyre'
            WHEN lat BETWEEN -45 AND -15 AND lng BETWEEN -50 AND 20 THEN 'South Atlantic Gyre'
            WHEN lat BETWEEN -45 AND -10 AND lng BETWEEN 40 AND 120 THEN 'Indian Ocean Gyre'
            ELSE 'Coastal / Other'
        END AS zone_name
    FROM observed_plastic
    WHERE concentration > 0
),
zone_stats AS (
    SELECT 
        zone_name,
        COUNT(*) AS sample_count,
        ROUND(AVG(concentration), 6) AS avg_concentration,
        ROUND(SUM(concentration), 4) AS total_load
    FROM real_zones
    GROUP BY zone_name
)
SELECT 
    zone_name,
    sample_count,
    avg_concentration,
    total_load,
    -- Calculate Percentage of Total Load
    ROUND((total_load / SUM(total_load) OVER ()) * 100, 2) AS pct_of_total_load,
    -- Calculate Percentage of Total Samples
    ROUND((sample_count / SUM(sample_count) OVER ()) * 100, 2) AS pct_of_samples,
    RANK() OVER (ORDER BY avg_concentration DESC) AS density_rank
FROM zone_stats
ORDER BY density_rank;

/*
Analysis of the Results
1. "Coastal / Other" is #1 (by a massive margin)
Avg Concentration: 66.53 (vs ~2.6 for the next highest).
Why? This confirms that plastic pollution is most dense near sources (river mouths, coastal cities, shipping lanes). 
The "Coastal / Other" bucket captures all these high-intensity source zones.
Portfolio Insight: This validates the need for upstream intervention (your Q4 hero question). 
Cleaning up coasts prevents plastic from ever reaching the gyres.

2. North Pacific Gyre is #2 (The "Garbage Patch" is Real)
Avg Concentration: 2.61.
Significance: Among the open ocean gyres, the North Pacific is the clear winner, 
with slightly higher average density than the South Atlantic (2.56) and significantly higher than the others.
Hypothesis H1 Validated: Your hypothesis that "Asian rivers dominate... and North Pacific is largest" is supported. 
The proximity of Asian river sources (from Q1) directly feeds this gyre.

3. South Atlantic is #3 (Surprising but Valid)
Avg Concentration: 2.56.
Why? It is very close to the North Pacific. This suggests significant accumulation, possibly from South American and African coastal sources.

4. The "Low" Gyres (Indian, North Atlantic, South Pacific)
These show much lower average concentrations (0.28 - 0.57).
Note on Sampling: Look at the sample_count. The North Atlantic has 1,309 samples (very well studied), yet the average is low. 
This means it genuinely has lower density in this dataset, not just less data. 
The South Pacific has very few samples (179), so its low average might be due to under-sampling remote areas.

Finding: 
Analysis of 15,534 real-world samples reveals that 99.3% of observed microplastic load is located in Coastal/Source Zones, not the open ocean gyres. 
While the North Pacific Gyre has the highest density among the gyres, its concentration is 25x lower than coastal averages.

Conclusion: H1 is rejected. Plastic has not yet fully migrated to the gyres; it remains trapped in coastal accumulation zones. 
This validates the strategy of intercepting plastic at river mouths (Q4) before it ever reaches the open ocean."
*/

-- H2: Coastal regions near high-input rivers show disproportionately high surface plastic density
-- H2 Final Proof: % of Coastal Plastic near Top 50 Rivers
WITH top_50_sources AS (
    -- Get coordinates of the top 50 emission points
    SELECT 
        emission_tons_year, 
        lat, 
        lon 
    FROM emission_points
    ORDER BY emission_tons_year DESC
    LIMIT 50
),
plastic_distances AS (
    SELECT 
        o.concentration,
        -- Calculate distance to the NEAREST of the Top 50 sources
        (SELECT MIN(ST_Distance_Sphere(POINT(o.lng, o.lat), POINT(s.lon, s.lat))) / 1000
         FROM top_50_sources s
        ) AS dist_to_nearest_top_river_km
    FROM observed_plastic o
    WHERE o.concentration > 0
      AND o.sampling_method LIKE '%net%'  -- 👈 ADD THIS LINE HERE
)
SELECT 
    COUNT(*) AS total_samples,
    SUM(CASE WHEN dist_to_nearest_top_river_km <= 50 THEN 1 ELSE 0 END) AS samples_near_top_rivers,
    ROUND(
        (SUM(CASE WHEN dist_to_nearest_top_river_km <= 50 THEN 1 ELSE 0 END) / COUNT(*)) * 100, 
        2
    ) AS percentage_near_top_rivers,
    ROUND(AVG(CASE WHEN dist_to_nearest_top_river_km <= 50 THEN concentration ELSE NULL END), 2) AS avg_density_near_rivers,
    ROUND(AVG(CASE WHEN dist_to_nearest_top_river_km > 50 THEN concentration ELSE NULL END), 2) AS avg_density_far_from_rivers
FROM plastic_distances;

/*
Verdict: CONFIRMED (with nuance)
"Disproportionately High Density": YES. The density near rivers (2.22) is 3 times higher than in the open ocean (0.74). 
This proves that river mouths are indeed hotspots for macro-plastic accumulation.
"Majority of Plastic": NO. Only 0.63% of the samples are found in these immediate zones.
Why? Macro-plastics float and drift. Once they leave the river mouth, currents sweep them away into the broader coastal zone or out to sea. 
They don't stay clustered at the source.
*/



