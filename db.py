"""
db.py — All database connection and query functions for Portfolio Terminal.
Connects to Supabase PostgreSQL via SQLAlchemy using st.secrets.
"""
import pandas as pd
import numpy as np
from collections import deque
from datetime import date, datetime, timedelta

import streamlit as st
from sqlalchemy import create_engine, text
import yfinance as yf


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
@st.cache_resource
def get_connection():
    url = st.secrets["connections"]["postgresql"]["url"]
    engine = create_engine(url, pool_pre_ping=True)
    return engine


# ─────────────────────────────────────────────
# READ FUNCTIONS
# ─────────────────────────────────────────────
def get_all_trades(conn):
    with conn.connect() as c:
        df = pd.read_sql(
            "SELECT * FROM trades ORDER BY date ASC, id ASC",
            c, parse_dates=['date', 'settlement', 'created_at'],
        )
    return df


def get_cash_flows(conn):
    with conn.connect() as c:
        df = pd.read_sql(
            "SELECT * FROM cash_flows ORDER BY date ASC, id ASC",
            c, parse_dates=['date', 'created_at'],
        )
    return df


def get_price_history(conn, tickers=None, start=None, end=None):
    """
    Fetch from price_cache. If tickers is None, fetch all.
    Returns long-format DataFrame: [ticker, date, close_price]
    """
    clauses = []
    params  = {}
    if tickers:
        clauses.append("ticker = ANY(:tickers)")
        params['tickers'] = list(tickers)
    if start:
        clauses.append("date >= :start")
        params['start'] = start
    if end:
        clauses.append("date <= :end")
        params['end'] = end

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql   = f"SELECT ticker, date, close_price FROM price_cache {where} ORDER BY ticker, date ASC"

    with conn.connect() as c:
        df = pd.read_sql(text(sql), c, params=params, parse_dates=['date'])
    return df


def get_ticker_info(conn):
    with conn.connect() as c:
        df = pd.read_sql("SELECT * FROM ticker_info ORDER BY ticker", c)
    return df


# ─────────────────────────────────────────────
# WRITE FUNCTIONS
# ─────────────────────────────────────────────
def insert_trade(conn, trade_dict):
    """
    trade_dict keys: date, settlement, ticker, action, quantity, price, amount
    """
    sql = text("""
        INSERT INTO trades (date, settlement, ticker, action, quantity, price, amount)
        VALUES (:date, :settlement, :ticker, :action, :quantity, :price, :amount)
    """)
    with conn.connect() as c:
        c.execute(sql, trade_dict)
        c.commit()


def insert_cash_flow(conn, cf_dict):
    """
    cf_dict keys: date, amount, description
    """
    sql = text("""
        INSERT INTO cash_flows (date, amount, description)
        VALUES (:date, :amount, :description)
    """)
    with conn.connect() as c:
        c.execute(sql, cf_dict)
        c.commit()


def upsert_prices(conn, prices_df):
    """
    prices_df columns: [ticker, date, close_price]
    Inserts or updates price_cache via ON CONFLICT upsert.
    """
    if prices_df.empty:
        return
    records = prices_df[['ticker', 'date', 'close_price']].to_dict('records')
    sql = text("""
        INSERT INTO price_cache (ticker, date, close_price, updated_at)
        VALUES (:ticker, :date, :close_price, NOW())
        ON CONFLICT (ticker, date) DO UPDATE SET
            close_price = EXCLUDED.close_price,
            updated_at  = NOW()
    """)
    with conn.connect() as c:
        c.executemany(sql, records)
        c.commit()


def upsert_ticker_info(conn, info_list):
    """
    info_list: list of dicts with keys [ticker, company, sector]
    """
    if not info_list:
        return
    sql = text("""
        INSERT INTO ticker_info (ticker, company, sector, updated_at)
        VALUES (:ticker, :company, :sector, NOW())
        ON CONFLICT (ticker) DO UPDATE SET
            company    = EXCLUDED.company,
            sector     = EXCLUDED.sector,
            updated_at = NOW()
    """)
    with conn.connect() as c:
        c.executemany(sql, info_list)
        c.commit()


# ─────────────────────────────────────────────
# POSITION ANALYTICS
# ─────────────────────────────────────────────
def compute_positions(trades_df):
    """
    FIFO computation of current shares and average cost per ticker.
    Returns DataFrame with columns: [Ticker, Cur_Shares, Avg_Cost]
    """
    if trades_df.empty:
        return pd.DataFrame(columns=['Ticker', 'Cur_Shares', 'Avg_Cost'])

    positions = {}
    for ticker in trades_df['ticker'].unique():
        t = (
            trades_df[trades_df['ticker'] == ticker]
            .sort_values(['date', 'id'])
        )
        buy_queue = deque()  # items: [remaining_qty, buy_price]

        for _, row in t.iterrows():
            action = str(row['action']).upper()
            qty    = float(row['quantity'])
            price  = float(row['price'])

            if action == 'BUY':
                buy_queue.append([qty, price])
            elif action == 'SELL':
                remaining = qty
                while remaining > 1e-9 and buy_queue:
                    if buy_queue[0][0] <= remaining + 1e-9:
                        remaining -= buy_queue[0][0]
                        buy_queue.popleft()
                    else:
                        buy_queue[0][0] -= remaining
                        remaining = 0

        total_qty  = sum(b[0] for b in buy_queue)
        total_cost = sum(b[0] * b[1] for b in buy_queue)
        avg_cost   = total_cost / total_qty if total_qty > 1e-9 else 0.0

        if total_qty > 1e-9:
            positions[ticker] = {
                'Ticker':    ticker,
                'Cur_Shares': round(total_qty, 6),
                'Avg_Cost':   round(avg_cost, 4),
            }

    if not positions:
        return pd.DataFrame(columns=['Ticker', 'Cur_Shares', 'Avg_Cost'])

    return pd.DataFrame(positions.values())


