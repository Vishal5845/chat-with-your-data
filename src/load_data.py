import pandas as pd
import duckdb as ddb

# Read the csv file into a pandas DataFrame
df = pd.read_csv('data/raw/data.csv', encoding='latin1')

# Connect to DuckDB (in-memory)
condb = ddb.connect("ai_assistant.duckdb")


# Create table
condb.execute("""
    CREATE TABLE IF NOT EXISTS ecommerce as select * from df
""")

# Verify the table creation
result = condb.execute("SELECT count(*) FROM ecommerce").fetchall()
print("Total rows in ecommerce table:", result[0][0])
print("Data loaded into DuckDB successfully.")