import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')

from db import (
    get_connection, get_all_trades, get_cash_flows, get_price_history,
    get_ticker_info, insert_trade, upsert_ticker_info,
    compute_positions, compute_equity_curve, refresh_eod_prices,
)

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
# PAGE CONFIG
# ─────────────────────────────────────────────
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
# AUTH GATE
# ─────────────────────────────────────────────
def check_password():
    """Returns True if the user is authenticated."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown(f"""
    <div style="max-width:380px;margin:120px auto;background:{BG_SECONDARY};
                border:1px solid {BORDER};padding:32px">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:600;
                color:{TEXT_HEADER};letter-spacing:3px;margin-bottom:4px">
    PORTFOLIO TERMINAL
    </div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:{TEXT_MUTED};
                margin-bottom:24px;letter-spacing:1px">
    AUTHENTICATION REQUIRED
    </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                            placeholder="Enter password...")
        if st.button("LOGIN", use_container_width=True):
            if pwd == st.secrets["auth"]["password"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()


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
conn = get_connection()


@st.cache_data(ttl=300)
def load_all_data():
    """Load all data from Supabase, compute positions and equity curve."""
    _conn = get_connection()
    trades_df     = get_all_trades(_conn)
    cash_flows_df = get_cash_flows(_conn)
    prices_df     = get_price_history(_conn)
    ticker_info   = get_ticker_info(_conn)
    return trades_df, cash_flows_df, prices_df, ticker_info


try:
    trades, cash_flows, prices_df, ticker_info = load_all_data()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Check your Supabase connection string in .streamlit/secrets.toml")
    st.stop()

if trades.empty and prices_df.empty:
    st.warning("No data found. Run `python migrate_excel.py` to migrate your Excel history first.")
    st.stop()

# ── Derived data ────────────────────────────────────────────────────────────
positions     = compute_positions(trades)
equity_curve  = compute_equity_curve(trades, cash_flows, prices_df)

if equity_curve.empty:
    st.warning("Equity curve could not be computed — check that price_cache has data.")
    st.stop()

# Price matrix: wide format (date × ticker) — used for last price lookups
prices_wide = (
    prices_df.pivot(index='date', columns='ticker', values='close_price')
    if not prices_df.empty else pd.DataFrame()
)
if not prices_wide.empty:
    prices_wide.index = pd.to_datetime(prices_wide.index)
    prices_wide = prices_wide.sort_index()

# Active positions enriched with company/sector from ticker_info
if not positions.empty and not ticker_info.empty:
    ti = ticker_info.rename(columns={'ticker': 'Ticker', 'company': 'Company', 'sector': 'Sector'})
    active = positions.merge(ti[['Ticker', 'Company', 'Sector']], on='Ticker', how='left')
    active['Company'] = active['Company'].fillna('')
    active['Sector']  = active['Sector'].fillna('')
else:
    active = positions.copy()
    if not active.empty:
        active['Company'] = ''
        active['Sector']  = ''

# Scalar metrics
current_nav   = float(equity_curve['NAV'].iloc[-1])
total_return  = float(equity_curve['Cumul_Return'].iloc[-1])
max_drawdown  = float(equity_curve['Drawdown'].min())
daily_ret     = equity_curve['Daily_Return'].dropna()
ann_vol       = float(daily_ret.std() * (252 ** 0.5))
ann_ret_val   = float((1 + daily_ret.mean()) ** 252 - 1)
sharpe        = (ann_ret_val - 0.045) / ann_vol if ann_vol > 0 else 0.0
today_return  = float(equity_curve['Daily_Return'].iloc[-1])
start_date    = equity_curve.index[0]
end_date      = equity_curve.index[-1]

# Correlation matrix over active tickers
active_tickers = active['Ticker'].tolist() if not active.empty else []
if not prices_wide.empty and active_tickers:
    price_ret     = prices_wide.pct_change().dropna()
    corr          = price_ret.corr().round(4)
    corr_filtered = corr.loc[
        [t for t in active_tickers if t in corr.index],
        [t for t in active_tickers if t in corr.columns],
    ]
else:
    corr          = pd.DataFrame()
    corr_filtered = pd.DataFrame()

# Correlation across all tickers in price_cache (for pages that need full corr)
market = prices_wide  # alias — used in page functions below


# ─────────────────────────────────────────────
# BENCHMARKS
# ─────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_benchmarks(start_str: str):
    from datetime import date as _date
    end_str = _date.today().strftime('%Y-%m-%d')
    data = {}
    for t in ['VOO', 'QQQ']:
        try:
            df = yf.download(t, start=start_str, end=end_str,
                             auto_adjust=True, progress=False)
            if not df.empty:
                data[t] = df['Close'].squeeze()
        except Exception:
            pass
    return pd.DataFrame(data) if data else pd.DataFrame()


benchmarks = fetch_benchmarks(start_date.strftime('%Y-%m-%d'))


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
    <span style="color:{TEXT_MUTED}">TOTAL RETURN</span> <span style="color:{ret_color}">{total_return:+.2%}</span> &nbsp;|&nbsp;
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
    {end_date.strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;color:{TEXT_MUTED};letter-spacing:2px;'
                f'text-transform:uppercase;padding:12px 0 6px 0;font-family:IBM Plex Sans,sans-serif">'
                f'NAVIGATION</div>', unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "Dashboard",
        "Enter Trade",
        "Positions",
        "Correlation",
        "Risk Metrics",
        "Benchmarks",
        "Kelly Sizing",
        "Factor Exposure",
        "Trade Log",
    ], label_visibility="collapsed")

    st.divider()

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
    Source: Supabase PostgreSQL<br>
    Last: {end_date.strftime('%Y-%m-%d')}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    page_header()
    st.markdown('<div class="bbg-section">KEY METRICS</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Portfolio NAV",   f"${current_nav:,.2f}")
    c2.metric("Total Return",    f"{total_return:+.2%}", delta=f"{today_return:+.2%}")
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
        if not active.empty and not market.empty:
            last_prices = market.iloc[-1]
            alloc_rows  = []
            for _, row in active.iterrows():
                px_val = last_prices.get(row['Ticker'], 0)
                val    = row['Cur_Shares'] * px_val
                alloc_rows.append({
                    'Ticker': row['Ticker'],
                    'Value':  val,
                    'Weight': val / current_nav if current_nav > 0 else 0,
                })
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
# PAGE: ENTER TRADE
# ─────────────────────────────────────────────
def page_enter_trade():
    page_header()
    st.markdown('<div class="bbg-section">ENTER TRADE</div>', unsafe_allow_html=True)

    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
        trade_date    = st.date_input("Trade Date", value=date.today())
        ticker_input  = st.text_input("Ticker", placeholder="e.g. AAPL").upper().strip()
        action        = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        quantity      = st.number_input("Quantity (shares)", min_value=0.0,
                                        step=0.000001, format="%.6f")

        # Auto-fill last close from yfinance when ticker is entered
        suggested_price = 0.0
        if ticker_input:
            try:
                hist = yf.Ticker(ticker_input).history(period='2d')
                if not hist.empty:
                    suggested_price = float(hist['Close'].iloc[-1])
            except Exception:
                pass

        price = st.number_input("Price per Share", min_value=0.0,
                                value=suggested_price, format="%.4f")

        # Compute amount preview
        amount_preview = quantity * price
        if action == "BUY":
            amount_preview = -amount_preview   # negative = cash out

        amt_color = NEGATIVE if amount_preview < 0 else POSITIVE
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:13px;'
            f'padding:12px 0;border-top:1px solid {BORDER};margin-top:8px">'
            f'Amount: <span style="color:{amt_color}">${amount_preview:,.2f}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        submit = st.button("SUBMIT TRADE", use_container_width=True,
                           type="primary" if quantity > 0 and price > 0 and ticker_input else "secondary")

        if submit:
            if not ticker_input:
                st.error("Ticker is required.")
            elif quantity <= 0:
                st.error("Quantity must be greater than 0.")
            elif price <= 0:
                st.error("Price must be greater than 0.")
            else:
                with st.spinner("Saving trade..."):
                    trade_dict = {
                        'date':       trade_date,
                        'settlement': None,
                        'ticker':     ticker_input,
                        'action':     action,
                        'quantity':   round(quantity, 6),
                        'price':      round(price, 4),
                        'amount':     round(amount_preview, 2),
                    }
                    insert_trade(conn, trade_dict)

                    # Fetch / update ticker info from yfinance
                    try:
                        info = yf.Ticker(ticker_input).info
                        upsert_ticker_info(conn, [{
                            'ticker':  ticker_input,
                            'company': info.get('longName', ''),
                            'sector':  info.get('sector', ''),
                        }])
                    except Exception:
                        pass

                    # Refresh EOD prices for this ticker
                    try:
                        refresh_eod_prices(conn, [ticker_input])
                    except Exception:
                        pass

                    st.cache_data.clear()

                st.success(f"Trade recorded: {action} {quantity:.4f} {ticker_input} @ ${price:.4f}")
                st.rerun()

    with col_preview:
        st.markdown(f'<div class="bbg-section">CURRENT POSITION</div>', unsafe_allow_html=True)
        if ticker_input and not active.empty and ticker_input in active['Ticker'].values:
            pos = active[active['Ticker'] == ticker_input].iloc[0]
            cur_px = 0.0
            if not market.empty and ticker_input in market.columns:
                cur_px = float(market[ticker_input].iloc[-1])
            mkt_val = pos['Cur_Shares'] * cur_px
            unreal  = mkt_val - (pos['Cur_Shares'] * pos['Avg_Cost'])
            st.metric("Shares Held",    f"{pos['Cur_Shares']:.4f}")
            st.metric("Avg Cost",       f"${pos['Avg_Cost']:.4f}")
            st.metric("Last Price",     f"${cur_px:.4f}")
            st.metric("Market Value",   f"${mkt_val:,.2f}")
            st.metric("Unrealized P&L", f"${unreal:,.2f}",
                      delta=f"{(unreal / (pos['Cur_Shares'] * pos['Avg_Cost'])):.2%}"
                      if pos['Avg_Cost'] > 0 else None)
        elif ticker_input:
            st.info(f"No current position in {ticker_input}")
            if suggested_price > 0:
                st.markdown(
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:11px;'
                    f'color:{TEXT_MUTED};margin-top:8px">Last close: ${suggested_price:.4f}</div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────
# PAGE: POSITIONS
# ─────────────────────────────────────────────
def page_positions():
    page_header()
    st.markdown(
        f'<div class="bbg-section">ACTIVE POSITIONS  —  {len(active)} HOLDINGS</div>',
        unsafe_allow_html=True,
    )

    if active.empty or market.empty:
        st.info("No active positions.")
        return

    last_prices = market.iloc[-1]
    prev_prices = market.iloc[-2] if len(market) >= 2 else market.iloc[-1]

    rows = []
    for _, row in active.iterrows():
        ticker     = row['Ticker']
        shares     = row['Cur_Shares']
        avg_cost   = row['Avg_Cost']
        cur_px     = float(last_prices.get(ticker, 0))
        prev_px    = float(prev_prices.get(ticker, 0))
        cost_basis = shares * avg_cost
        mkt_value  = shares * cur_px
        unreal_pnl = mkt_value - cost_basis
        pnl_pct    = unreal_pnl / cost_basis if cost_basis > 0 else 0
        day_chg    = (cur_px - prev_px) / prev_px if prev_px > 0 else 0
        weight     = mkt_value / current_nav if current_nav > 0 else 0
        rows.append({
            'Ticker':     ticker,
            'Company':    row.get('Company', ''),
            'Sector':     row.get('Sector', ''),
            'Shares':     shares,
            'Avg Cost':   avg_cost,
            'Price':      cur_px,
            'Day Chg%':   day_chg,
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
        sector_df = (
            pos_df.groupby('Sector')['Mkt Value']
            .sum().reset_index().sort_values('Mkt Value')
        )
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
# PAGE: CORRELATION
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
# PAGE: RISK METRICS
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

    _max_dd = ((nav_s / nav_s.cummax()) - 1).min()
    var_95  = dr.quantile(0.05)
    var_99  = dr.quantile(0.01)
    cvar_95 = dr[dr <= var_95].mean()

    beta    = None
    bm_col  = None
    if not benchmarks.empty and 'VOO' in benchmarks.columns:
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
        'Daily Impact':  [f"${var_95*current_nav:,.2f}", f"${var_99*current_nav:,.2f}",
                          f"${cvar_95*current_nav:,.2f}", f"${_max_dd*current_nav:,.2f}"],
        'Annual Impact': [f"${var_95*current_nav*252:,.2f}", f"${var_99*current_nav*252:,.2f}",
                          f"${cvar_95*current_nav*252:,.2f}", "—"],
    })
    st.dataframe(impact_df, hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE: BENCHMARKS
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
            s      = benchmarks[bm].dropna()
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
# PAGE: KELLY SIZING
# ─────────────────────────────────────────────
def page_kelly():
    page_header()
    st.markdown('<div class="bbg-section">POSITION SIZING — KELLY CRITERION MONITOR</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<span style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED}">'
        f'Kelly fraction computed from Trade_Log win rate and avg win/loss per ticker. '
        f'Half-Kelly applied as practical sizing limit.</span>',
        unsafe_allow_html=True,
    )

    if trades.empty:
        st.warning("No trade history available.")
        return

    from collections import deque

    def compute_trade_stats(trade_df):
        stats = {}
        for ticker in trade_df['ticker'].unique():
            t_trades  = trade_df[trade_df['ticker'] == ticker].sort_values('date')
            buy_queue = deque()
            realized  = []
            for _, row in t_trades.iterrows():
                action = str(row['action']).strip().upper()
                qty    = abs(float(row['quantity']))
                price  = abs(float(row['price']))
                if action == 'BUY':
                    buy_queue.append([qty, price])
                elif action == 'SELL' and buy_queue:
                    remaining_sell = qty
                    while remaining_sell > 0 and buy_queue:
                        buy_qty, buy_px = buy_queue[0]
                        matched = min(remaining_sell, buy_qty)
                        pnl_pct = (price - buy_px) / buy_px if buy_px > 0 else 0
                        realized.append(pnl_pct)
                        buy_queue[0][0] -= matched
                        remaining_sell  -= matched
                        if buy_queue[0][0] <= 1e-6:
                            buy_queue.popleft()
            if len(realized) < 2:
                continue
            wins     = [r for r in realized if r > 0]
            losses   = [r for r in realized if r <= 0]
            win_rate = len(wins) / len(realized)
            avg_win  = np.mean(wins)            if wins   else 0.0
            avg_loss = abs(np.mean(losses))     if losses else 1e-6
            R        = avg_win / avg_loss if avg_loss > 0 else 0
            kelly_f  = win_rate - (1 - win_rate) / R if R > 0 else 0
            kelly_f  = max(kelly_f, 0)
            stats[ticker] = {
                'Trades':     len(realized),
                'Win Rate':   win_rate,
                'Avg Win':    avg_win,
                'Avg Loss':   avg_loss,
                'Kelly':      kelly_f,
                'Half Kelly': kelly_f / 2,
            }
        return stats

    trade_stats = compute_trade_stats(trades)

    last_prices = market.iloc[-1] if not market.empty else pd.Series()
    kelly_rows  = []
    for _, row in active.iterrows():
        ticker     = row['Ticker']
        shares     = row['Cur_Shares']
        cur_px     = float(last_prices.get(ticker, 0))
        mkt_value  = shares * cur_px
        cur_weight = mkt_value / current_nav if current_nav > 0 else 0
        if ticker in trade_stats:
            ts      = trade_stats[ticker]
            kelly_w = ts['Half Kelly']
            diff    = cur_weight - kelly_w
            if cur_weight > kelly_w * 1.25:
                signal, sig_color = 'REDUCE', NEGATIVE
            elif cur_weight < kelly_w * 0.75:
                signal, sig_color = 'ADD', POSITIVE
            else:
                signal, sig_color = 'HOLD', AMBER
            kelly_rows.append({
                'Ticker':     ticker,
                'Trades':     ts['Trades'],
                'Win Rate':   ts['Win Rate'],
                'Avg Win':    ts['Avg Win'],
                'Avg Loss':   ts['Avg Loss'],
                'Full Kelly': ts['Kelly'],
                'Half Kelly': kelly_w,
                'Current Wt': cur_weight,
                'Diff':       diff,
                'Signal':     signal,
                '_sig_color': sig_color,
            })
        else:
            kelly_rows.append({
                'Ticker':     ticker,
                'Trades':     0,
                'Win Rate':   None,
                'Avg Win':    None,
                'Avg Loss':   None,
                'Full Kelly': None,
                'Half Kelly': None,
                'Current Wt': cur_weight,
                'Diff':       None,
                'Signal':     'NEW',
                '_sig_color': TEXT_MUTED,
            })

    reduces = [r for r in kelly_rows if r['Signal'] == 'REDUCE']
    adds    = [r for r in kelly_rows if r['Signal'] == 'ADD']
    holds   = [r for r in kelly_rows if r['Signal'] == 'HOLD']
    news    = [r for r in kelly_rows if r['Signal'] == 'NEW']

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("REDUCE",           len(reduces))
    sc2.metric("ADD",              len(adds))
    sc3.metric("HOLD",             len(holds))
    sc4.metric("NEW / NO HISTORY", len(news))

    st.markdown('<div class="bbg-section">KELLY SIZING TABLE</div>', unsafe_allow_html=True)
    st.markdown(
        f'<span style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED}">'
        f'Half-Kelly is the practical sizing target. '
        f'REDUCE = current weight > 125% of Half-Kelly. '
        f'ADD = current weight < 75% of Half-Kelly.</span>',
        unsafe_allow_html=True,
    )

    header_style = (f"padding:6px 10px;font-size:10px;text-transform:uppercase;"
                    f"letter-spacing:1px;color:{TEXT_MUTED};font-family:IBM Plex Sans,sans-serif;"
                    f"text-align:right")
    headers = ['Ticker', 'Trades', 'Win Rate', 'Avg Win', 'Avg Loss',
               'Full Kelly', 'Half Kelly', 'Cur Wt', 'Diff', 'Signal']

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return f'<span style="color:#444">—</span>'
        return f'{v:+.2%}'

    def fmt_pct_plain(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return f'<span style="color:#444">—</span>'
        return f'{v:.2%}'

    header_row = "".join(f'<th style="{header_style}">{h}</th>' for h in headers)
    data_rows  = ""
    for r in kelly_rows:
        diff_color = NEGATIVE if (r['Diff'] or 0) > 0.01 else (POSITIVE if (r['Diff'] or 0) < -0.01 else TEXT_MUTED)
        data_rows += (
            f"<tr style='border-bottom:1px solid {BORDER}'>"
            f"<td style='padding:5px 10px;font-family:IBM Plex Mono,monospace;font-size:11px;"
            f"font-weight:600;color:{TEXT_PRIMARY}'>{r['Ticker']}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{TEXT_MUTED}'>{r['Trades']}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right'>{fmt_pct_plain(r['Win Rate'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{POSITIVE}'>{fmt_pct_plain(r['Avg Win'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{NEGATIVE}'>{fmt_pct_plain(r['Avg Loss'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{TEXT_MUTED}'>{fmt_pct_plain(r['Full Kelly'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{ACCENT_BLUE}'>{fmt_pct_plain(r['Half Kelly'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{TEXT_PRIMARY}'>{r['Current Wt']:.2%}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;color:{diff_color}'>{fmt_pct(r['Diff'])}</td>"
            f"<td style='padding:5px 10px;font-size:11px;text-align:right;"
            f"font-weight:600;color:{r['_sig_color']}'>{r['Signal']}</td>"
            f"</tr>"
        )

    st.markdown(f"""
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;background:{BG_SECONDARY};border:1px solid {BORDER}">
      <thead><tr style="background:{BG_HEADER}">{header_row}</tr></thead>
      <tbody>{data_rows}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="bbg-section">CURRENT WEIGHT VS HALF-KELLY TARGET</div>',
                unsafe_allow_html=True)

    chart_rows = [r for r in kelly_rows if r['Half Kelly'] is not None]
    if chart_rows:
        ch_df = pd.DataFrame(chart_rows).sort_values('Current Wt', ascending=True)
        fig_k = go.Figure()
        fig_k.add_trace(go.Bar(
            y=ch_df['Ticker'], x=ch_df['Current Wt'],
            name='Current Weight', orientation='h',
            marker_color=ACCENT_BLUE, opacity=0.9,
        ))
        fig_k.add_trace(go.Bar(
            y=ch_df['Ticker'], x=ch_df['Half Kelly'],
            name='Half-Kelly Target', orientation='h',
            marker_color=AMBER, opacity=0.6,
        ))
        fig_k.update_layout(
            **CHART_THEME,
            title='Current Weight vs Half-Kelly Optimal Weight',
            xaxis_title='Portfolio Weight',
            xaxis_tickformat='.1%',
            barmode='overlay',
            height=max(250, len(chart_rows) * 32),
        )
        st.plotly_chart(fig_k, use_container_width=True)

    st.markdown(
        f'<div style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED};'
        f'margin-top:12px;line-height:1.8">'
        f'Kelly formula: f = W - (1-W)/R &nbsp;|&nbsp; '
        f'W = win rate &nbsp;|&nbsp; R = avg win / avg loss &nbsp;|&nbsp; '
        f'Half-Kelly applied to reduce ruin risk. '
        f'Minimum 2 completed round-trips required for signal.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# PAGE: FACTOR EXPOSURE
# ─────────────────────────────────────────────
def page_factors():
    page_header()
    st.markdown('<div class="bbg-section">ROLLING FACTOR EXPOSURE</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<span style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED}">'
        f'Daily OLS regression of portfolio returns against 5 factors. '
        f'Rolling 30-day window. Beta = sensitivity of portfolio to each factor.</span>',
        unsafe_allow_html=True,
    )

    FACTORS = {
        'SPY':  ('Market Beta',    TEXT_PRIMARY),
        'GLD':  ('Gold/Inflation', AMBER),
        'TLT':  ('Duration/Rates', ACCENT_BLUE),
        'UUP':  ('USD Strength',   '#A78BFA'),
        'VIXY': ('Volatility',     NEGATIVE),
    }

    @st.cache_data(ttl=1800)
    def fetch_factors(start_str: str):
        from datetime import date as _date
        end_str = _date.today().strftime('%Y-%m-%d')
        result  = {}
        for ticker in FACTORS:
            try:
                df = yf.download(ticker, start=start_str, end=end_str,
                                 auto_adjust=True, progress=False)
                if not df.empty:
                    result[ticker] = df['Close'].squeeze()
            except Exception:
                pass
        return pd.DataFrame(result)

    factor_data = fetch_factors(start_date.strftime('%Y-%m-%d'))

    if factor_data.empty:
        st.warning("Could not fetch factor data. Check your internet connection.")
        return

    factor_returns = factor_data.pct_change().dropna()
    port_returns   = equity_curve['Daily_Return'].dropna()
    common         = port_returns.index.intersection(factor_returns.index)

    if len(common) < 30:
        st.warning(f"Only {len(common)} common trading days — need at least 30 for rolling regression.")
        return

    p_ret              = port_returns.loc[common]
    f_ret              = factor_returns.loc[common]
    available_factors  = [f for f in FACTORS if f in f_ret.columns]

    if not available_factors:
        st.warning("None of the factor tickers (SPY, GLD, TLT, UUP, VIXY) could be fetched.")
        return

    from numpy.linalg import lstsq

    window     = 30
    roll_betas = {f: [] for f in available_factors}
    roll_r2    = []
    roll_dates = []

    for i in range(window, len(p_ret) + 1):
        y       = p_ret.iloc[i - window:i].values
        X       = f_ret[available_factors].iloc[i - window:i].values
        X_const = np.column_stack([np.ones(len(X)), X])
        try:
            coeffs, _, _, _ = lstsq(X_const, y, rcond=None)
            y_hat  = X_const @ coeffs
            ss_res = np.sum((y - y_hat) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            for j, f in enumerate(available_factors):
                roll_betas[f].append(coeffs[j + 1])
            roll_r2.append(r2)
            roll_dates.append(p_ret.index[i - 1])
        except Exception:
            for f in available_factors:
                roll_betas[f].append(np.nan)
            roll_r2.append(np.nan)
            roll_dates.append(p_ret.index[i - 1])

    st.markdown('<div class="bbg-section">CURRENT FACTOR BETAS (LAST 30 DAYS)</div>',
                unsafe_allow_html=True)

    beta_cols = st.columns(len(available_factors))
    for col, f in zip(beta_cols, available_factors):
        b_val = roll_betas[f][-1] if roll_betas[f] else None
        if b_val is not None and not np.isnan(b_val):
            col.metric(FACTORS[f][0], f"{b_val:.3f}")
        else:
            col.metric(FACTORS[f][0], "N/A")

    if roll_r2:
        cur_r2    = roll_r2[-1]
        fit_label = ("good fit" if cur_r2 > 0.7 else
                     "moderate fit" if cur_r2 > 0.4 else
                     "low fit — idiosyncratic returns dominate")
        st.markdown(
            f'<div style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED};'
            f'margin-bottom:12px">Model R² (last 30d): '
            f'<span style="color:{TEXT_PRIMARY}">{cur_r2:.3f}</span> — {fit_label}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="bbg-section">ROLLING 30-DAY FACTOR BETAS</div>',
                unsafe_allow_html=True)

    fig_factors = go.Figure()
    for f in available_factors:
        _, color = FACTORS[f]
        fig_factors.add_trace(go.Scatter(
            x=roll_dates, y=roll_betas[f],
            name=FACTORS[f][0],
            line=dict(color=color, width=1.5),
            mode='lines',
        ))
    fig_factors.add_hline(y=0, line_color=BORDER, line_width=1)
    fig_factors.update_layout(
        **CHART_THEME,
        title='Rolling 30-Day Factor Betas',
        yaxis_title='Beta',
        height=380,
    )
    st.plotly_chart(fig_factors, use_container_width=True)

    st.markdown('<div class="bbg-section">FACTOR CONTRIBUTION SNAPSHOT</div>',
                unsafe_allow_html=True)

    snap_betas  = {FACTORS[f][0]: roll_betas[f][-1]
                   for f in available_factors
                   if roll_betas[f] and not np.isnan(roll_betas[f][-1])}
    snap_colors = [FACTORS[f][1] for f in available_factors
                   if roll_betas[f] and not np.isnan(roll_betas[f][-1])]

    if snap_betas:
        fig_snap = go.Figure(go.Bar(
            x=list(snap_betas.keys()),
            y=list(snap_betas.values()),
            marker_color=snap_colors,
        ))
        fig_snap.add_hline(y=0, line_color=BORDER, line_width=1)
        fig_snap.update_layout(
            **CHART_THEME,
            title='Current Factor Betas (Last 30-Day Window)',
            yaxis_title='Beta',
            height=280,
        )
        st.plotly_chart(fig_snap, use_container_width=True)

    st.markdown(
        f'<div style="font-size:10px;font-family:IBM Plex Mono,monospace;color:{TEXT_MUTED};'
        f'margin-top:8px;line-height:1.8">'
        f'SPY = market direction &nbsp;|&nbsp; GLD = gold/inflation hedge &nbsp;|&nbsp; '
        f'TLT = long-duration rates &nbsp;|&nbsp; UUP = USD strength &nbsp;|&nbsp; '
        f'VIXY = short volatility exposure. '
        f'Positive beta = portfolio moves with factor. Negative = inverse.</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# PAGE: TRADE LOG
# ─────────────────────────────────────────────
def page_trade_log():
    page_header()
    st.markdown(
        f'<div class="bbg-section">TRADE HISTORY — {len(trades)} TRANSACTIONS</div>',
        unsafe_allow_html=True,
    )

    if trades.empty:
        st.info("No trades recorded yet. Use 'Enter Trade' to add your first trade.")
        return

    buys  = trades[trades['action'].str.upper() == 'BUY']
    sells = trades[trades['action'].str.upper() == 'SELL']
    total_inv  = buys['amount'].abs().sum()  if not buys.empty  else 0
    total_proc = sells['amount'].sum()        if not sells.empty else 0

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Total Buys",        len(buys))
    sc2.metric("Total Sells",       len(sells))
    sc3.metric("Total Invested",    f"${total_inv:,.2f}")
    sc4.metric("Total Proceeds",    f"${total_proc:,.2f}")
    sc5.metric("Net Cash Deployed", f"${total_inv - total_proc:,.2f}")

    ticker_filter = st.multiselect(
        "Filter by ticker",
        options=sorted(trades['ticker'].dropna().unique()),
    )
    display = trades[trades['ticker'].isin(ticker_filter)] if ticker_filter else trades

    display = display.sort_values('date', ascending=False)

    # Rename columns for display
    display_renamed = display.rename(columns={
        'date': 'Date', 'settlement': 'Settlement', 'ticker': 'Ticker',
        'action': 'Action', 'quantity': 'Quantity', 'price': 'Price',
        'amount': 'Amount',
    })

    st.dataframe(
        display_renamed[['Date', 'Ticker', 'Action', 'Quantity', 'Price', 'Amount']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'Amount':   st.column_config.NumberColumn('Amount',   format='$%,.2f'),
            'Price':    st.column_config.NumberColumn('Price',    format='$%.4f'),
            'Quantity': st.column_config.NumberColumn('Quantity', format='%.4f'),
        },
    )


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
if page == "Dashboard":
    page_dashboard()
elif page == "Enter Trade":
    page_enter_trade()
elif page == "Positions":
    page_positions()
elif page == "Correlation":
    page_correlation()
elif page == "Risk Metrics":
    page_risk()
elif page == "Benchmarks":
    page_benchmarks()
elif page == "Kelly Sizing":
    page_kelly()
elif page == "Factor Exposure":
    page_factors()
elif page == "Trade Log":
    page_trade_log()