def compute_equity_curve(trades_df, cash_flows_df, prices_df):
    """
    Builds daily NAV series from trades, external cash flows, and price_cache.
    Returns DataFrame indexed by date:
      columns = [NAV, Cash, Invested, Daily_Return, Cumul_Return, Drawdown]
    """
    if prices_df.empty:
        return pd.DataFrame()

    # Wide price matrix: index=date, columns=ticker
    prices_wide = prices_df.pivot(index='date', columns='ticker', values='close_price')
    prices_wide.index = pd.to_datetime(prices_wide.index)
    prices_wide = prices_wide.sort_index()
    all_tickers = prices_wide.columns.tolist()
    dates       = prices_wide.index

    # ── Daily signed quantity per ticker ────────────────────────────────────
    if not trades_df.empty:
        tdf = trades_df.copy()
        tdf['date'] = pd.to_datetime(tdf['date'])
        tdf['qty_signed'] = tdf.apply(
            lambda r: float(r['quantity']) if str(r['action']).upper() == 'BUY'
                      else -float(r['quantity']), axis=1
        )
        # Sum signed qty by (date, ticker), reindex to all dates × all tickers
        daily_qty = (
            tdf.groupby(['date', 'ticker'])['qty_signed']
            .sum()
            .unstack(fill_value=0)
            .reindex(index=dates, columns=all_tickers, fill_value=0)
        )
        daily_shares = daily_qty.cumsum().clip(lower=0)

        # Cumulative trade cash impact
        trade_cash = (
            tdf.groupby('date')['amount']
            .sum()
            .reindex(dates, fill_value=0)
            .cumsum()
        )
    else:
        daily_shares = pd.DataFrame(0.0, index=dates, columns=all_tickers)
        trade_cash   = pd.Series(0.0, index=dates)

    # ── External cash flows ──────────────────────────────────────────────────
    if not cash_flows_df.empty:
        cdf = cash_flows_df.copy()
        cdf['date'] = pd.to_datetime(cdf['date'])
        ext_cash = (
            cdf.groupby('date')['amount']
            .sum()
            .reindex(dates, fill_value=0)
            .cumsum()
        )
    else:
        ext_cash = pd.Series(0.0, index=dates)

    cash_s   = ext_cash + trade_cash
    invested = (daily_shares * prices_wide).fillna(0).sum(axis=1)
    nav      = cash_s + invested

    # Trim to first date where NAV > 0
    valid = nav[nav > 0]
    if valid.empty:
        return pd.DataFrame()
    first = valid.index[0]
    nav      = nav.loc[first:]
    cash_s   = cash_s.loc[first:]
    invested = invested.loc[first:]

    daily_ret = nav.pct_change().fillna(0)
    cumul_ret = (nav / nav.iloc[0]) - 1
    drawdown  = (nav / nav.cummax()) - 1

    return pd.DataFrame({
        'NAV':          nav,
        'Cash':         cash_s,
        'Invested':     invested,
        'Daily_Return': daily_ret,
        'Cumul_Return': cumul_ret,
        'Drawdown':     drawdown,
    })


# ─────────────────────────────────────────────
# EOD PRICE REFRESH
# ─────────────────────────────────────────────
def refresh_eod_prices(conn, tickers):
    """
    Fetch EOD prices from yfinance for the given tickers and upsert to price_cache.
    Skips fetching today's close if market has not yet closed (before 4:30pm ET).
    """
    if not tickers:
        return

    today = date.today()

    # Determine if we should include today's close
    try:
        import pytz
        et      = pytz.timezone('America/New_York')
        now_et  = datetime.now(et)
        # Market closed = weekday AND after 4:30pm ET
        include_today = not (now_et.weekday() < 5 and now_et.hour < 16 or
                             (now_et.hour == 16 and now_et.minute < 30))
    except Exception:
        include_today = True

    # Check which tickers need today's price
    if include_today:
        sql = text(
            "SELECT ticker FROM price_cache WHERE date = :today AND ticker = ANY(:tickers)"
        )
        with conn.connect() as c:
            result = c.execute(sql, {'today': today, 'tickers': list(tickers)})
            cached = {row[0] for row in result}
        missing = [t for t in tickers if t not in cached]
    else:
        missing = list(tickers)

    if not missing:
        return

    fetch_end   = today.strftime('%Y-%m-%d') if include_today else (today - timedelta(days=1)).strftime('%Y-%m-%d')
    fetch_start = (today - timedelta(days=7)).strftime('%Y-%m-%d')

    rows = []
    for ticker in missing:
        try:
            df = yf.download(ticker, start=fetch_start, end=fetch_end,
                             auto_adjust=True, progress=False)
            if df.empty:
                continue
            close = df['Close'].squeeze()
            if isinstance(close, pd.Series):
                for d, p in close.items():
                    if not pd.isna(p):
                        rows.append({'ticker': ticker, 'date': d.date() if hasattr(d, 'date') else d,
                                     'close_price': float(p)})
            else:
                rows.append({'ticker': ticker,
                             'date': close.index[0].date(),
                             'close_price': float(close.iloc[0])})
        except Exception:
            pass

    if rows:
        upsert_prices(conn, pd.DataFrame(rows))
