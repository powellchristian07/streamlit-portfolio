import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import openpyxl
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
EXCEL_PATH = r"C:\Users\powel\OneDrive\Documents\Portfolio_BUILT_v2.xlsx"

st.set_page_config(
    page_title="Portfolio Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# BLOOMBERG THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0e1a; color: #e0e4ef; }
[data-testid="stSidebar"]          { background-color: #0d1117; border-right: 1px solid #1c2541; }
[data-testid="metric-container"]   { background: #0d1929; border: 1px solid #1c2541;
                                     border-radius: 6px; padding: 12px; }
.dataframe { font-size: 12px !important; }
thead tr th { background-color: #1c2541 !important; color: white !important; }
.positive { color: #00c076 !important; font-weight: 600; }
.negative { color: #ff3b30 !important; font-weight: 600; }
.section-title { font-size: 1.1rem; font-weight: 700; color: #4a9eff;
                 border-bottom: 1px solid #1c2541; padding-bottom: 6px; margin-bottom: 16px; }
div[data-testid="stMetricValue"]  { font-size: 1.4rem !important; font-weight: 700; }
div[data-testid="stMetricLabel"]  { font-size: 0.75rem !important; color: #8892b0; }
div[data-testid="stMetricDelta"]  { font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

CHART_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='#0d1929',
    font=dict(color='#e0e4ef', size=11),
    xaxis=dict(gridcolor='#1c2541', showgrid=True),
    yaxis=dict(gridcolor='#1c2541', showgrid=True),
    margin=dict(l=50, r=20, t=40, b=40),
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

    # Align date indices
    common_dates = market.index.intersection(units.index).intersection(cash.index)
    market = market.loc[common_dates]
    units  = units.loc[common_dates]
    cash   = cash.loc[common_dates]

    # Fill NaN units (closed positions) with 0
    units = units.fillna(0)

    # Invested value = sum(shares × price) per day
    shared_tickers = market.columns.intersection(units.columns)
    invested = (units[shared_tickers] * market[shared_tickers]).sum(axis=1)

    # NAV = cash + invested
    cash_series = cash.iloc[:, 0]
    nav = cash_series + invested

    # Returns from NAV time series
    daily_returns    = nav.pct_change().fillna(0)
    cumulative_return = (nav / nav.iloc[0]) - 1
    rolling_max      = nav.cummax()
    drawdown         = (nav - rolling_max) / rolling_max

    equity_curve = pd.DataFrame({
        'NAV':          nav,
        'Cash':         cash_series,
        'Invested':     invested,
        'Daily_Return': daily_returns,
        'Cumul_Return': cumulative_return,
        'Drawdown':     drawdown,
    })

    # Clean correlation matrix
    corr = corr_raw.copy()
    corr = corr.loc[~corr.index.isna()]
    corr = corr.drop(columns=[c for c in corr.columns if 'TICKER' in str(c)], errors='ignore')
    corr.index = corr.index.astype(str)
    corr = corr.apply(pd.to_numeric, errors='coerce')

    # Clean risk metrics
    risk = risk_raw.dropna(subset=[risk_raw.columns[0]])
    risk = risk[risk.iloc[:, 0].astype(str).str.strip() != 'METRIC']

    return equity_curve, ref, trades, corr, risk, market, units


# ─────────────────────────────────────────────
# LOAD DATA WITH ERROR HANDLING
# ─────────────────────────────────────────────
try:
    equity_curve, ref, trades, corr, risk, market, units = load_data(EXCEL_PATH)
except FileNotFoundError:
    st.error(f"File not found: {EXCEL_PATH}")
    st.info("Make sure Portfolio_BUILT_v2.xlsx exists at that path and try again.")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ─────────────────────────────────────────────
# DERIVED GLOBALS
# ─────────────────────────────────────────────
active         = ref[ref['Cur_Shares'] > 0].copy()
current_nav    = equity_curve['NAV'].iloc[-1]
total_return   = equity_curve['Cumul_Return'].iloc[-1]
max_drawdown   = equity_curve['Drawdown'].min()
daily_ret_std  = equity_curve['Daily_Return'].std()
ann_vol        = daily_ret_std * (252 ** 0.5)
ann_return_val = (1 + equity_curve['Daily_Return'].mean()) ** 252 - 1
sharpe         = (ann_return_val - 0.045) / ann_vol if ann_vol > 0 else 0
today_return   = equity_curve['Daily_Return'].iloc[-1]
start_date     = equity_curve.index[0]
end_date       = equity_curve.index[-1]

# Active-only correlation matrix
active_tickers = active['Ticker'].tolist()
corr_filtered  = corr.loc[
    [t for t in active_tickers if t in corr.index],
    [t for t in active_tickers if t in corr.columns],
]

# Terminal validation
print(f"[OK] Loaded {len(equity_curve)} trading days")
print(f"[OK] {len(active)} active positions: {active['Ticker'].tolist()}")
print(f"[OK] Correlation matrix: {corr_filtered.shape} (active only)")
print(f"[OK] Current NAV: ${current_nav:,.2f}")
print(f"[OK] Total Return: {total_return:.2%}")
print(f"[OK] Sharpe: {sharpe:.2f} | MaxDD: {max_drawdown:.2%}")

# ─────────────────────────────────────────────
# BENCHMARK FETCH
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
            data[t] = pd.Series(dtype=float)
    return pd.DataFrame(data)

benchmarks = fetch_benchmarks(start_date, end_date)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Portfolio Terminal")
    st.caption(f"Account  |  {end_date.strftime('%b %d, %Y')}")
    st.divider()

    page = st.radio("Navigate", [
        "Dashboard",
        "Positions",
        "Correlation",
        "Risk Metrics",
        "Benchmark Comparison",
        "Trade Log",
    ])

    st.divider()

    nav_color  = "normal"
    st.metric("NAV",          f"${current_nav:,.2f}")
    st.metric("Today",        f"{today_return:.2%}",  delta=f"{today_return:.2%}")
    st.metric("Total Return", f"{total_return:.2%}")
    st.metric("Max Drawdown", f"{max_drawdown:.2%}")

    st.divider()
    st.caption(f"Source: Portfolio_BUILT_v2.xlsx")
    st.caption(f"Last price date: {end_date.strftime('%Y-%m-%d')}")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ─────────────────────────────────────────────
# PAGE 1 — DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard():
    st.title("📊 Portfolio Dashboard")

    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Portfolio NAV",   f"${current_nav:,.2f}")
    c2.metric("Total Return",    f"{total_return:.2%}",              delta=f"{today_return:.2%}")
    c3.metric("Today's P&L",     f"${today_return * current_nav:,.2f}", delta=f"{today_return:.2%}")
    c4.metric("Sharpe Ratio",    f"{sharpe:.2f}")
    c5.metric("Max Drawdown",    f"{max_drawdown:.2%}")
    c6.metric("Ann. Volatility", f"{ann_vol:.2%}")

    st.write("")

    # Equity curve
    fig_nav = go.Figure()
    fig_nav.add_trace(go.Scatter(
        x=equity_curve.index,
        y=equity_curve['NAV'],
        name='NAV',
        line=dict(color='#4a9eff', width=2),
        fill='tozeroy',
        fillcolor='rgba(74,158,255,0.08)',
    ))
    fig_nav.update_layout(
        **CHART_THEME,
        title=f"Portfolio NAV — {start_date.strftime('%b %Y')} to Present",
        yaxis_title="NAV ($)",
        height=320,
    )
    st.plotly_chart(fig_nav, use_container_width=True)

    # Drawdown + Allocation
    col_left, col_right = st.columns([6, 4], gap="medium")

    with col_left:
        dd = equity_curve['Drawdown']
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=dd.index,
            y=dd * 100,
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='#ff3b30', width=1),
            fillcolor='rgba(255,59,48,0.18)',
        ))
        fig_dd.update_layout(
            **CHART_THEME,
            title="Drawdown from Peak (%)",
            yaxis_title="Drawdown (%)",
            height=280,
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with col_right:
        last_prices = market.iloc[-1]
        alloc_data  = []
        for _, row in active.iterrows():
            px_val = last_prices.get(row['Ticker'], 0)
            alloc_data.append({'Ticker': row['Ticker'], 'Value': row['Cur_Shares'] * px_val})
        alloc_df = pd.DataFrame(alloc_data)

        if not alloc_df.empty:
            fig_pie = px.pie(
                alloc_df, values='Value', names='Ticker',
                hole=0.4,
                color_discrete_sequence=['#4a9eff','#00c076','#ff9f0a','#ff3b30',
                                         '#bf5af2','#32d74b','#ffd60a','#ff6b6b',
                                         '#a8dadc','#e9c46a'],
                title="Current Allocation",
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e0e4ef', size=11),
                margin=dict(l=10, r=10, t=40, b=10),
                height=280,
                legend=dict(orientation='v', font=dict(size=10)),
            )
            st.plotly_chart(fig_pie, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 2 — POSITIONS
# ─────────────────────────────────────────────
def page_positions():
    st.title("📋 Active Positions")
    st.caption(f"{len(active)} positions  |  NAV ${current_nav:,.2f}")

    last_prices = market.iloc[-1]
    prev_prices = market.iloc[-2] if len(market) >= 2 else market.iloc[-1]

    rows = []
    for _, row in active.iterrows():
        ticker    = row['Ticker']
        shares    = row['Cur_Shares']
        avg_cost  = row['Avg_Cost']
        cur_px    = last_prices.get(ticker, 0)
        prev_px   = prev_prices.get(ticker, 0)
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

    # Sector exposure chart
    if 'Sector' in pos_df.columns and not pos_df['Sector'].isna().all():
        sector_df = pos_df.groupby('Sector')['Mkt Value'].sum().reset_index().sort_values('Mkt Value')
        fig_sector = px.bar(
            sector_df, x='Mkt Value', y='Sector', orientation='h',
            color_discrete_sequence=['#4a9eff'],
            title='Exposure by Sector',
        )
        fig_sector.update_layout(**CHART_THEME, xaxis_title='Market Value ($)', yaxis_title='', height=max(250, len(sector_df) * 40))
        st.plotly_chart(fig_sector, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 3 — CORRELATION
# ─────────────────────────────────────────────
def page_correlation():
    st.title("🔗 Correlation Matrix")
    st.caption("Based on daily returns  |  Green = low correlation (good diversification)  |  Red = high correlation (concentration risk)")

    if corr_filtered.empty:
        st.warning("No correlation data available for active positions.")
        return

    fig = go.Figure(go.Heatmap(
        z=corr_filtered.values,
        x=corr_filtered.columns.tolist(),
        y=corr_filtered.index.tolist(),
        colorscale=[
            [0.0, '#63BE7B'],
            [0.5, '#FFEB84'],
            [1.0, '#F8696B'],
        ],
        zmid=0, zmin=-1, zmax=1,
        text=corr_filtered.round(2).values,
        texttemplate='%{text}',
        textfont=dict(size=10),
        showscale=True,
    ))
    fig.update_layout(
        **CHART_THEME,
        title='Daily Return Correlations (Active Positions Only)',
        height=500,
        xaxis=dict(side='bottom', gridcolor='#1c2541'),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Interpretation callouts
    st.markdown('<div class="section-title">Notable Correlations</div>', unsafe_allow_html=True)

    # Extract upper triangle pairs (exclude self-correlation)
    pairs = []
    tickers_list = corr_filtered.columns.tolist()
    for i in range(len(tickers_list)):
        for j in range(i + 1, len(tickers_list)):
            val = corr_filtered.iloc[i, j]
            if pd.notna(val):
                pairs.append((tickers_list[i], tickers_list[j], val))

    pairs.sort(key=lambda x: x[2])

    col_low, col_high = st.columns(2)

    with col_high:
        st.markdown("**⚠️ Highest Correlations (concentration risk)**")
        for t1, t2, v in sorted(pairs, key=lambda x: x[2], reverse=True)[:3]:
            st.info(f"**{t1} / {t2}**: {v:.2f} — High correlation, concentrated risk")

    with col_low:
        st.markdown("**✅ Lowest Correlations (diversification)**")
        for t1, t2, v in pairs[:3]:
            st.success(f"**{t1} / {t2}**: {v:.2f} — Good diversifier")


# ─────────────────────────────────────────────
# PAGE 4 — RISK METRICS
# ─────────────────────────────────────────────
def page_risk():
    st.title("⚠️ Risk Analytics")
    st.caption(f"Based on {len(equity_curve)} trading days  |  RF Rate: 4.50%")

    daily_returns = equity_curve['Daily_Return'].dropna()
    rf_daily      = 0.045 / 252
    nav_series    = equity_curve['NAV']

    ann_ret  = (1 + daily_returns.mean()) ** 252 - 1
    _ann_vol = daily_returns.std() * (252 ** 0.5)
    _sharpe  = (ann_ret - 0.045) / _ann_vol if _ann_vol > 0 else 0

    downside = daily_returns[daily_returns < rf_daily]
    down_vol = downside.std() * (252 ** 0.5) if len(downside) > 0 else 1
    sortino  = (ann_ret - 0.045) / down_vol if down_vol > 0 else 0

    _max_dd  = ((nav_series / nav_series.cummax()) - 1).min()
    var_95   = daily_returns.quantile(0.05)
    var_99   = daily_returns.quantile(0.01)
    cvar_95  = daily_returns[daily_returns <= var_95].mean()

    # Beta to VOO
    beta = None
    if 'VOO' in market.columns:
        voo_ret = market['VOO'].pct_change().dropna()
        aligned = daily_returns.align(voo_ret, join='inner')
        p_ret, v_ret = aligned[0], aligned[1]
        if len(p_ret) > 5:
            beta = np.cov(p_ret, v_ret)[0][1] / np.var(v_ret)
    elif not benchmarks.empty and 'VOO' in benchmarks.columns:
        voo_ret = benchmarks['VOO'].pct_change().dropna()
        aligned = daily_returns.align(voo_ret, join='inner')
        p_ret, v_ret = aligned[0], aligned[1]
        if len(p_ret) > 5:
            beta = np.cov(p_ret, v_ret)[0][1] / np.var(v_ret)

    # KPI grid
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Annualized Return",  f"{ann_ret:.2%}")
        st.metric("Sharpe Ratio",       f"{_sharpe:.2f}")
        st.metric("Beta to VOO",        f"{beta:.2f}" if beta is not None else "N/A")
    with c2:
        st.metric("Annualized Vol",     f"{_ann_vol:.2%}")
        st.metric("Sortino Ratio",      f"{sortino:.2f}")
        st.metric("Max Drawdown",       f"{_max_dd:.2%}")
    with c3:
        st.metric("VaR 95% (Daily)",    f"{var_95:.2%}")
        st.metric("VaR 99% (Daily)",    f"{var_99:.2%}")
        st.metric("CVaR 95% (Daily)",   f"{cvar_95:.2%}")

    st.write("")

    # Return distribution histogram
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=daily_returns * 100,
        nbinsx=50,
        marker_color='#4a9eff',
        opacity=0.7,
        name='Daily Returns',
    ))
    fig_hist.add_vline(x=var_95 * 100, line_dash='dash', line_color='#ff9f0a',
                       annotation_text=f'VaR 95%: {var_95:.2%}',
                       annotation_font_color='#ff9f0a')
    fig_hist.add_vline(x=var_99 * 100, line_dash='dash', line_color='#ff3b30',
                       annotation_text=f'VaR 99%: {var_99:.2%}',
                       annotation_font_color='#ff3b30')
    fig_hist.update_layout(
        **CHART_THEME,
        title='Daily Return Distribution',
        xaxis_title='Return (%)',
        yaxis_title='Frequency',
        height=320,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Dollar impact table
    st.markdown('<div class="section-title">Dollar Impact at Current NAV</div>', unsafe_allow_html=True)
    impact_data = {
        'Metric':        ['VaR 95%',             'VaR 99%',             'CVaR 95%',             'Max Drawdown'],
        'Daily Impact':  [f"${var_95  * current_nav:,.2f}",
                          f"${var_99  * current_nav:,.2f}",
                          f"${cvar_95 * current_nav:,.2f}",
                          f"${_max_dd * current_nav:,.2f}"],
        'Annual Impact': [f"${var_95  * current_nav * 252:,.2f}",
                          f"${var_99  * current_nav * 252:,.2f}",
                          f"${cvar_95 * current_nav * 252:,.2f}",
                          "—"],
    }
    st.dataframe(pd.DataFrame(impact_data), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# PAGE 5 — BENCHMARK COMPARISON
# ─────────────────────────────────────────────
def page_benchmark():
    st.title("📈 Performance vs Benchmarks")
    st.caption("Rolling returns: Portfolio vs VOO (S&P 500) vs QQQ (Nasdaq 100)")

    nav_series = equity_curve['NAV']

    def period_return(series, n_days):
        s = series.dropna()
        if len(s) < n_days + 1:
            return None
        return float((s.iloc[-1] / s.iloc[-n_days - 1]) - 1)

    ytd_start = datetime(datetime.now().year, 1, 1)
    ytd_days  = max(len(nav_series[nav_series.index >= pd.Timestamp(ytd_start)]) - 1, 1)

    periods = [('1D', 1), ('1W', 5), ('1M', 21), ('3M', 63), ('YTD', ytd_days), ('1Y', 252)]

    perf_rows = []
    for label, n in periods:
        row = {'Period': label, 'Portfolio': period_return(nav_series, n)}
        for bm in ['VOO', 'QQQ']:
            if not benchmarks.empty and bm in benchmarks.columns:
                row[bm] = period_return(benchmarks[bm], n)
            else:
                row[bm] = None
        perf_rows.append(row)

    perf_df = pd.DataFrame(perf_rows)

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        color = '#00c076' if v >= 0 else '#ff3b30'
        return f'<span style="color:{color};font-weight:600">{v:.2%}</span>'

    # Render as HTML table for color coding
    html_rows = ""
    for _, r in perf_df.iterrows():
        html_rows += f"<tr><td><b>{r['Period']}</b></td>"
        html_rows += f"<td>{fmt_pct(r['Portfolio'])}</td>"
        html_rows += f"<td>{fmt_pct(r.get('VOO'))}</td>"
        html_rows += f"<td>{fmt_pct(r.get('QQQ'))}</td></tr>"

    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <thead>
        <tr style="background:#1c2541;color:white">
          <th style="padding:8px;text-align:left">Period</th>
          <th style="padding:8px">Portfolio</th>
          <th style="padding:8px">VOO (S&P 500)</th>
          <th style="padding:8px">QQQ (Nasdaq)</th>
        </tr>
      </thead>
      <tbody>{html_rows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.write("")

    # Normalized chart rebased to 100
    port_rebased = (nav_series / nav_series.iloc[0]) * 100

    fig_bm = go.Figure()
    fig_bm.add_trace(go.Scatter(
        x=port_rebased.index, y=port_rebased,
        name='Portfolio', line=dict(color='#4a9eff', width=2),
    ))

    if not benchmarks.empty:
        for bm, color, label in [('VOO', '#00c076', 'VOO (S&P 500)'), ('QQQ', '#ff9f0a', 'QQQ (Nasdaq)')]:
            if bm in benchmarks.columns:
                bm_s = benchmarks[bm].dropna()
                if not bm_s.empty:
                    bm_rebased = (bm_s / bm_s.iloc[0]) * 100
                    fig_bm.add_trace(go.Scatter(
                        x=bm_rebased.index, y=bm_rebased,
                        name=label, line=dict(color=color, width=1.5, dash='dot'),
                    ))

    fig_bm.update_layout(
        **CHART_THEME,
        title='Normalized Performance (Base = 100)',
        yaxis_title='Value (Base 100)',
        xaxis_title='Date',
        height=400,
    )
    st.plotly_chart(fig_bm, use_container_width=True)

    # Alpha callouts
    port_total = float((nav_series.iloc[-1] / nav_series.iloc[0]) - 1)
    st.markdown('<div class="section-title">Alpha vs Benchmarks</div>', unsafe_allow_html=True)
    ac1, ac2, ac3 = st.columns(3)

    for col, bm, label in [(ac1, 'VOO', 'Alpha vs S&P 500'), (ac2, 'QQQ', 'Alpha vs Nasdaq')]:
        if not benchmarks.empty and bm in benchmarks.columns:
            bm_s = benchmarks[bm].dropna()
            bm_total = float((bm_s.iloc[-1] / bm_s.iloc[0]) - 1) if len(bm_s) > 1 else 0
            alpha = port_total - bm_total
            col.metric(label, f"{alpha:+.2%}", delta=f"Port: {port_total:.2%} | {bm}: {bm_total:.2%}")
        else:
            col.metric(label, "N/A")

    with ac3:
        if not benchmarks.empty and 'VOO' in benchmarks.columns:
            voo_ret = benchmarks['VOO'].pct_change().dropna()
            daily_r = equity_curve['Daily_Return']
            aligned = daily_r.align(voo_ret, join='inner')
            if len(aligned[0]) > 5:
                corr_val = aligned[0].corr(aligned[1])
                ac3.metric("Correlation to VOO", f"{corr_val:.2f}")
            else:
                ac3.metric("Correlation to VOO", "N/A")
        else:
            ac3.metric("Correlation to VOO", "N/A")


# ─────────────────────────────────────────────
# PAGE 6 — TRADE LOG
# ─────────────────────────────────────────────
def page_trade_log():
    st.title("📝 Trade History")
    st.caption(f"{len(trades)} transactions  |  {start_date.strftime('%b %d, %Y')} to Present")

    buys        = trades[trades['Action'].str.upper() == 'BUY']  if 'Action' in trades.columns else pd.DataFrame()
    sells       = trades[trades['Action'].str.upper() == 'SELL'] if 'Action' in trades.columns else pd.DataFrame()
    total_inv   = buys['Amount'].abs().sum()  if not buys.empty  and 'Amount' in buys.columns  else 0
    total_proc  = sells['Amount'].sum()       if not sells.empty and 'Amount' in sells.columns else 0

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Total Buys",       len(buys))
    sc2.metric("Total Sells",      len(sells))
    sc3.metric("Total Invested",   f"${total_inv:,.2f}")
    sc4.metric("Total Proceeds",   f"${total_proc:,.2f}")
    sc5.metric("Net Cash Deployed",f"${total_inv - total_proc:,.2f}")

    st.write("")

    # Filter
    if 'Symbol' in trades.columns:
        ticker_filter = st.multiselect(
            "Filter by ticker",
            options=sorted(trades['Symbol'].dropna().unique()),
        )
        display_trades = trades[trades['Symbol'].isin(ticker_filter)] if ticker_filter else trades
    else:
        display_trades = trades

    display_trades = display_trades.sort_values('Date', ascending=False) if 'Date' in display_trades.columns else display_trades

    col_config = {}
    if 'Amount' in display_trades.columns:
        col_config['Amount'] = st.column_config.NumberColumn('Amount', format='$%,.2f')
    if 'Price' in display_trades.columns:
        col_config['Price'] = st.column_config.NumberColumn('Price', format='$%.4f')

    st.dataframe(display_trades, use_container_width=True, hide_index=True, column_config=col_config)


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
elif page == "Benchmark Comparison":
    page_benchmark()
elif page == "Trade Log":
    page_trade_log()
