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

#4. Total number of orders
print("\n 4. Total number of unique orders:")
print(con.execute("""select count(distinct invoiceno) from ecommerce""").fetchone()[0])

#5. Number of unique customers
print("\n 5. Total number of unique customers:")
print(con.execute(""" select count(distinct customerid) from ecommerce""").fetchone()[0])

#6. Top 5 products
print("\n 6. Top 5 products by quantity sold:")
print(con.execute("""
                  select description, sum(quantity) as total_quantity
                  from ecommerce
                  group by description
                  order by total_quantity desc
                  limit 5
                  """).fetch_df())

#7. Monthly sales trend
print("\n 7. Monthly sales trend (total revenue per month):")
print(con.execute("""
                  select strftime(strptime(invoicedate, '%m/%d/%Y %H:%M'), '%Y-%m') as Month, sum(quantity * unitprice) as total_revenue
                  from ecommerce
                  group by Month
                  order by total_revenue
                  """).fetch_df())


# Missing values per column
df = (con.execute("""
                  select *
                 from ecommerce""").fetchdf())


print("/n Missing values per column:")
print(df.isnull().sum())

# Duplicate rows
print("\n Number of duplicate rows:")
print(df.duplicated().sum())
print(con.execute(""" select count(*) from 
      (select *, count(*) as cnt 
      from ecommerce
      group by all
      having count(*) >1
      )"""
    ).fetchone()[0])

# Negtive entries
print("\n Number of rows with negative quantity or unit price:")
print(con.execute("""
                  select count(*) as Negative_Entries
                  from ecommerce
                  where quantity < 0 or unitprice < 0
                  """).fetch_df())


#Top 10 customers by revenue
print("\n Top 10 customers by revenue:")
print(con.execute("""
                  select customerid, round(sum( quantity * UnitPrice), 2) as total_revenue
                  from ecommerce
                  group by customerid
                  order by total_revenue desc
                  limit 10
                  """).fetch_df())


# Average order value per customer (AOV)
print("\n Average order value per customer (AOV):")
print(con.execute("""
                  select customerid, avg(order_value) as AOV
                  from (
                  select customerid, invoiceno, round(sum(quantity * UnitPrice), 2) as order_value
                  from ecommerce
                  group by customerid, invoiceno
                  )
                  group by customerid
                  order by AOV desc
                  limit 10
                  """).fetch_df())

