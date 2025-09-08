import pandas as pd
import duckdb as ddb


#Connect to DuckDB
con = ddb.connect('ai_assistant.duckdb')

#1. How many rows?
print("\n 1. Total number of rows in the dataset:")
print(con.execute("Select count(*) from ecommerce").fetchall()) 

#2. Top 5 products by sales revenue
print("\n 2. Top 5 products by sales revenue:")
print(con.execute("""
                  select description, sum(unitprice * quantity) as total_revenue
                  from ecommerce
                  group by description
                  order by total_revenue desc
                  limit 5
                """).fetchdf())

#3. Revenue by country (top 5 countries)
print("\n 3. Top 5 countries by sales revenue:")
print(con.execute("""select country, round(sum(unitprice * quantity), 2) as total_revenue
                  from ecommerce
                  group by country
                  order by total_revenue desc
                  limit 5
                  """).fetchdf())