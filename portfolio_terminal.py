import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# COLOR PALETTE
# ─────────────────────────────────────────────
BG_PRIMARY   = "#0C0C0C"
BG_SECONDARY = "#111111"
BG_HEADER    = "#1A1A1A"
BORDER       = "#2A2A2A"
TEXT_PRIMARY = "#E8E8E8"
TEXT_MUTED   = "#666666"
TEXT_HEADER  = "#FFFFFF"
ACCENT_BLUE  = "#0077CC"
POSITIVE     = "#00C176"
NEGATIVE     = "#E8001C"
AMBER        = "#FF8C00"

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
EXCEL_PATH = r"C:\Users\powel\OneDrive\Documents\Portfolio_BUILT_v2.xlsx"

st.set_page_config(
    page_title="Portfolio Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap');

* { box-sizing: border-box; }

[data-testid="stAppViewContainer"] {
    background-color: #0C0C0C;
    color: #E8E8E8;
    font-family: 'IBM Plex Sans', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 1px solid #2A2A2A;
}
[data-testid="stSidebar"] * {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
}
[data-testid="block-container"] { padding-top: 1rem; }
.stRadio > label {
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #666666;
}
.stRadio [data-testid="stMarkdownContainer"] p { font-size: 12px; }

[data-testid="metric-container"] {
    background-color: #111111;
    border: 1px solid #2A2A2A;
    border-radius: 0px;
    padding: 10px 14px;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #E8E8E8 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #666666 !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
}
.dataframe {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    border: 1px solid #2A2A2A !important;
}
thead tr th {
    background-color: #1A1A1A !important;
    color: #FFFFFF !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid #2A2A2A !important;
}
tbody tr:nth-child(even) { background-color: #111111 !important; }
tbody tr:nth-child(odd)  { background-color: #0C0C0C !important; }
tbody tr:hover           { background-color: #1A1A1A !important; }

.stButton > button {
    background-color: #111111;
    color: #E8E8E8;
    border: 1px solid #2A2A2A;
    border-radius: 0px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 6px 16px;
}
.stButton > button:hover {
    background-color: #1A1A1A;
    border-color: #0077CC;
    color: #FFFFFF;
}
hr { border-color: #2A2A2A; }

.bbg-section {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #666666;
    border-bottom: 1px solid #2A2A2A;
    padding-bottom: 6px;
    margin-bottom: 16px;
    margin-top: 24px;
}
.bbg-header {
    background-color: #1A1A1A;
    border-bottom: 1px solid #0077CC;
    padding: 8px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #E8E8E8;
    letter-spacing: 1px;
    margin-bottom: 16px;
}
.bbg-status {
    display: flex;
    gap: 24px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    background: #1A1A1A;
    border-bottom: 1px solid #2A2A2A;
    padding: 6px 12px;
    color: #666666;
}
.bbg-status span { color: #E8E8E8; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────────
CHART_THEME = dict(
    paper_bgcolor=BG_PRIMARY,
    plot_bgcolor=BG_PRIMARY,
    font=dict(family='IBM Plex Mono', color=TEXT_PRIMARY, size=10),
    xaxis=dict(
        gridcolor=BG_HEADER,
        linecolor=BORDER,
        tickfont=dict(family='IBM Plex Mono', size=10),
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=BG_HEADER,
        linecolor=BORDER,
        tickfont=dict(family='IBM Plex Mono', size=10),
        showgrid=True,
        zeroline=False,
    ),
    legend=dict(
        bgcolor=BG_SECONDARY,
        bordercolor=BORDER,
        borderwidth=1,
        font=dict(family='IBM Plex Mono', size=10),
    ),
    margin=dict(l=50, r=20, t=36, b=40),
    title_font=dict(family='IBM Plex Sans', size=11, color=TEXT_MUTED),
)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data(path):
    market   = pd.read_excel(path, sheet_name='Market_Data',  index_col=0, parse_dates=True)
    units    = pd.read_excel(path, sheet_name='Daily_Units',  index_col=0, parse_dates=True)
    cash     = pd.read_excel(path, sheet_name='Daily_Cash',   index_col=0, parse_dates=True)
    ref      = pd.read_excel(path, sheet_name='Reference_Data')
    trades   = pd.read_excel(path, sheet_name='Trade_Log',    parse_dates=['Date', 'Settlement'])
    corr_raw = pd.read_excel(path, sheet_name='Correlation',  header=1, index_col=0)
    risk_raw = pd.read_excel(path, sheet_name='Risk_Metrics', header=3)

    # Align date indices across all three daily sheets
    common_dates = market.index.intersection(units.index).intersection(cash.index)
    market = market.loc[common_dates]
    units  = units.loc[common_dates]
    cash   = cash.loc[common_dates]

    # Closed positions have NaN units — treat as 0
    units = units.fillna(0)

    # Invested value: sum(shares × price) per day, active tickers only
    shared   = market.columns.intersection(units.columns)
    invested = (units[shared] * market[shared]).sum(axis=1)
    cash_s   = cash.iloc[:, 0]
    nav      = cash_s + invested

    # ── TIME-WEIGHTED RETURN (TWR) ──────────────────────────────────────────
    # External cash flows = daily cash change minus cash impact from trades
    # Trades: BUY = negative Amount (cash out), SELL = positive Amount (cash in)
    trades_net  = trades.groupby('Date')['Amount'].sum().reindex(cash_s.index, fill_value=0)
    cash_change = cash_s.diff().fillna(0)
    external_cf = (cash_change - trades_net).fillna(0)

    # Sub-period return for each day, adjusting denominator for external flows
    sub_returns = pd.Series(0.0, index=nav.index)
    for i in range(1, len(nav)):
        denom = nav.iloc[i - 1] + external_cf.iloc[i]
        sub_returns.iloc[i] = (nav.iloc[i] / denom - 1) if denom > 0 else 0.0

    twr_cumulative = (1 + sub_returns).cumprod() - 1

    # Drawdown from rolling NAV peak
    rolling_max = nav.cummax()
    drawdown    = (nav - rolling_max) / rolling_max

    equity_curve = pd.DataFrame({
        'NAV':          nav,
        'Cash':         cash_s,
        'Invested':     invested,
        'Daily_Return': sub_returns,      # TWR daily sub-period returns
        'Cumul_Return': twr_cumulative,   # TWR cumulative
        'Drawdown':     drawdown,
    })

    # ── CORRELATION MATRIX ─────────────────────────────────────────────────
    # header=1 loads tickers as column names; drop the 'TICKER / TICKER' index row
    corr = corr_raw.copy()
    corr = corr[~corr.index.astype(str).str.contains('TICKER', na=True)]
    corr = corr.drop(columns=[c for c in corr.columns if 'TICKER' in str(c)], errors='ignore')
    corr.index = corr.index.astype(str).str.strip()
    corr.columns = corr.columns.astype(str).str.strip()
    corr = corr.apply(pd.to_numeric, errors='coerce')

    # ── RISK METRICS ───────────────────────────────────────────────────────
    risk = risk_raw.dropna(subset=[risk_raw.columns[0]])
    risk = risk[risk.iloc[:, 0].astype(str).str.strip() != 'METRIC']

    return equity_curve, ref, trades, corr, risk, market, units


# ─────────────────────────────────────────────
# LOAD WITH ERROR HANDLING
# ─────────────────────────────────────────────
try:
    equity_curve, ref, trades, corr, risk, market, units = load_data(EXCEL_PATH)
except FileNotFoundError:
    st.error(f"File not found: {EXCEL_PATH}")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ─────────────────────────────────────────────
# DERIVED GLOBALS
# ─────────────────────────────────────────────
active        = ref[ref['Cur_Shares'] > 0].copy()
current_nav   = equity_curve['NAV'].iloc[-1]
total_return  = equity_curve['Cumul_Return'].iloc[-1]
max_drawdown  = equity_curve['Drawdown'].min()
daily_ret     = equity_curve['Daily_Return'].dropna()
ann_vol       = daily_ret.std() * (252 ** 0.5)
ann_ret_val   = (1 + daily_ret.mean()) ** 252 - 1
sharpe        = (ann_ret_val - 0.045) / ann_vol if ann_vol > 0 else 0
today_return  = equity_curve['Daily_Return'].iloc[-1]
start_date    = equity_curve.index[0]
end_date      = equity_curve.index[-1]

active_tickers = active['Ticker'].tolist()
corr_filtered  = corr.loc[
    [t for t in active_tickers if t in corr.index],
    [t for t in active_tickers if t in corr.columns],
]

# Terminal stdout validation
print(f"[OK] Loaded {len(equity_curve)} trading days")
print(f"[OK] {len(active)} active positions: {active['Ticker'].tolist()}")
print(f"[OK] Correlation matrix: {corr_filtered.shape}")
print(f"[OK] NAV: ${current_nav:,.2f}")
print(f"[OK] TWR Total Return: {total_return:.2%}")
print(f"[OK] Sharpe: {sharpe:.2f} | MaxDD: {max_drawdown:.2%}")

# ─────────────────────────────────────────────
# BENCHMARKS
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_benchmarks(start, end):
    data = {}
    for t in ['VOO', 'QQQ']:
        try:
            df = yf.download(t, start=start, end=end, auto_adjust=True, progress=False)
            if not df.empty:
                data[t] = df['Close'].squeeze()
        except Exception:
            pass
    return pd.DataFrame(data) if data else pd.DataFrame()

benchmarks = fetch_benchmarks(start_date, end_date)

# ─────────────────────────────────────────────
# SHARED PAGE HEADER
# ─────────────────────────────────────────────
def page_header():
    ret_color = POSITIVE if total_return >= 0 else NEGATIVE
    day_color = POSITIVE if today_return >= 0 else NEGATIVE
    st.markdown(f"""
    <div class="bbg-header">
    PORTFOLIO TERMINAL &nbsp;|&nbsp;
    <span style="color:{TEXT_MUTED}">AS OF</span> {end_date.strftime('%Y-%m-%d')} &nbsp;|&nbsp;
    <span style="color:{TEXT_MUTED}">NAV</span> <span style="color:{POSITIVE}">${current_nav:,.2f}</span> &nbsp;|&nbsp;
    <span style="color:{TEXT_MUTED}">TWR RETURN</span> <span style="color:{ret_color}">{total_return:+.2%}</span> &nbsp;|&nbsp;
    <span style="color:{TEXT_MUTED}">TODAY</span> <span style="color:{day_color}">{today_return:+.2%}</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;
                color:{TEXT_HEADER};letter-spacing:2px;padding-bottom:8px">
    PORTFOLIO TERMINAL
    </div>
    <div style="font-size:10px;color:{TEXT_MUTED};font-family:'IBM Plex Mono',monospace;
                border-bottom:1px solid {BORDER};padding-bottom:8px">
    Account: Z37353029<br>{end_date.strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;color:{TEXT_MUTED};letter-spacing:2px;'
                f'text-transform:uppercase;padding:12px 0 6px 0;font-family:IBM Plex Sans,sans-serif">'
                f'NAVIGATION</div>', unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "Dashboard",
        "Positions",
        "Correlation",
        "Risk Metrics",
        "Benchmarks",
        "Trade Log",
    ], label_visibility="collapsed")

    st.divider()

    nav_color = POSITIVE if current_nav > 0 else TEXT_PRIMARY
    day_color = POSITIVE if today_return >= 0 else NEGATIVE
    ret_color = POSITIVE if total_return >= 0 else NEGATIVE
    dd_color  = NEGATIVE if max_drawdown < 0 else TEXT_PRIMARY

    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;line-height:2">
    <div style="display:flex;justify-content:space-between">
        <span style="color:{TEXT_MUTED}">NAV</span>
        <span style="color:{TEXT_PRIMARY}">${current_nav:,.2f}</span>
    </div>
    <div style="display:flex;justify-content:space-between">
        <span style="color:{TEXT_MUTED}">Today</span>
        <span style="color:{day_color}">{today_return:+.2%}</span>
    </div>
    <div style="display:flex;justify-content:space-between">
        <span style="color:{TEXT_MUTED}">Return</span>
        <span style="color:{ret_color}">{total_return:+.2%}</span>
    </div>
    <div style="display:flex;justify-content:space-between">
        <span style="color:{TEXT_MUTED}">Max DD</span>
        <span style="color:{dd_color}">{max_drawdown:.2%}</span>
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div style="font-size:10px;color:{TEXT_MUTED};font-family:'IBM Plex Mono',monospace;
                margin-top:8px;line-height:1.8">
    Source: Portfolio_BUILT_v2.xlsx<br>
    Last: {end_date.strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE 1 — DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    page_header()
    st.markdown('<div class="bbg-section">KEY METRICS</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Portfolio NAV",   f"${current_nav:,.2f}")
    c2.metric("TWR Return",      f"{total_return:+.2%}", delta=f"{today_return:+.2%}")
    c3.metric("Today P&L",       f"${today_return * current_nav:,.2f}", delta=f"{today_return:+.2%}")
    c4.metric("Sharpe Ratio",    f"{sharpe:.2f}")
    c5.metric("Max Drawdown",    f"{max_drawdown:.2%}")
    c6.metric("Ann. Volatility", f"{ann_vol:.2%}")

    st.markdown('<div class="bbg-section">EQUITY CURVE</div>', unsafe_allow_html=True)

    fig_nav = go.Figure()
    fig_nav.add_trace(go.Scatter(
        x=equity_curve.index,
        y=equity_curve['NAV'],
        name='NAV',
        line=dict(color=ACCENT_BLUE, width=1.5),
        mode='lines',
    ))
    fig_nav.update_layout(
        **CHART_THEME,
        title=f"Portfolio NAV  —  {start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')}",
        yaxis_title="NAV ($)",
        height=300,
    )
    st.plotly_chart(fig_nav, use_container_width=True)

    col_left, col_right = st.columns([6, 4], gap="medium")

    with col_left:
        st.markdown('<div class="bbg-section">DRAWDOWN</div>', unsafe_allow_html=True)
        dd = equity_curve['Drawdown']
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Bar(
            x=dd.index,
            y=dd * 100,
            name='Drawdown',
            marker_color=NEGATIVE,
        ))
        fig_dd.update_layout(
            **CHART_THEME,
            title="Drawdown from Peak (%)",
            yaxis_title="Drawdown (%)",
            height=260,
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with col_right:
        st.markdown('<div class="bbg-section">ALLOCATION</div>', unsafe_allow_html=True)
        last_prices = market.iloc[-1]
        alloc_rows  = []
        for _, row in active.iterrows():
            px_val = last_prices.get(row['Ticker'], 0)
            val    = row['Cur_Shares'] * px_val
            alloc_rows.append({'Ticker': row['Ticker'], 'Value': val,
                                'Weight': val / current_nav if current_nav > 0 else 0})
        alloc_df = pd.DataFrame(alloc_rows).sort_values('Value')

        if not alloc_df.empty:
            fig_alloc = go.Figure(go.Bar(
                x=alloc_df['Value'],
                y=alloc_df['Ticker'],
                orientation='h',
                marker_color=ACCENT_BLUE,
                text=[f"{w:.1%}" for w in alloc_df['Weight']],
                textposition='outside',
                textfont=dict(family='IBM Plex Mono', size=9, color=TEXT_MUTED),
            ))
            fig_alloc.update_layout(
                **CHART_THEME,
                title="Current Allocation by Market Value",
                xaxis_title="Market Value ($)",
                yaxis_title="",
                height=260,
            )
            st.plotly_chart(fig_alloc, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 2 — POSITIONS
# ─────────────────────────────────────────────
def page_positions():
    page_header()
    st.markdown(f'<div class="bbg-section">ACTIVE POSITIONS  —  {len(active)} HOLDINGS</div>',
                unsafe_allow_html=True)

    last_prices = market.iloc[-1]
    prev_prices = market.iloc[-2] if len(market) >= 2 else market.iloc[-1]

    rows = []
    for _, row in active.iterrows():
        ticker      = row['Ticker']
        shares      = row['Cur_Shares']
        avg_cost    = row['Avg_Cost']
        cur_px      = last_prices.get(ticker, 0)
        prev_px     = prev_prices.get(ticker, 0)
        cost_basis  = shares * avg_cost
        mkt_value   = shares * cur_px
        unreal_pnl  = mkt_value - cost_basis
        pnl_pct     = unreal_pnl / cost_basis if cost_basis > 0 else 0
        day_chg_pct = (cur_px - prev_px) / prev_px if prev_px > 0 else 0
        weight      = mkt_value / current_nav if current_nav > 0 else 0
        rows.append({
            'Ticker':     ticker,
            'Company':    row.get('Company', ''),
            'Sector':     row.get('Sector', ''),
            'Shares':     shares,
            'Avg Cost':   avg_cost,
            'Price':      cur_px,
            'Day Chg%':   day_chg_pct,
            'Cost Basis': cost_basis,
            'Mkt Value':  mkt_value,
            'Unreal P&L': unreal_pnl,
            'P&L%':       pnl_pct,
            'Weight':     weight,
        })

    pos_df = pd.DataFrame(rows).sort_values('Mkt Value', ascending=False)

    st.dataframe(
        pos_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Shares':     st.column_config.NumberColumn('Shares',     format='%.4f'),
            'Avg Cost':   st.column_config.NumberColumn('Avg Cost',   format='$%.2f'),
            'Price':      st.column_config.NumberColumn('Price',      format='$%.2f'),
            'Day Chg%':   st.column_config.NumberColumn('Day Chg%',   format='%.2f%%'),
            'Cost Basis': st.column_config.NumberColumn('Cost Basis', format='$%,.2f'),
            'Mkt Value':  st.column_config.NumberColumn('Mkt Value',  format='$%,.2f'),
            'Unreal P&L': st.column_config.NumberColumn('Unreal P&L', format='$%,.2f'),
            'P&L%':       st.column_config.NumberColumn('P&L%',       format='%.2f%%'),
            'Weight':     st.column_config.NumberColumn('Weight',     format='%.2f%%'),
        },
    )

    if 'Sector' in pos_df.columns and not pos_df['Sector'].isna().all():
        st.markdown('<div class="bbg-section">SECTOR EXPOSURE</div>', unsafe_allow_html=True)
        sector_df = (pos_df.groupby('Sector')['Mkt Value']
                     .sum().reset_index().sort_values('Mkt Value'))
        fig_sec = go.Figure(go.Bar(
            x=sector_df['Mkt Value'],
            y=sector_df['Sector'],
            orientation='h',
            marker_color=ACCENT_BLUE,
        ))
        fig_sec.update_layout(
            **CHART_THEME,
            title="Market Value by Sector",
            xaxis_title="Market Value ($)",
            yaxis_title="",
            height=max(200, len(sector_df) * 36),
        )
        st.plotly_chart(fig_sec, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 3 — CORRELATION
# ─────────────────────────────────────────────
def page_correlation():
    page_header()
    st.markdown('<div class="bbg-section">CORRELATION MATRIX — ACTIVE POSITIONS</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<span style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED}">'
        f'Blue = negative correlation (diversifying) &nbsp;|&nbsp; '
        f'Red = positive correlation (concentrated risk)</span>',
        unsafe_allow_html=True,
    )

    if corr_filtered.empty:
        st.warning("No correlation data for active positions.")
        return

    fig = go.Figure(go.Heatmap(
        z=corr_filtered.values,
        x=corr_filtered.columns.tolist(),
        y=corr_filtered.index.tolist(),
        colorscale=[
            [0.0, ACCENT_BLUE],
            [0.5, BG_HEADER],
            [1.0, NEGATIVE],
        ],
        zmid=0, zmin=-1, zmax=1,
        text=corr_filtered.round(2).values,
        texttemplate='%{text}',
        textfont=dict(family='IBM Plex Mono', size=9, color=TEXT_PRIMARY),
        showscale=True,
        colorbar=dict(
            bgcolor=BG_SECONDARY,
            bordercolor=BORDER,
            tickfont=dict(family='IBM Plex Mono', size=9),
        ),
    ))
    fig.update_layout(
        **CHART_THEME,
        title='Daily Return Correlations (Active Positions)',
        height=520,
        xaxis=dict(side='bottom', gridcolor=BORDER, tickfont=dict(family='IBM Plex Mono', size=9)),
        yaxis=dict(gridcolor=BORDER, tickfont=dict(family='IBM Plex Mono', size=9)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Notable pairs
    pairs = []
    tlist = corr_filtered.columns.tolist()
    for i in range(len(tlist)):
        for j in range(i + 1, len(tlist)):
            v = corr_filtered.iloc[i, j]
            if pd.notna(v):
                pairs.append((tlist[i], tlist[j], float(v)))

    if pairs:
        pairs.sort(key=lambda x: x[2])
        c_low, c_high = st.columns(2)

        with c_high:
            st.markdown('<div class="bbg-section">HIGHEST CORRELATION</div>', unsafe_allow_html=True)
            for t1, t2, v in sorted(pairs, key=lambda x: x[2], reverse=True)[:3]:
                color = NEGATIVE if v > 0.5 else AMBER
                st.markdown(
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:11px;'
                    f'padding:4px 0;border-bottom:1px solid {BORDER}">'
                    f'<span style="color:{color}">{v:+.2f}</span>'
                    f'&nbsp;&nbsp;{t1} / {t2}</div>',
                    unsafe_allow_html=True,
                )

        with c_low:
            st.markdown('<div class="bbg-section">LOWEST CORRELATION</div>', unsafe_allow_html=True)
            for t1, t2, v in pairs[:3]:
                color = POSITIVE if v < 0 else TEXT_PRIMARY
                st.markdown(
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:11px;'
                    f'padding:4px 0;border-bottom:1px solid {BORDER}">'
                    f'<span style="color:{color}">{v:+.2f}</span>'
                    f'&nbsp;&nbsp;{t1} / {t2}</div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────
# PAGE 4 — RISK METRICS
# ─────────────────────────────────────────────
def page_risk():
    page_header()
    st.markdown(
        f'<div class="bbg-section">RISK ANALYTICS — {len(equity_curve)} TRADING DAYS | RF: 4.50%</div>',
        unsafe_allow_html=True,
    )

    dr       = equity_curve['Daily_Return'].dropna()
    rf_daily = 0.045 / 252
    nav_s    = equity_curve['NAV']

    _ann_ret = (1 + dr.mean()) ** 252 - 1
    _ann_vol = dr.std() * (252 ** 0.5)
    _sharpe  = (_ann_ret - 0.045) / _ann_vol if _ann_vol > 0 else 0

    downside = dr[dr < rf_daily]
    down_vol = downside.std() * (252 ** 0.5) if len(downside) > 0 else 1
    sortino  = (_ann_ret - 0.045) / down_vol if down_vol > 0 else 0

    _max_dd  = ((nav_s / nav_s.cummax()) - 1).min()
    var_95   = dr.quantile(0.05)
    var_99   = dr.quantile(0.01)
    cvar_95  = dr[dr <= var_95].mean()

    beta = None
    bm_col = None
    if 'VOO' in market.columns:
        bm_col = market['VOO'].pct_change().dropna()
    elif not benchmarks.empty and 'VOO' in benchmarks.columns:
        bm_col = benchmarks['VOO'].pct_change().dropna()
    if bm_col is not None:
        aligned = dr.align(bm_col, join='inner')
        p_r, v_r = aligned[0], aligned[1]
        if len(p_r) > 5:
            beta = np.cov(p_r, v_r)[0][1] / np.var(v_r)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Annualized Return", f"{_ann_ret:+.2%}")
        st.metric("Sharpe Ratio",      f"{_sharpe:.2f}")
        st.metric("Beta to VOO",       f"{beta:.2f}" if beta is not None else "N/A")
    with c2:
        st.metric("Annualized Vol",    f"{_ann_vol:.2%}")
        st.metric("Sortino Ratio",     f"{sortino:.2f}")
        st.metric("Max Drawdown",      f"{_max_dd:.2%}")
    with c3:
        st.metric("VaR 95% (Daily)",   f"{var_95:.2%}")
        st.metric("VaR 99% (Daily)",   f"{var_99:.2%}")
        st.metric("CVaR 95% (Daily)",  f"{cvar_95:.2%}")

    st.markdown('<div class="bbg-section">RETURN DISTRIBUTION</div>', unsafe_allow_html=True)
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=dr * 100, nbinsx=50,
        marker_color=ACCENT_BLUE,
        opacity=0.85,
        name='Daily Returns',
    ))
    fig_hist.add_vline(x=var_95 * 100, line_dash='dash', line_color=AMBER,
                       annotation_text=f'VaR 95%: {var_95:.2%}',
                       annotation_font_color=AMBER, annotation_font_size=9)
    fig_hist.add_vline(x=var_99 * 100, line_dash='dash', line_color=NEGATIVE,
                       annotation_text=f'VaR 99%: {var_99:.2%}',
                       annotation_font_color=NEGATIVE, annotation_font_size=9)
    fig_hist.update_layout(
        **CHART_THEME,
        title='Daily Return Distribution (%)',
        xaxis_title='Return (%)',
        yaxis_title='Frequency',
        height=300,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown('<div class="bbg-section">DOLLAR IMPACT AT CURRENT NAV</div>', unsafe_allow_html=True)
    impact_df = pd.DataFrame({
        'Metric':        ['VaR 95%', 'VaR 99%', 'CVaR 95%', 'Max Drawdown'],
        'Daily Impact':  [f"${var_95*current_nav:,.2f}",  f"${var_99*current_nav:,.2f}",
                          f"${cvar_95*current_nav:,.2f}", f"${_max_dd*current_nav:,.2f}"],
        'Annual Impact': [f"${var_95*current_nav*252:,.2f}", f"${var_99*current_nav*252:,.2f}",
                          f"${cvar_95*current_nav*252:,.2f}", "—"],
    })
    st.dataframe(impact_df, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 5 — BENCHMARKS
# ─────────────────────────────────────────────
def page_benchmarks():
    page_header()
    st.markdown('<div class="bbg-section">PERFORMANCE VS BENCHMARKS</div>', unsafe_allow_html=True)

    nav_s = equity_curve['NAV']

    def period_return(series, n):
        s = series.dropna()
        if len(s) < n + 1:
            return None
        return float(s.iloc[-1] / s.iloc[-n - 1] - 1)

    ytd_start = datetime(datetime.now().year, 1, 1)
    ytd_days  = max(len(nav_s[nav_s.index >= pd.Timestamp(ytd_start)]) - 1, 1)

    periods = [('1D', 1), ('1W', 5), ('1M', 21), ('3M', 63), ('YTD', ytd_days), ('1Y', 252)]

    rows = []
    for label, n in periods:
        row = {'Period': label, 'Portfolio': period_return(nav_s, n)}
        for bm in ['VOO', 'QQQ']:
            bm_s = benchmarks[bm].dropna() if (not benchmarks.empty and bm in benchmarks.columns) else pd.Series()
            row[bm] = period_return(bm_s, n) if not bm_s.empty else None
        rows.append(row)

    perf_df = pd.DataFrame(rows)

    def fmt(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        c = POSITIVE if v >= 0 else NEGATIVE
        return f'<span style="color:{c};font-family:IBM Plex Mono,monospace">{v:+.2%}</span>'

    html_rows = "".join(
        f"<tr style='border-bottom:1px solid {BORDER}'>"
        f"<td style='padding:6px 12px;font-family:IBM Plex Mono,monospace;font-size:12px;"
        f"font-weight:600;color:{TEXT_PRIMARY}'>{r['Period']}</td>"
        f"<td style='padding:6px 12px;font-size:12px'>{fmt(r['Portfolio'])}</td>"
        f"<td style='padding:6px 12px;font-size:12px'>{fmt(r.get('VOO'))}</td>"
        f"<td style='padding:6px 12px;font-size:12px'>{fmt(r.get('QQQ'))}</td>"
        f"</tr>"
        for _, r in perf_df.iterrows()
    )
    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;background:{BG_SECONDARY};
                  border:1px solid {BORDER}">
      <thead>
        <tr style="background:{BG_HEADER}">
          <th style="padding:6px 12px;text-align:left;font-size:10px;letter-spacing:1px;
                     text-transform:uppercase;color:{TEXT_MUTED};font-family:IBM Plex Sans,sans-serif">
              Period</th>
          <th style="padding:6px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;
                     color:{TEXT_MUTED};font-family:IBM Plex Sans,sans-serif">Portfolio</th>
          <th style="padding:6px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;
                     color:{TEXT_MUTED};font-family:IBM Plex Sans,sans-serif">VOO (S&P 500)</th>
          <th style="padding:6px 12px;font-size:10px;letter-spacing:1px;text-transform:uppercase;
                     color:{TEXT_MUTED};font-family:IBM Plex Sans,sans-serif">QQQ (Nasdaq)</th>
        </tr>
      </thead>
      <tbody>{html_rows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bbg-section">NORMALIZED PERFORMANCE (BASE 100)</div>', unsafe_allow_html=True)

    port_rb = (nav_s / nav_s.iloc[0]) * 100

    fig_bm = go.Figure()
    fig_bm.add_trace(go.Scatter(
        x=port_rb.index, y=port_rb,
        name='Portfolio', line=dict(color=TEXT_PRIMARY, width=2),
    ))
    if not benchmarks.empty:
        for bm, color, label in [('VOO', ACCENT_BLUE, 'VOO (S&P 500)'), ('QQQ', TEXT_MUTED, 'QQQ (Nasdaq)')]:
            if bm in benchmarks.columns:
                s = benchmarks[bm].dropna()
                if not s.empty:
                    fig_bm.add_trace(go.Scatter(
                        x=s.index, y=(s / s.iloc[0]) * 100,
                        name=label, line=dict(color=color, width=1, dash='dot'),
                    ))
    fig_bm.update_layout(
        **CHART_THEME,
        title='Normalized Performance (Base = 100)',
        yaxis_title='Value', xaxis_title='Date', height=380,
    )
    st.plotly_chart(fig_bm, use_container_width=True)

    st.markdown('<div class="bbg-section">ALPHA VS BENCHMARKS</div>', unsafe_allow_html=True)
    port_tot = float(nav_s.iloc[-1] / nav_s.iloc[0] - 1)
    ac1, ac2, ac3 = st.columns(3)
    for col, bm, label in [(ac1, 'VOO', 'Alpha vs S&P 500'), (ac2, 'QQQ', 'Alpha vs Nasdaq')]:
        if not benchmarks.empty and bm in benchmarks.columns:
            s = benchmarks[bm].dropna()
            bm_tot = float(s.iloc[-1] / s.iloc[0] - 1) if len(s) > 1 else 0
            alpha  = port_tot - bm_tot
            col.metric(label, f"{alpha:+.2%}")
        else:
            col.metric(label, "N/A")
    if not benchmarks.empty and 'VOO' in benchmarks.columns:
        voo_r   = benchmarks['VOO'].pct_change().dropna()
        aligned = daily_ret.align(voo_r, join='inner')
        if len(aligned[0]) > 5:
            ac3.metric("Corr to VOO", f"{aligned[0].corr(aligned[1]):.3f}")
        else:
            ac3.metric("Corr to VOO", "N/A")
    else:
        ac3.metric("Corr to VOO", "N/A")


# ─────────────────────────────────────────────
# PAGE 6 — TRADE LOG
# ─────────────────────────────────────────────
def page_trade_log():
    page_header()
    st.markdown(f'<div class="bbg-section">TRADE HISTORY — {len(trades)} TRANSACTIONS</div>',
                unsafe_allow_html=True)

    buys  = trades[trades['Action'].str.upper() == 'BUY']  if 'Action' in trades.columns else pd.DataFrame()
    sells = trades[trades['Action'].str.upper() == 'SELL'] if 'Action' in trades.columns else pd.DataFrame()
    total_inv  = buys['Amount'].abs().sum()  if not buys.empty  and 'Amount' in buys.columns  else 0
    total_proc = sells['Amount'].sum()        if not sells.empty and 'Amount' in sells.columns else 0

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Total Buys",        len(buys))
    sc2.metric("Total Sells",       len(sells))
    sc3.metric("Total Invested",    f"${total_inv:,.2f}")
    sc4.metric("Total Proceeds",    f"${total_proc:,.2f}")
    sc5.metric("Net Cash Deployed", f"${total_inv - total_proc:,.2f}")

    if 'Symbol' in trades.columns:
        ticker_filter = st.multiselect(
            "Filter by ticker",
            options=sorted(trades['Symbol'].dropna().unique()),
        )
        display = trades[trades['Symbol'].isin(ticker_filter)] if ticker_filter else trades
    else:
        display = trades

    if 'Date' in display.columns:
        display = display.sort_values('Date', ascending=False)

    col_cfg = {}
    if 'Amount' in display.columns:
        col_cfg['Amount'] = st.column_config.NumberColumn('Amount', format='$%,.2f')
    if 'Price' in display.columns:
        col_cfg['Price']  = st.column_config.NumberColumn('Price',  format='$%.4f')

    st.dataframe(display, use_container_width=True, hide_index=True, column_config=col_cfg)


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
if page == "Dashboard":
    page_dashboard()
elif page == "Positions":
    page_positions()
elif page == "Correlation":
    page_correlation()
elif page == "Risk Metrics":
    page_risk()
elif page == "Benchmarks":
    page_benchmarks()
elif page == "Trade Log":
    page_trade_log()
