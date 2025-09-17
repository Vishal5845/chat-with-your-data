import pandas as pd
import duckdb as ddb
import matplotlib.pyplot as plt
import seaborn as sns

con = ddb.connect("ai_assistant.duckdb")

# Get the latest date
rfm = con.execute("""
    with latest_date as (
                  SELECT MAX(strptime(InvoiceDate, '%m/%d/%Y %H:%M')) AS LatestDate
                  FROM ecommerce
                )

    SELECT
        CustomerID,
        COUNT(InvoiceNo) AS Frequency,
        SUM(Quantity * UnitPrice) AS Monetary,
        date_diff('day' ,MAX(strptime(InvoiceDate, '%m/%d/%Y %H:%M')), (select LatestDate from latest_date)) AS Recency
    FROM ecommerce
    WHERE CustomerID IS NOT NULL
    GROUP BY CustomerID
""").fetchdf()

print(rfm.head())

rfm["R_Quartile"] = pd.qcut(rfm["Recency"], 4, labels=[4, 3, 2, 1])
rfm["F_Quartile"] = pd.qcut(rfm["Frequency"], 4, labels=[1, 2, 3, 4])
rfm["M_Quartile"] = pd.qcut(rfm["Monetary"], 4, labels=[1, 2, 3, 4])

# RFM Score
rfm["RFM_Score"] = rfm["R_Quartile"].astype(str) + rfm["F_Quartile"].astype(str) + rfm["M_Quartile"].astype(str)

print(rfm[["CustomerID", "RFM_Score"]].head(10))


# RFM score distribution
plt.figure(figsize=(10, 6))
sns.countplot(data=rfm, x="RFM_Score", order=sorted(rfm["RFM_Score"].unique()))
plt.title("RFM Score Distribution")
plt.xlabel("RFM Score")
plt.ylabel("Number of Customers")
plt.xticks(rotation=90)
plt.savefig('reports/rfm_score_distribution.png')
# plt.show()

# Heatmap for avergae Monetary value by Recency and Frequency
rfm_pivot = rfm.pivot_table(index='R_Quartile', columns='F_Quartile', values='Monetary', aggfunc='mean')

plt.figure(figsize=(8, 6))
sns.heatmap(rfm_pivot, annot=True, fmt=".2f", cmap="YlGnBu")
plt.title("Average Monetary Value by Recency and Frequency Quartiles")
plt.xlabel("Frequency Quartile")
plt.ylabel("Recency Quartile")
plt.savefig('reports/rfm_heatmap.png')
# plt.show()

# Save to CSV
rfm.to_csv("reports/rfm_scores.csv", index=False)
print("RFM scores saved to reports/rfm_scores.csv")

def segment(row):
    if row["RFM_Score"] == "444":
        return "Champions"
    elif row["R_Quartile"] == 4 and row["F_Quartile"] >= 3:
        return "Loyal"
    elif row["R_Quartile"] == 1 and row["F_Quartile"] == 1:
        return "Lost"
    else:
        return "Others"
    

rfm["Segment"] = rfm.apply(segment, axis=1)
# print(rfm[["CustomerID", "RFM_Score", "Segment"]].head(10))

con.execute("drop table if exists rfm")
con.execute("Create table if not exists rfm as select * from rfm")
print("RFM table created in DuckDB")