import pandas as pd
import re
import matplotlib.pyplot as plt
import os
from datetime import *
import csv, time

# Load all summaries

summary = pd.read_csv("data/processed/summary.csv").to_dict(orient="records")[0]
countries = pd.read_csv("data/processed/countries_revenue.csv")
products = pd.read_csv("data/processed/products_revenue.csv")


class QAPrototype:
    def __init__ (self, summary_folder = "data/processed"):
        self.summary_folder = summary_folder
        os.makedirs("reports/plots", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        self.log_file = "logs/qa_log.csv"

        # Synonyms for query types
        self.queries = {
            "customers": ["customer", "customers", "users", "buyers"],
            "countries": ["country", "countries", "nation", "region"],
            "products": ["product", "products", "item", "sku"],
            "monthly_revenue": ["monthly revenue", "sales trend", "trend", "revenue by month", "monthly"],
            "transactions": ["transaction", "transactions", "orders", "purchases"],
            "revenue": ["revenue", "sales", "income"]
        }

        # Metadata defines CSV, columns, and behavior for each category
        self.metadata = {
            "customers" :{
                "file": "summary.csv",
                "name_col": None,
                "value_col": "Total Customers",
                "top_n": False,
                "plot": False
            },
            "revenue" :{
                "file": "summary.csv",
                "name_col": None,
                "value_col": "Total Revenue",
                "top_n": False,
                "plot": False
            },
            "countries" :{
                "file": "countries_revenue.csv",
                "name_col": "Country",
                "value_col": "Revenue",
                "top_n": True,
                "plot": True,
                "chart_type": "bar"
            },
            "products" :{
                "file": "products_revenue.csv",
                "name_col": "Description",
                "value_col": "Revenue",
                "top_n": True,
                "plot": True,
                "chart_type": "bar"
            },
            "monthly_revenue" :{
                "file": "monthly_revenue.csv",
                "name_col": "YearMonth",
                "value_col": "Revenue",
                "top_n": False,
                "plot": True,
                "chart_type" : "line"
            },
            "transactions" :{
                "file": "transactions.csv",
                "name_col": "InvoiceNo",
                "value_col": "Revenue",
                "top_n": False,
                "plot": False
            }
        }

        # Regex patterns (precompiled)
        self.regex_intents = {
            "monthly_revenue": re.compile(r"\b(revenue|sales|income).*(month|monthly|trend)\b", re.IGNORECASE),
            "countries_top": re.compile(r"\btop\s*\d*\s*(countries|regions|nations)\b", re.IGNORECASE),
            "products_in_country": re.compile(r"\btop\s*\d*\s*(products|items|skus).*(?:in|from)\s+([\w\s\.]+)", re.IGNORECASE),
            "transactions": re.compile(r"\btransactions?.*(?:in|from)\s+([\w\s\.]+)", re.IGNORECASE),
        }

        # map common short names/aliases -> canonical country name as in your CSV
        self.country_map = {
            "uk": "United Kingdom",
            "u.k.": "United Kingdom",
            "gb": "United Kingdom",
            "great britain": "United Kingdom",
            "us": "United States",
            "usa": "United States",
            "eire": "EIRE",          
            "ireland": "EIRE",
        }

        self.category_priority = {
            "monthly_revenue": 5,
            "countries": 4,
            "products": 3,
            "transactions": 2,
            "customers": 1,
            "revenue": 0
        }

    def normalize_country(self, raw_country:str) -> str:
        """
        Normalize a country string from user input to the canonical form
        used in your CSVs. Uses self.country_map; falls back to title-case.
        """
        if not raw_country:
            return raw_country
        
        key = re.sub(r"[^\w\s]", "", raw_country).strip().lower()
        key = re.sub(r"\s+", " ", key)
        # print(key)
        if key in self.country_map:
            return self.country_map[key]
        
        
        tx_file = os.path.join(self.summary_folder, "transactions.csv")
        if os.path.exists(tx_file):
            tx = pd.read_csv(tx_file)
            uni = [str(i).strip().lower() for i in tx["Country"].unique()]
            # print(uni)
            # try exact startswith
            for i in uni:
                if i.startswith(key):
                    print(i)
                    return i.title()
        return raw_country.strip().title()
        
    def detect_category(self, query: str):
        """Detect category using synonyms."""
        q = query.lower()

        regex_to_meta = {
            "monthly_revenue" : "monthly_revenue",
            "countries_top" : "countries",
            "products_in_country" : "products",
            "transactions": "transactions"
        }

        # Regex matching
        for cat, pat in self.regex_intents.items():
            if pat.search(q):
                print(f"🔎 Matched regex → {cat}")
                return regex_to_meta[cat], "regex"
            
        # Fallback to Synonyms
        matches = []
        for cat, words in self.queries.items():
            for w in words:
                if w in q:
                    return cat, "synonym"
        
        return None, None
    
    def extract_top_n(self, query:str, default=5):
        """Extract Top N from query, default=5."""
        match = re.search(r"\btop\s*(\d+)", query.lower())
        return int(match.group(1)) if match else default
    
    def load_csv(self, category):
        """ Load CSV file into DataFrame """
        meta = self.metadata[category]
        file_path = os.path.join(self.summary_folder, meta["file"])
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        return pd.read_csv(file_path)
    
    def plot_chart(self, df, x_col, y_col, category, chart_type=None, top_n=False):
        plt.figure(figsize=(8,5))
        ax = plt.gca()
        if chart_type is None:
            print(f"⚠️ No chart type specified for {category}, skipping plot.")
            return
        
        if chart_type == "line":
            df[x_col] = pd.to_datetime(df[x_col], format="%Y-%m", errors="coerce")
            df.plot(x_col, y_col, kind= "line", marker="o", ax=ax)
        elif chart_type == "bar":
            df.plot(x_col, y_col, kind="bar", ax=ax)
        else:
            print(f"⚠️ Unknown chart type: {chart_type}")
            return
        
        if top_n:
            plt.title(f"Top {len(df)} {x_col}")
        else:
            plt.title(f"{category.replace('_',' ').title()} Trend")
            
        plt.ylabel(y_col)
        plt.xlabel(x_col)
        plt.tight_layout()
        save_path = f"reports/plots/{category}.png"
        plt.savefig(save_path)
        plt.show()
        print(f"✅ Plot saved to {save_path}")

    def handle_products_in_country(self, query, n):
        country_match = re.search(r"(?:in|from) ([\w\s]+)", query, re.IGNORECASE)
        if country_match:
            raw = country_match.group(1).strip()
            country = self.normalize_country(raw)
            tx_file = os.path.join(self.summary_folder, "transactions.csv")
            if os.path.exists(tx_file):
                tx = pd.read_csv(tx_file)
                tx_country_norm = tx["Country"].astype(str).str.strip().str.lower()
                target_norm = country.lower()
                tx_filter = tx[tx_country_norm == target_norm]
                if tx_filter.empty:
                    print(f"⚠️ No transactions found for country: {country}")
                    return True
                df_country = (
                    tx_filter
                    .groupby("Description")["Revenue"].sum().nlargest(n).reset_index()
                )
                self.plot_chart(df_country, "Description", "Revenue", f"products_in_{country}", "bar")
                print(f"\nTop {n} Products in {country}")
                print("-"*40)
                print(df_country.to_string(index=False))
                return True
        return False
    
    def handle_transactions_in_country(self, query, n=None):
        country_match = re.search(r"(?:in|from) ([\w\s]+)", query, re.IGNORECASE)
        if country_match:
            raw = country_match.group(1).strip()
            country = self.normalize_country(raw)
            tx_file = os.path.join(self.summary_folder, "transactions.csv")
            if os.path.exists(tx_file):
                tx = pd.read_csv(tx_file)
                tx_country_norm = tx["Country"].astype(str).str.strip().str.lower()
                target_norm = country.lower()
                tx_filter = tx[tx_country_norm == target_norm]
                if tx_filter.empty:
                    print(f"⚠️ No transactions found for country: {country}")
                    return True
                if n:
                    tx_filter = tx_filter.nlargest(n, "Revenue")
                print(f"\nTransactions in {country}")
                print("-"*40)
                print(tx_filter.head(10).to_string(index=False))
                print(f"\nTotal Transactions: {len(tx_filter)}")
                print(f"Total Revenue: {tx_filter['Revenue'].sum():,.2f}")
                out_file = f"reports/transactions/transactions_{country.replace(' ', '_')}.csv"
                tx_filter.to_csv(out_file, index=False)
                print(f"Filtered data saved to {out_file}")
                return True
        return False
    
    def display(self, category, query=None):
        print(f"\n🔎 Query: {query}")
        meta = self.metadata[category]
        df = self.load_csv(category)
        
        # Determine top N 
        n = self.extract_top_n(query) if meta["top_n"] and query else None
        
        # Routes to handlers
        if category in ["customers", "revenue"]:
            # Single value summary
            self.handle_single_value(meta, df)

        elif category in ["countries", "products"]:
            # top N list
            if category == "products" and self.handle_products_in_country(query, n):
                return
            self.handle_topn(category, meta, df, query, n)

        elif category == "monthly_revenue":
            # trend/ timeseries
            self.handle_trend(category, meta, df)
        elif category == "transactions":
            if not self.handle_transactions_in_country(query, n):
                self.handle_topn(category, meta, df, query, n)
        else:
            # fallback
            self.fallback_response()
    
    # Handlers
    def handle_single_value(self, meta, df):
        """Show one metric (customers, revenue, etc.)"""
        val = df.iloc[0][meta["value_col"]]
        print(f"{meta['value_col']}: {val:,}")
    
    def handle_topn(self, category, meta, df, query, n):
        """Show top-N results (products, countries, etc.)"""
        if n:
            df = df.sort_values(meta["value_col"], ascending=False).head(n)
        
        print(f"\nTop {len(df)} {meta['name_col']}")
        print("-"*40)
        print(df.to_string(index=False))

        if meta.get("plot", False):
            self.plot_chart(df,
                            meta["name_col"],
                            meta["value_col"],
                            category,
                            meta["chart_type"],
                            top_n=True)
    
    def handle_trend(self, category, meta, df):
        """Show trend chart (monthly revenue, etc.)"""
        print("\n Monthly Revenue Trend")
        print("-"*40)
        print(df.to_string(index=False))

        if meta.get("plot", False):
            self.plot_chart(df,
                            meta["name_col"],
                            meta["value_col"],
                            category,
                            meta["chart_type"],
                            top_n=False)
    
    def fallback_response(self):
        print("Sorry, I don’t know how to answer that yet.")
        print("Try asking about customers, revenue, countries, products, transactions, or monthly trends.")
    
    def log_query(self, query:str, category: str = None, status:str = "success", rows:int=None, plot:bool=False, matched_by:str=None, exec_time_ms:float=None):
        """Log user queries in csv with extra context."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = self.log_file.replace(".txt", ".csv")

        file_exists = os.path.exists(log_path)
        with open(log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "query", "category", "status","rows", "plot", "matched_by","exec_time_ms"])
            writer.writerow([ts, query, category, status, rows if rows is not None else "", "yes" if plot else "no", matched_by if matched_by else "", f"{exec_time_ms: .2f}" if exec_time_ms else ""])

    def run_interactive(self):
        print("Welcome to QA Prototype! Type 'exit' to quit.")
        while True:
            query = input("\nEnter your query: ").strip().lower()
            if query == 'exit':
                print("Exiting. Goodbye!")
                break

            start = time.time()
            try:
                cat, matched_by = self.detect_category(query)
                print(cat, matched_by)
                if not cat:
                    self.fallback_response()
                    self.log_query(query, None, "fallback", matched_by=matched_by, exec_time_ms = (time.time() - start) * 1000)
                    continue

                # Display + count rows
                df = self.load_csv(cat)
                rows = len(df)
                meta = self.metadata[cat]
                # print(meta)
                self.display(cat, query)
                self.log_query(query, cat, status="success", rows=rows, plot=meta.get("plot", False), matched_by=matched_by, exec_time_ms = (time.time() - start) * 1000)

            except Exception as e:
                print(f"⚠️ Error: {e}")
                self.log_query(query, category=cat if 'cat' in locals() else None,
                               status=str(e),
                               exec_time_ms=(time.time() - start) * 1000)

if __name__ == "__main__":
    qa = QAPrototype(summary_folder="data/processed")
    qa.run_interactive()

