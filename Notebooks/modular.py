import pandas as pd
import sqlalchemy
import logging
import yaml
import os
from typing import Optional

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles database connections and query execution."""
    
    def __init__(self, config_path: str = "../config.yaml"):
        self.config_path = config_path
        self.engine = None
        self._connect()

    def _connect(self):
        """Initializes the database engine using credentials from config or env."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # You can store password in config or use environment variable for security
            # Here we assume you might have it in env or config. 
            # For this demo, we'll ask for it if not in env, but in production use env vars.
            password = os.getenv("DB_PASSWORD")
            if not password:
                # Fallback for local dev if not set in env (you can remove this prompt in production)
                import getpass
                password = getpass.getpass("Enter MySQL Password: ")
            
            user = config.get("db_user", "root")
            host = config.get("db_host", "localhost")
            db_name = config.get("db_name", "river_risk_index")
            
            connection_string = f"mysql+pymysql://{user}:{password}@{host}/{db_name}"
            self.engine = sqlalchemy.create_engine(connection_string)
            logger.info("Database connection established successfully.")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def query_to_df(self, query: str) -> pd.DataFrame:
        """Executes a SQL query and returns a Pandas DataFrame."""
        try:
            logger.info(f"Executing query: {query[:50]}...")
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def upload_df(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace'):
        """Uploads a DataFrame to SQL."""
        try:
            logger.info(f"Uploading {len(df)} rows to table '{table_name}'...")
            df.to_sql(table_name, con=self.engine, if_exists=if_exists, index=False)
            logger.info("Upload successful.")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

# =============================================================================
# Analysis Functions (Modular Logic)
# =============================================================================

def get_top_countries_per_continent(db: DatabaseManager, limit: int = 3) -> pd.DataFrame:
    """
    Advanced SQL Challenge 1: Top N Polluted Countries per Continent.
    """
    query = f"""
    WITH ranked_countries AS (
        SELECT 
            cont.continent_name,
            coun.country_name,
            ROUND(SUM(e.emission_tons_year), 2) AS total_emission_tons,
            RANK() OVER (
                PARTITION BY cont.continent_name 
                ORDER BY SUM(e.emission_tons_year) DESC
            ) AS continent_rank
        FROM emission_points e
        JOIN countries coun ON e.country_id = coun.country_id
        JOIN continents cont ON coun.continent_id = cont.continent_id
        GROUP BY cont.continent_name, coun.country_name
    )
    SELECT continent_name, country_name, total_emission_tons, continent_rank
    FROM ranked_countries
    WHERE continent_rank <= {limit}
    ORDER BY continent_name ASC, continent_rank ASC;
    """
    return db.query_to_df(query)

def get_key_nations_ranking(db: DatabaseManager, countries: list) -> pd.DataFrame:
    """
    Advanced SQL Challenge 2: Global & Continental Rank for Specific Nations.
    """
    country_list_str = ', '.join(f"'{c}'" for c in countries)
    
    query = f"""
    WITH global_rankings AS (
        SELECT 
            c.country_name,
            cont.continent_name,
            SUM(e.emission_tons_year) AS total_emission,
            RANK() OVER (ORDER BY SUM(e.emission_tons_year) DESC) AS global_rank,
            RANK() OVER (
                PARTITION BY cont.continent_name 
                ORDER BY SUM(e.emission_tons_year) DESC
            ) AS continent_rank
        FROM emission_points e
        JOIN countries c ON e.country_id = c.country_id
        JOIN continents cont ON c.continent_id = cont.continent_id
        GROUP BY c.country_name, cont.continent_name
    )
    SELECT country_name, continent_name, 
           ROUND(total_emission, 2) AS total_emission_tons,
           global_rank, continent_rank
    FROM global_rankings
    WHERE country_name IN ({country_list_str})
    ORDER BY global_rank ASC;
    """
    return db.query_to_df(query)

def get_macro_plastic_trend(db: DatabaseManager) -> pd.DataFrame:
    """
    Advanced SQL Challenge 3: Macro-Plastic Trend Analysis (Nets Only).
    Uses Window Functions for YoY growth and Moving Averages.
    """
    query = """
    WITH yearly_net_stats AS (
        SELECT 
            year,
            ROUND(AVG(concentration), 6) AS avg_concentration,
            COUNT(*) AS sample_count
        FROM observed_plastic
        WHERE concentration > 0
          AND sampling_method LIKE '%net%'
        GROUP BY year
    )
    SELECT 
        year,
        sample_count,
        avg_concentration,
        LAG(avg_concentration, 1) OVER (ORDER BY year) AS prev_year_avg,
        ROUND(
            (avg_concentration - LAG(avg_concentration, 1) OVER (ORDER BY year)) / 
            NULLIF(LAG(avg_concentration, 1) OVER (ORDER BY year), 0) * 100, 
            2
        ) AS yoy_growth_pct,
        ROUND(
            AVG(avg_concentration) OVER (
                ORDER BY year 
                ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
            ), 
            6
        ) AS moving_avg_5yr
    FROM yearly_net_stats
    ORDER BY year;
    """
    return db.query_to_df(query)

def prepare_master_observation_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Data Cleaning: Prepares the raw parquet dataframe for SQL upload.
    - Extracts year
    - Renames columns
    - Filters invalid rows
    """
    logger.info("Preparing master observation table...")
    
    # Extract Year
    df_raw['sample_date'] = pd.to_datetime(df_raw['sample_date'], errors='coerce')
    df_raw['year'] = df_raw['sample_date'].dt.year
    
    # Rename measurement column to match SQL schema
    if 'microplastics_measurement' in df_raw.columns:
        df_raw = df_raw.rename(columns={'microplastics_measurement': 'concentration'})
    
    # Ensure types
    df_raw['concentration'] = pd.to_numeric(df_raw['concentration'], errors='coerce')
    df_raw['sampling_method'] = df_raw['sampling_method'].astype(str)
    
    # Drop nulls
    clean_df = df_raw.dropna(subset=['year', 'lat', 'lng', 'concentration', 'sampling_method'])
    
    # Select final columns
    final_df = clean_df[['year', 'lat', 'lng', 'concentration', 'sampling_method']]
    
    logger.info(f"Prepared {len(final_df)} clean rows.")
    return final_df