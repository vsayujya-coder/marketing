
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Marketing Intelligence Dashboard", layout="wide")

st.title("Marketing Intelligence Dashboard")

# --- Data loading ---
@st.cache_data
def load_csv(path):
    try:
        df = pd.read_csv(path, parse_dates=['date'], infer_datetime_format=True, low_memory=False)
    except Exception:
        df = pd.read_csv(path, low_memory=False)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

# Expect these CSV filenames in the same folder as app
fb_path = "Facebook.csv"
google_path = "Google.csv"
tiktok_path = "TikTok.csv"
business_path = "Business.csv"

# Load (if present)
dfs = {}
for p in [fb_path, google_path, tiktok_path, business_path]:
    try:
        dfs[p] = load_csv(p)
    except FileNotFoundError:
        dfs[p] = None

st.sidebar.header("Data status")
for k, v in dfs.items():
    if v is None:
        st.sidebar.write(f"- {k}: **NOT FOUND**")
    else:
        st.sidebar.write(f"- {k}: {v.shape[0]} rows, {v.shape[1]} cols")

# If business data missing, cannot show some KPIs
if dfs[business_path] is None:
    st.error("Business.csv not found. Please upload Business.csv into the app folder.")

# Combine marketing sources
marketing_frames = []
for p in [fb_path, google_path, tiktok_path]:
    df = dfs.get(p)
    if df is not None:
        # Standardize column names lowercase
        df = df.rename(columns=str.lower)
        # Ensure a date column exists
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        marketing_frames.append(df.assign(source=p.replace('.csv','')))
if marketing_frames:
    marketing = pd.concat(marketing_frames, ignore_index=True, sort=False)
else:
    marketing = pd.DataFrame()

business = dfs.get(business_path)
if business is not None:
    business = business.rename(columns=str.lower)
    if 'date' in business.columns:
        business['date'] = pd.to_datetime(business['date'], errors='coerce')

# Sidebar filters
st.sidebar.header("Filters")
if not marketing.empty and 'date' in marketing.columns:
    min_date = marketing['date'].min().date()
    max_date = marketing['date'].max().date()
elif business is not None and 'date' in business.columns:
    min_date = business['date'].min().date()
    max_date = business['date'].max().date()
else:
    today = pd.Timestamp.today().date()
    min_date = today
    max_date = today

date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
selected_sources = st.sidebar.multiselect("Platforms", options=marketing['source'].unique().tolist() if not marketing.empty else [], default=marketing['source'].unique().tolist() if not marketing.empty else [])
campaign_choice = st.sidebar.selectbox("Campaign (optional)", options=["All"] + (marketing['campaign'].dropna().unique().tolist() if 'campaign' in marketing.columns else []))

# Apply filters
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start, end = min_date, max_date
if not marketing.empty:
    m = marketing.copy()
    if 'date' in m.columns:
        m = m[(m['date'] >= start) & (m['date'] <= end)]
    if selected_sources:
        m = m[m['source'].isin(selected_sources)]
    if campaign_choice and campaign_choice != 'All' and 'campaign' in m.columns:
        m = m[m['campaign'] == campaign_choice]
else:
    m = pd.DataFrame()

if business is not None:
    b = business.copy()
    if 'date' in b.columns:
        b = b[(b['date'] >= start) & (b['date'] <= end)]
else:
    b = pd.DataFrame()

# KPI calculations
st.markdown("## Key metrics")
col1, col2, col3, col4 = st.columns(4)
# Basic marketing KPIs
total_spend = m['spend'].sum() if 'spend' in m.columns else np.nan
total_impr = m['impression'].sum() if 'impression' in m.columns else (m['impressions'].sum() if 'impressions' in m.columns else np.nan)
total_clicks = m['click'].sum() if 'click' in m.columns else (m['clicks'].sum() if 'clicks' in m.columns else np.nan)
attributed_revenue = m['attributed_revenue'].sum() if 'attributed_revenue' in m.columns else np.nan

total_orders = b['orders'].sum() if 'orders' in b.columns else np.nan
total_revenue = b['total_revenue'].sum() if 'total_revenue' in b.columns else (b['revenue'].sum() if 'revenue' in b.columns else np.nan)
total_profit = b['gross_profit'].sum() if 'gross_profit' in b.columns else (b['profit'].sum() if 'profit' in b.columns else np.nan)

roas = (attributed_revenue / total_spend) if total_spend and not np.isnan(total_spend) and total_spend>0 else np.nan
cac = (total_spend / total_orders) if total_orders and total_orders>0 else np.nan

col1.metric("Total Spend", f"${total_spend:,.0f}" if not np.isnan(total_spend) else "—")
col2.metric("Attributed Revenue", f"${attributed_revenue:,.0f}" if not np.isnan(attributed_revenue) else "—")
col3.metric("ROAS", f"{roas:.2f}" if not np.isnan(roas) else "—")
col4.metric("CAC", f"${cac:,.2f}" if not np.isnan(cac) else "—")

# Time series charts
st.markdown("## Time trends")
if not m.empty and 'date' in m.columns:
    daily_marketing = m.groupby('date').agg({col: 'sum' for col in ['spend'] if col in m.columns}).reset_index()
    if 'attributed_revenue' in m.columns:
        daily_marketing = daily_marketing.merge(m.groupby('date').agg({'attributed_revenue':'sum'}).reset_index(), on='date', how='left')
    fig = px.line(daily_marketing, x='date', y=[c for c in daily_marketing.columns if c!='date'], title='Marketing spend & attributed revenue over time')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('No marketing data available for time trends.')

if not b.empty and 'date' in b.columns:
    daily_business = b.groupby('date').agg({col:'sum' for col in ['orders','total_revenue','gross_profit'] if col in b.columns}).reset_index()
    fig2 = px.line(daily_business, x='date', y=[c for c in daily_business.columns if c!='date'], title='Business metrics over time')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info('No business data available for time trends.')

# Platform breakdown
st.markdown("## Platform breakdown")
if not m.empty and 'source' in m.columns:
    plat = m.groupby('source').agg({col:'sum' for col in ['spend','click','attributed_revenue'] if col in m.columns}).reset_index()
    st.dataframe(plat)
    fig3 = px.bar(plat, x='source', y='spend', title='Spend by platform')
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info('No platform-level data.')

# Campaign table
st.markdown("## Campaign-level detail")
if not m.empty:
    cols_to_show = [c for c in ['date','source','campaign','adset','impression','click','spend','attributed_revenue'] if c in m.columns]
    st.dataframe(m[cols_to_show].sort_values(by='date', ascending=False).reset_index(drop=True))
else:
    st.info('No campaign-level data to show.')

st.markdown("---")
st.caption("App generated by assistant — edit the file to match your CSV column names if needed.")
