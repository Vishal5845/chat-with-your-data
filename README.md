# Chat With Your Data 🤖📊  

Have you ever looked at a messy sales Excel file and wished you could just *ask it a question* like:  
> "What were my top 5 products last month?"  

That’s exactly what this project does.  

I built an **AI-powered data pipeline** that turns raw sales data into clean tables, and then lets you **chat with your data in plain English**.  

---

## ✨ What it Does
- Load raw CSV sales data into a local database (DuckDB).  
- Clean and organize the data with **dbt** (think "data modeling for analytics").  
- Ask questions in natural language → AI converts them into SQL queries.  
- See answers instantly in a simple **Streamlit app** (tables + charts).  

---

## 🛠️ Tech Behind It
- **DuckDB** → lightweight, free database (like SQLite but built for analytics).  
- **dbt** → transformations + tests to make data reliable.  
- **LangChain + Hugging Face** → LLM agent that turns text → SQL.  
- **Streamlit** → clean, interactive chat UI.  

---

## 🚀 How to Try It
1. Clone this repo & install requirements:
   ```bash
   git clone https://github.com/your-username/chat-with-your-data.git
   cd chat-with-your-data
   pip install -r requirements.txt
2. Load the sample sales data
   ``` bash
   python load_and_query.py
3. Run the Streamlit app and start chatting with your data
   ``` bash
   streamlit run app.py


