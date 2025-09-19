import pandas as pd

summary = pd.read_csv("data/processed/summary_statistics.csv")

q = input("Ask a question about your data: ").lower()

if any(word in q for word in ["customer", "customers", "buyers"]):
    print("Total Customers:", summary["TotalCustomers"][0])
elif any(word in q for word in ["revenue", "sales", "income"]):
    print("Total Revenue:", summary["Total_Revenue"][0])
else:
    print("Sorry, I can’t answer that yet.")

