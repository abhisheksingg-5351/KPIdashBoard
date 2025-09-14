# 📘 Marketing Intelligence Dashboard

## Overview
This Streamlit app provides a **Marketing Intelligence Dashboard** by combining campaign-level marketing data (Facebook, Google, TikTok) with business outcomes (orders, revenue, customers).

It includes:
- KPI cards (Spend, Revenue, Orders, Customers)
- Daily % change trend charts
- Daily spend & revenue totals
- Weekly spend, revenue, ROAS
- Platform share (%) of spend & revenue
- Time series analysis
- Campaign performance ranking
- Correlation analysis between marketing spend and orders
- Channel summary metrics
- Raw data explorers

---

## 📂 Files Required
Make sure these CSVs are in the **same folder** as the script:

- `Facebook.csv`
- `Google.csv`
- `TikTok.csv`
- `Business.csv`  
  *(your file may be named `business.csv`, but casing doesn’t matter — the script handles it)*

---

## ⚙️ Installation & Setup

### 1. Clone or download this project
Save the file `main.py` (your dashboard script) along with the CSV files into a folder.

### 2. Create a virtual environment
It’s best practice to use a virtual environment.
and install the requirements by 
```bash
python install -r requirements.txt
```

**Windows (PowerShell or CMD):**
```bash
python -m venv venv
venv\Scripts\activate
```
**Run the project using the streamlit run**
```bash
streamlit run main.py
```
