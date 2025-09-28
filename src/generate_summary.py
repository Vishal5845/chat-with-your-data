import pandas as pd
import duckdb as ddb

con = ddb.connect("ai_assistant.duckdb")


# Load full data
df = con.execute("select * from ecommerce").fetchdf()
# print(df.columns)

# Add revenue column
df["Revenue"] = df["Quantity"] * df["UnitPrice"]

# Total customers and total revenue
summary = {
    "Total Customers" : df["CustomerID"].nunique(),
    "Total Revenue" : df["Revenue"].sum()
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv("data/processed/summary.csv", index=False)

# countries by revenue
country_revenue = df.groupby("Country")["Revenue"].sum().reset_index().sort_values(by="Revenue", ascending=False).reset_index(drop=True)

country_revenue.to_csv("data/processed/countries_revenue.csv", index=False)

# Revenue by Prduct(Description)
product_revenue = df.groupby("Description")["Revenue"].sum().reset_index().sort_values(by="Revenue", ascending=False).reset_index(drop=True)
product_revenue.to_csv("data/processed/products_revenue.csv", index=False)

# Monthly Revenue
# Convert InvoiceDate to datetime
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format = "%m/%d/%Y %H:%M")

# Extract year-month
df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

# group by year month and sum revenue
monthly_revenue = df.groupby("YearMonth")["Revenue"].sum().reset_index().sort_values(by="YearMonth")
monthly_revenue.to_csv("data/processed/monthly_revenue.csv", index=False)

# Transaction summary
transactions = df[["InvoiceNo", "InvoiceDate", "Country", "Description", "Revenue", "Quantity", "YearMonth"]].copy()
transactions.rename(columns= {"InvoiceNo" : "TransactionID", "InvoiceDate" : "Date"}, inplace=True)
transactions.to_csv("data/processed/transactions.csv", index=False)

print("✅ Summary files generated in data/processed/")
