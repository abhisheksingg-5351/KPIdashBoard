# Marketing Intelligence Dashboard

## Overview

This Streamlit app provides a **Marketing Intelligence Dashboard** by combining campaign-level marketing data (Facebook, Google, TikTok) with business outcomes (orders, revenue, customers).

It includes:

* KPI cards (Spend, Revenue, Orders, Customers)
* Daily % change trend charts
* Daily spend & revenue totals
* Weekly spend, revenue, ROAS
* Platform share (%) of spend & revenue
* Time series analysis
* Campaign performance ranking
* Correlation analysis between marketing spend and orders
* Channel summary metrics
* Raw data explorers

---

## Files required

Place the following CSV files in the **same folder** as `main.py`:

* `Facebook.csv`
* `Google.csv`
* `TikTok.csv`
* `Business.csv` (the script will accept `business.csv` or different casing)

---

## Installation & Setup

These steps will get the app running locally on your machine.

### 1. Create a virtual environment (recommended)

**Windows (PowerShell / CMD)**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

Make sure `requirements.txt` sits alongside `main.py`. Then run:

```bash
pip install -r requirements.txt
```

### 3. Run the app locally

From the project folder (where `main.py` is located) run:

```bash
streamlit run main.py
```

Streamlit will open the dashboard in your browser at `http://localhost:8501` by default.

---

## Example `requirements.txt`

(Adjust versions if your environment requires it.)

```
streamlit>=1.20.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.0.0
matplotlib>=3.6.0
scikit-learn>=1.2.0
seaborn>=0.12.0
```

---

## Deployment tips & troubleshooting

* **ModuleNotFoundError**: If you see `ModuleNotFoundError: No module named 'plotly'` (or any other module), activate your virtual environment and re-run `pip install -r requirements.txt`.
* **Port conflicts**: If port 8501 is already in use, run `streamlit run main.py --server.port 8502` (or any free port).
* **Large CSVs**: If files are large, consider sampling locally while developing and using full datasets in a deployed environment.

---

## Useful commands

* Install dependencies: `pip install -r requirements.txt`
* Run the app: `streamlit run main.py`
* Run on a different port: `streamlit run main.py --server.port 8502`

---

## Hosted app

Live demo: [https://kpidashboardlifesight.streamlit.app/](https://kpidashboardlifesight.streamlit.app/)

---

If you'd like, I can also:

* Generate a ready-to-save `requirements.txt` file for you,
* Create a short `Procfile` / Dockerfile for deploying to Streamlit Cloud or other hosts,
* Or add a short README section describing how the CSV columns should be formatted.

Tell me which of the above you want next.

