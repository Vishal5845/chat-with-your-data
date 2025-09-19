import pandas as pd
import duckdb as ddb

# Connect to DuckDB
con = ddb.connect("ai_assistant.duckdb")

# Top 10 loyal customer
loyal = con.execute("""
                   select customerid, frequency, monetary
                   from rfm
                   where segment = 'Loyal'
                   order by monetary desc
                   limit 10
                   """).fetchdf()

print("Top 10 Loyal Customers:\n", loyal)
loyal.to_csv("reports/loyal_customers.csv", index=False)

# Top 10 lost customer
lost = con.execute("""
                   select customerid, recency, monetary
                   from rfm
                   where Segment = 'Lost'
                   order by monetary desc
                   limit 10
                   """).fetchdf()

print("Top 10 Lost Customers:\n", lost)
lost.to_csv("reports/lost_customers.csv", index=False)