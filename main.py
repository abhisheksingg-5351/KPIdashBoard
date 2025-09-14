import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(layout="wide", page_title="Marketing Intelligence Dashboard", page_icon="📊")
st.title("Marketing Intelligence Dashboard 📈")
st.markdown("""
**Overview:** Loads campaign-level marketing data (Facebook, Google, TikTok) and business outcomes (orders, revenue).
Use the sidebar to filter date range, platform, state and campaign. The app calculates CTR, CPC and ROAS and shows business-focused analytics.
""")

# ---------- Helpers ----------
@st.cache_data
def try_read_csv_paths(possible_names, base_paths=("./", "/mnt/data/")):
    """Try to load each filename from a list of possible names returning dict of dataframes."""
    dfs = {}
    for key, names in possible_names.items():
        df = None
        for name in names:
            for p in base_paths:
                fp = p + name
                try:
                    df = pd.read_csv(fp)
                    # Stash the actual path used
                    df._source_path = fp  # not standard but helpful for debugging
                    break
                except Exception:
                    continue
            if df is not None:
                break
        if df is None:
            raise FileNotFoundError(f"Could not find any of {names} in {base_paths}")
        dfs[key] = df
    return dfs

def standardize_columns_lower(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def parse_dates_safely(df, date_cols=('date',)):
    df = df.copy()
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce').dt.date
    return df

def coerce_numeric(df, cols):
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        else:
            # create column of NaNs so later aggregations run smoothly
            df[c] = np.nan
    return df

def normalize_marketing(df, platform_name):
    df = standardize_columns_lower(df)
    # common marketing numeric columns we expect (handle variations gracefully)
    # try synonyms mapping if necessary
    # Keep the canonical names: date, tactic, state, campaign, impression, clicks, spend, attributed revenue
    # Attempt to rename common variants:
    rename_map = {}
    colnames = df.columns.tolist()

    # mapping heuristics
    for c in colnames:
        c_low = c.lower()
        if "impression" in c_low or "impr" == c_low:
            rename_map[c] = "impression"
        if c_low in ("click", "clicks"):
            rename_map[c] = "clicks"
        if "spend" in c_low or "cost" in c_low or "amount" in c_low:
            rename_map[c] = "spend"
        if "attributed" in c_low and "revenue" in c_low:
            rename_map[c] = "attributed revenue"
        if c_low == "revenue":
            # be careful: only rename revenue if there is no explicit 'attributed revenue'
            if "attributed revenue" not in colnames:
                rename_map[c] = "attributed revenue"
        if c_low in ("campaign", "campaign name", "ad_group", "adgroup"):
            rename_map[c] = "campaign"
        if c_low in ("tactic", "channel", "adset", "ad_set"):
            rename_map[c] = "tactic"
        if c_low in ("state", "region"):
            rename_map[c] = "state"
        if c_low in ("date", "day"):
            rename_map[c] = "date"

    if rename_map:
        df = df.rename(columns=rename_map)

    # Ensure expected numeric columns exist
    df = coerce_numeric(df, ["impression", "clicks", "spend", "attributed revenue"])
    df = parse_dates_safely(df, date_cols=("date",))
    df["platform"] = platform_name
    # keep original columns as well
    return df

# ---------- Load data ----------
# allow different filename casings; user uploaded files: business.csv, Facebook.csv, Google.csv, TikTok.csv
possible_names = {
    "facebook": ["Facebook.csv", "facebook.csv", "FB.csv", "fb.csv"],
    "google": ["Google.csv", "google.csv", "Google Ads.csv", "google_ads.csv"],
    "tiktok": ["TikTok.csv", "tiktok.csv"],
    "business": ["Business.csv", "business.csv", "business_data.csv"]
}

try:
    raw = try_read_csv_paths(possible_names)
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# show small preview of loaded files & detected path
with st.expander("Data sources (detected)"):
    for k, df in raw.items():
        try:
            source = getattr(df, "_source_path", "unknown")
        except Exception:
            source = "unknown"
        st.write(f"**{k}** — rows: {len(df):,}, columns: {df.shape[1]}, source: `{source}`")
        st.dataframe(df.head(4))

# ---------- Normalize datasets ----------
fb = normalize_marketing(raw["facebook"], "Facebook")
gg = normalize_marketing(raw["google"], "Google")
tt = normalize_marketing(raw["tiktok"], "TikTok")
marketing = pd.concat([fb, gg, tt], ignore_index=True, sort=False)

biz = standardize_columns_lower(raw["business"])
biz = parse_dates_safely(biz, date_cols=("date",))
# Try to ensure common business columns exist: orders, revenue, new customers
biz = coerce_numeric(biz, ["orders", "revenue", "new customers"])

# Derived marketing metrics
# Protect divisions by zero and NaN
marketing["ctr"] = marketing["clicks"] / marketing["impression"]
marketing["cpc"] = marketing["spend"] / marketing["clicks"]
marketing["roas"] = marketing["attributed revenue"] / marketing["spend"]

# Aggregate daily marketing per platform
agg_funcs = {"impression": "sum", "clicks": "sum", "spend": "sum", "attributed revenue": "sum"}
daily_marketing = (
    marketing.groupby(["date", "platform"], dropna=True, as_index=False)
    .agg(agg_funcs)
)
# recompute rates
daily_marketing["ctr"] = daily_marketing["clicks"] / daily_marketing["impression"]
daily_marketing["cpc"] = daily_marketing["spend"] / daily_marketing["clicks"]
daily_marketing["roas"] = daily_marketing["attributed revenue"] / daily_marketing["spend"]

# Total marketing across platforms per day
total_marketing_daily = (
    daily_marketing.groupby("date", as_index=False)
    .agg({"impression":"sum","clicks":"sum","spend":"sum","attributed revenue":"sum"})
)
if not total_marketing_daily.empty:
    total_marketing_daily["ctr"] = total_marketing_daily["clicks"] / total_marketing_daily["impression"]
    total_marketing_daily["roas"] = total_marketing_daily["attributed revenue"] / total_marketing_daily["spend"]

# Merge economics/business + aggregated marketing by date (left join — keep business days)
merged = pd.merge(biz, total_marketing_daily, on="date", how="left", suffixes=("","_mkt"))

# ---------- Sidebar Filters ----------
st.sidebar.header("Filters & Controls")

# date range defaults
all_dates = marketing["date"].dropna().sort_values()
if not all_dates.empty:
    default_start = all_dates.min()
    default_end = all_dates.max()
else:
    # fallback to business dates or today
    bdates = biz["date"].dropna().sort_values()
    default_start = bdates.min() if not bdates.empty else date.today()
    default_end = bdates.max() if not bdates.empty else date.today()

date_range = st.sidebar.date_input("Select date range", value=(default_start, default_end), min_value=None, max_value=None)

platforms = ["All"] + sorted(marketing["platform"].dropna().unique().tolist())
platform_select = st.sidebar.selectbox("Platform", platforms)

states = ["All"]
if "state" in marketing.columns:
    vals = marketing["state"].dropna().unique().tolist()
    states = ["All"] + sorted(vals)
state_select = st.sidebar.selectbox("State", states)

campaigns = ["All"]
if "campaign" in marketing.columns:
    vals = marketing["campaign"].dropna().unique().tolist()
    campaigns = ["All"] + sorted(vals)
campaign_select = st.sidebar.selectbox("Campaign", campaigns)

# ---------- Apply filters ----------
def apply_filters_marketing(df):
    df = df.copy()
    # date range
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        if start is not None and end is not None:
            df = df[(df["date"] >= start) & (df["date"] <= end)]
    # platform
    if platform_select != "All":
        df = df[df["platform"] == platform_select]
    # state
    if state_select != "All" and "state" in df.columns:
        df = df[df["state"] == state_select]
    # campaign
    if campaign_select != "All" and "campaign" in df.columns:
        df = df[df["campaign"] == campaign_select]
    return df

def apply_filters_df(df):
    # generic (works for merged / totals)
    df = df.copy()
    if "date" in df.columns and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        if start is not None and end is not None:
            df = df[(df["date"] >= start) & (df["date"] <= end)]
    if "platform" in df.columns and platform_select != "All":
        df = df[df["platform"] == platform_select]
    if "state" in df.columns and state_select != "All":
        df = df[df["state"] == state_select]
    if "campaign" in df.columns and campaign_select != "All":
        df = df[df["campaign"] == campaign_select]
    return df

filtered_marketing = apply_filters_marketing(marketing)
filtered_daily_marketing = apply_filters_df(daily_marketing)
filtered_total_marketing_daily = apply_filters_df(total_marketing_daily)
filtered_merged = apply_filters_df(merged)

# ---------- KPI Row ----------
k1, k2, k3, k4 = st.columns(4)
total_spend = filtered_marketing["spend"].sum(min_count=1)
total_attr_rev = filtered_marketing["attributed revenue"].sum(min_count=1)
total_orders = filtered_merged["orders"].sum(min_count=1) if "orders" in filtered_merged.columns else np.nan
new_customers = filtered_merged["new customers"].sum(min_count=1) if "new customers" in filtered_merged.columns else np.nan

k1.metric("Total Spend", f"${total_spend:,.0f}" if not np.isnan(total_spend) else "N/A")
k2.metric("Attributed Revenue (marketing)", f"${total_attr_rev:,.0f}" if not np.isnan(total_attr_rev) else "N/A")
k3.metric("Orders (business)", f"{int(total_orders):,}" if not np.isnan(total_orders) else "N/A")
k4.metric("New Customers", f"{int(new_customers):,}" if not np.isnan(new_customers) else "N/A")

st.markdown("---")

# ---------- Time Series: Spend vs Attributed Revenue ----------
st.subheader("Time Series — Marketing Spend vs Attributed Revenue")
time_df = filtered_marketing.groupby("date", as_index=False).agg({"spend":"sum","attributed revenue":"sum"})
if time_df.empty:
    st.info("No marketing time-series data for the selected filters.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time_df["date"], y=time_df["spend"], name="Marketing Spend", mode="lines+markers", yaxis="y1"))
    fig.add_trace(go.Scatter(x=time_df["date"], y=time_df["attributed revenue"], name="Attributed Revenue", mode="lines+markers", yaxis="y2"))
    fig.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="Spend ($)", side="left"),
        yaxis2=dict(title="Attributed Revenue ($)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Spend by Platform (stacked area) ----------
st.subheader("Daily Spend by Platform (stacked)")
spend_by_platform = filtered_marketing.groupby(["date", "platform"], as_index=False).agg({"spend":"sum"})
if spend_by_platform.empty:
    st.info("No spend data available for the selected filters.")
else:
    fig2 = px.area(spend_by_platform, x="date", y="spend", color="platform", title="Daily Spend by Platform")
    st.plotly_chart(fig2, use_container_width=True)

# ---------- Top campaigns by attributed revenue ----------
st.subheader("Top Campaigns by Attributed Revenue")
if "campaign" not in filtered_marketing.columns:
    st.info("No campaign column found in marketing data.")
else:
    camp = filtered_marketing.groupby(["platform", "campaign"], as_index=False).agg({"spend":"sum","attributed revenue":"sum","clicks":"sum"})
    camp["roas"] = camp["attributed revenue"] / camp["spend"]
    top_camp = camp.sort_values("attributed revenue", ascending=False).head(20)
    if top_camp.empty:
        st.info("No campaign-level revenue data for the selected filters.")
    else:
        fig3 = px.bar(top_camp, x="campaign", y="attributed revenue", color="platform",
                      hover_data=["spend", "clicks", "roas"], title="Top Campaigns by Attributed Revenue (Top 20)")
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)

# ---------- Correlation: Spend vs Orders ----------
st.subheader("Correlation: Marketing Spend vs Business Orders (daily)")
if "orders" in filtered_merged.columns:
    corr_df = filtered_merged[["date", "spend", "orders"]].dropna()
    if corr_df.empty:
        st.info("Need both spend and orders in the selected date range to show correlation.")
    else:
        scatter = px.scatter(corr_df, x="spend", y="orders", trendline="ols", title="Daily Spend vs Orders (with linear fit)")
        st.plotly_chart(scatter, use_container_width=True)
else:
    st.info("Business data does not contain an 'orders' column — correlation not available.")

# ---------- Channel performance summary ----------
st.subheader("Channel Performance Summary")
channel_summary = filtered_marketing.groupby("platform", as_index=False).agg({
    "impression":"sum","clicks":"sum","spend":"sum","attributed revenue":"sum"
})
if channel_summary.empty:
    st.info("No channel data to summarize.")
else:
    channel_summary["ctr"] = channel_summary["clicks"] / channel_summary["impression"]
    channel_summary["cpc"] = channel_summary["spend"] / channel_summary["clicks"]
    channel_summary["roas"] = channel_summary["attributed revenue"] / channel_summary["spend"]
    # Format for readability
    st.dataframe(
        channel_summary.round({
            "impression":0, "clicks":0, "spend":2, "attributed revenue":2, "ctr":4, "cpc":2, "roas":2
        }).assign(
            impression=lambda d: d["impression"].map(lambda x: f"{int(x):,}" if not pd.isna(x) else "0"),
            clicks=lambda d: d["clicks"].map(lambda x: f"{int(x):,}" if not pd.isna(x) else "0"),
            spend=lambda d: d["spend"].map(lambda x: f"${x:,.2f}" if not pd.isna(x) else "$0.00"),
            **{}
        ),
        height=300
    )

# ---------- Raw / Diagnostic Data ----------
with st.expander("Show raw marketing data (filtered)"):
    st.write(f"Rows: {len(filtered_marketing):,}")
    st.dataframe(filtered_marketing.sort_values("date", ascending=False).reset_index(drop=True).head(500))

with st.expander("Show raw business/merged data (filtered)"):
    st.write(f"Rows: {len(filtered_merged):,}")
    st.dataframe(filtered_merged.sort_values("date", ascending=False).reset_index(drop=True).head(500))

# ---------- Notes and next steps ----------
st.markdown("---")
st.markdown("""
**Notes & next steps**
- If you want to attribute business orders to campaigns / UTMs, provide order-level data with campaign/utm fields or pass orders with campaign column in `Business.csv`.
- Suggested additions: cohort LTV analysis (requires customer-level data), CAC over time, retention curves, statistical uplift experiments.
- If a column you expect is missing, rename that column in the CSV or tell me the column name and I can adapt the mapping logic.
""")
