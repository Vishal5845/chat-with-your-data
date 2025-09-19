import duckdb as ddb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

con = ddb.connect("ai_assistant.duckdb")

# Monthly Sales Trend
df_sales = con.execute("""
    SELECT strftime(strptime(InvoiceDate, '%m/%d/%Y %H:%M'), '%Y-%m') AS Year_Month,
                       sum(quantity * unitprice) AS TotalSales
                       from ecommerce
                       group by Year_Month
                       order by Year_Month""").fetchdf()


# print(len(df_sales))
plt.figure(figsize=(10,5))
plt.plot(df_sales['Year_Month'], df_sales['TotalSales'], marker='o')
plt.title('Monthly Sales Trend')
plt.xlabel("Year Month")
plt.ylabel("Total Sales")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("reports/monthly_sales_trend.png")
plt.close()

# Top 10 Products by Revenue
df_prod = con.execute("""
    SELECT Description, sum(quantity * unitprice) AS TotalRevenue
    from ecommerce
    group by Description
    order by TotalRevenue DESC
    limit 10
""").fetchdf()

plt.figure(figsize=(10,5))
plt.barh(df_prod['Description'], df_prod['TotalRevenue'])
plt.title('Top 10 Products by Revenue')
plt.xlabel("Total Revenue")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("reports/top_products_by_revenue.png")
plt.close()

# Summary Statistics
summary = con.execute("""
    SELECT count(distinct CustomerId) AS TotalCustomers,
           count(distinct stockcode) AS TotalProducts,
           sum(quantity * unitprice) AS Total_Revenue
    from ecommerce
""").fetchdf()

summary.to_csv("data/processed/summary_statistics.csv", index=False)