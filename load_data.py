import os
import pandas as pd
from sqlalchemy import create_engine
import pymysql
from dotenv import load_dotenv

load_dotenv()

# MySQL configuration
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_user = os.getenv("MYSQL_USER", "root")
mysql_password = os.getenv("MYSQL_PASSWORD", "tranvanhuy2k5")  # from docker-compose
mysql_db = os.getenv("MYSQL_DB", "ecommerce_recommender_system")
mysql_conn = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"

# Create engine
engine = create_engine(mysql_conn)

# Read data from the three tables
tables = ["data_shirts", "data_women_clothes", "data_watches"]
dfs = []
for table in tables:
    try:
        df = pd.read_sql_table(table, engine)
        dfs.append(df)
        print(f"Loaded {len(df)} records from {table}")
    except Exception as e:
        print(f"Error loading {table}: {e}")

# Concatenate the data
if dfs:
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total records after concatenation: {len(df)}")
else:
    print("No data loaded from tables")
    exit()

# Drop the unnamed index column if it exists
if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

# Synthesize information: clean and process
# For example, handle missing values, etc.
# Since data_cleaning.py does the cleaning, here we can do basic cleaning

# Assume columns are similar
# Remove duplicates if any
df = df.drop_duplicates()

# Handle missing values (simple fill)
df = df.fillna("")

print(f"After cleaning: {len(df)} records")

# Synthesized info
synthesized_info = {
    "total_products": len(df),
    "categories": {
        "shirts": len(dfs[0]) if len(dfs) > 0 else 0,
        "women_clothes": len(dfs[1]) if len(dfs) > 1 else 0,
        "watches": len(dfs[2]) if len(dfs) > 2 else 0,
    },
    "columns": list(df.columns),
    "sample_products": df.head(5).to_dict("records"),
}

# Load into MySQL table
table_name = "data_cleaned"
df.to_sql(table_name, engine, if_exists="replace", index=False)

print(f"Data synthesized and loaded into {table_name} table successfully.")
print("Synthesized Information:")
import json

print(json.dumps(synthesized_info, indent=4, default=str))
