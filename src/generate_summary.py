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

print("✅ Summary files generated in data/processed/")
