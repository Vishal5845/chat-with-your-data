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
            "compare_monthly": re.compile(r"compare\s+monthly\s+(?:revenue|sales|income)?\s*([\w\s\.\-]+?)\s+(?:vs|v\.?|and)\s*([\w\s\.\-]+)",re.IGNORECASE),
            "compare_total": re.compile(r"compare(?!\s+monthly)\s+(?:total\s+)?(?:revenue|sales|income)?\s*([\w\s\.\-]+?)\s+(?:vs|v\.?|and)\s*([\w\s\.\-]+)",re.IGNORECASE),

        }

        # map common short names/aliases -> canonical country name as in your CSV
        self.country_map = {
            "uk": "United Kingdom",
            "u.k.": "United Kingdom",
            "gb": "United Kingdom",
            "great britain": "United Kingdom",
            "britain": "United Kingdom",
            "us": "USA",
            "u.s.": "USA",
            "u.s.a": "USA",
            "usa": "USA",
            "united states": "USA",
            "america": "USA",
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
        
        if not hasattr(self, '_csv_countries'):
            tx_file = os.path.join(self.summary_folder, "transactions.csv")
            if os.path.exists(tx_file):
                tx = pd.read_csv(tx_file, usecols=["Country"])
                self._csv_countries = [str(country).strip() for country in tx["Country"].dropna().unique()]
        else:
            pass
        
        for i in self._csv_countries:
            clean = re.sub(r"[^\w\s]", "", i).strip().lower()
            if clean == key or clean.startswith(key):
                return i.strip().title()
            
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
            m = pat.search(q)
            if m:
                print(f"Matched regex → {cat}")
                if cat in ("compare_total", "compare_monthly"):
                    return "compare", "regex", cat, m
                else:
                    return regex_to_meta.get(cat, cat), "regex", None, m
            
        # Fallback to Synonyms
        for cat, words in self.queries.items():
            for w in words:
                if w in q:
                    return cat, "synonym"
        
        return None, None, None, None
    
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
        country_match = re.search(r"(?:in|from|for)\s+([\w\s]+)", query, re.IGNORECASE)
        if country_match:
            raw = country_match.group(1).strip()
            country = self.normalize_country(raw)
            # print(country)
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
    
    def handle_revenue(self, query):
        country_match = re.search(r"(?:in|from|for)\s+([\w\s]+)", query, re.IGNORECASE)
        if country_match:
            country = self.normalize_country(country_match.group(1))
            print(country)
            countries_df = pd.read_csv(os.path.join(self.summary_folder, "countries_revenue.csv"))
            match = countries_df[countries_df["Country"].str.lower() == country.lower()]
            if not match.empty:
                revenue = match["Revenue"].sum()
                print(f"Revenue for {country}: {revenue:,.2f}")
                return True
            else:
                print(f"No revenue found for country: {country}")
                return True
        else:
        # fallback: total revenue
            total = summary["Total Revenue"]
            print(f"Total Revenue: {total:,.2f}")
            return True

    def handle_comparison(self, query, intent_match):
        """
    intent_match is the regex match object; detect_category returned ("compare", "regex", intent_name, match)
    Supports compare_total and compare_monthly.
    """
        intent_name = intent_match[2]
        m = intent_match[3]

        metric = "revenue"
        if not m or m.lastindex < 2:
            print("⚠️ Couldn't extract comparison countries properly.")
            return True
        # --- Extract country names depending on regex groups ---
        if m.lastindex >= 2:
            a_raw = m.group(1).strip()
            b_raw = m.group(2).strip()

        else:
            print("⚠️ Couldn't extract comparison countries properly.")
            return True

        a = self.normalize_country(a_raw)
        b = self.normalize_country(b_raw)


        tx_file = os.path.join(self.summary_folder, "transactions.csv")
        if not os.path.exists(tx_file):
            print("transactions.csv file missing")
            return True
        
        tx = pd.read_csv(tx_file)
        tx["Country_norm"] = tx["Country"].apply(lambda x: self.normalize_country(str(x)))

        a_norm = a.lower()
        b_norm = b.lower()
        tx["Country_norm"] = tx["Country_norm"].str.lower()
        print("a_norm:", a_norm)
        print("b_norm:", b_norm)
        
        if intent_name == "compare_total":
            sum_a = tx[tx["Country_norm"] == a_norm]["Revenue"].sum()
            sum_b = tx[tx["Country_norm"] == b_norm]["Revenue"].sum()
            df_cmp = pd.DataFrame({
                "Country" : [a,b],
                metric.capitalize(): [sum_a, sum_b]
            })
            print(f"Total {metric.title()} Comparison: {a} vs {b}")
            print("-"*40)
            print(df_cmp.to_string(index=False))

            # plot the bar chart
            fig, ax = plt.subplots(figsize=(6,4))
            df_cmp.plot(x="Country", y=metric.capitalize(), kind="bar", ax=ax, legend=False)
            ax.set_title(f"Total {metric.title()}: {a} vs {b}")
            ax.set_ylabel(metric.capitalize())
            # Save the plot
            out = f"reports/plots/compare_{a.replace(' ','_')}_vs_{b.replace(' ','_')}.png"
            plt.tight_layout()
            plt.savefig(out)
            plt.show()
            print(f"Plot save to {out}")
            return True

        elif intent_name == "compare_monthly":
            if 'YearMonth' not in tx.columns:
                print("Year month columns is missing in transacctions.csv")
                return True
            
            df_a = tx[tx["Country_norm"] == a_norm].groupby("YearMonth")["Revenue"].sum().reset_index()
            df_b = tx[tx["Country_norm"] == b_norm].groupby("YearMonth")["Revenue"].sum().reset_index()

            if df_a.empty and df_b.empty:
                print(f"No monthly data for {a} or {b}")
                return True
            
            # merge and prepare for plotting
            df_m = pd.merge(df_a, df_b, on=["YearMonth"], how="outer", suffixes=(f"_{a}", f"_{b}")).fillna(0)
            df_m_plot = df_m.set_index("YearMonth")
            df_m_plot.columns = [f"{metric.title()} {a}", f"{metric.title()} {b}"]

            #plot
            fig , ax = plt.subplots(figsize=(9,4))
            df_m_plot.plot(ax=ax, marker='o')
            ax.set_title(f"Monthly {metric.title()} Trend: {a} vs {b}")
            ax.set_ylabel(metric.title())
            plt.xticks(rotation=45)
            plt.tight_layout()

            out = f"reports/plots/compare_{a.replace(' ', '_')}_vs_{b.replace(' ', '_')}_monthly.png"
            plt.savefig(out)
            plt.show()
            print(f"Plot saved to {out}")
            return True
        else:
            print("⚠️ Unknown comparison intent.")
            return True

    def display(self, category, query=None):
        print(f"\n🔎 Query: {query}")
        meta = self.metadata[category]
        df = self.load_csv(category)
        
        # Determine top N 
        n = self.extract_top_n(query) if meta["top_n"] and query else None
        
        # Routes to handlers
        if category in ["customers"]:
            # Single value summary
            self.handle_single_value(meta, df, query)
        
        elif category == "revenue":
            if not self.handle_revenue(query):
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
    def handle_single_value(self, meta, df, query=None):
        """Show one metric (customers, revenue, etc.)"""
        if query and any(i in query.lower() for i in self.queries["revenue"]):
            match = re.search(r"(?:from|in)\s+([\w\s\.]+)", query, re.IGNORECASE)
            # print(match)
            if match:
                country = match.group(1).strip()
                country = re.sub(r"^the\s+", "", country, flags=re.IGNORECASE)
                country_norm = self.normalize_country(country)
                tx_file = os.path.join(self.summary_folder, "transactions.csv")
                if os.path.exists(tx_file):
                    tx = pd.read_csv(tx_file)
                    tx["Country_norm"] = tx["Country"].astype(str).str.strip().str.lower()
                    target = country_norm.lower()
                    subset = tx[tx["Country_norm"] == target]
                    if subset.empty:
                        print(f"⚠️ No revenue found for country: {country}")
                        return
                    total = subset["Revenue"].sum()
                    print(f"Total Revenue for {country}: {total:,.3f}")
                    return
        
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
            if query in ['exit', "quit"]:
                print("Exiting. Goodbye!")
                break

            start = time.time()
            try:
                intent_match = self.detect_category(query)
                if not intent_match:
                    self.fallback_response()
                    self.log_query(query, None, "fallback", matched_by=None, exec_time_ms =(time.time() - start) * 1000)
                    continue
                
                cat, matched_by = intent_match[0], intent_match[1]
                print(cat, matched_by)

                # Handle Comparison queries first
                if cat == "compare":
                    self.handle_comparison(query, intent_match)
                    self.log_query(query, cat, status="success", matched_by=matched_by, exec_time_ms = (time.time() - start) * 1000)
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

