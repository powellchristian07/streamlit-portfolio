"""
migrate_excel.py — One-time migration from Portfolio_BUILT_v2.xlsx to Supabase.

Run once locally:
    python migrate_excel.py

Requires .streamlit/secrets.toml with Supabase connection string.
"""
import sys
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# CONFIG — edit if needed
# ─────────────────────────────────────────────
EXCEL_PATH = r"C:\Users\powel\OneDrive\Documents\Portfolio_BUILT_v2.xlsx"

# Read Supabase URL from secrets.toml directly (no Streamlit runtime needed)
import tomllib, pathlib

secrets_path = pathlib.Path(".streamlit/secrets.toml")
if not secrets_path.exists():
    print("ERROR: .streamlit/secrets.toml not found. Create it first.")
    sys.exit(1)

with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

DB_URL = secrets["connections"]["postgresql"]["url"]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def safe_date(val):
    """Convert various date formats to Python date, or None."""
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, date)):
        return pd.Timestamp(val).date()
    return None


def safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if not np.isnan(v) else default
    except Exception:
        return default


# ─────────────────────────────────────────────
# CONNECT
# ─────────────────────────────────────────────
print(f"Connecting to database...")
engine = create_engine(DB_URL, pool_pre_ping=True)

# ─────────────────────────────────────────────
# READ EXCEL
# ─────────────────────────────────────────────
print(f"Reading {EXCEL_PATH} ...")
xl = pd.ExcelFile(EXCEL_PATH)
print(f"  Sheets found: {xl.sheet_names}")

market  = pd.read_excel(EXCEL_PATH, sheet_name='Market_Data',    index_col=0, parse_dates=True)
units   = pd.read_excel(EXCEL_PATH, sheet_name='Daily_Units',    index_col=0, parse_dates=True)
cash    = pd.read_excel(EXCEL_PATH, sheet_name='Daily_Cash',     index_col=0, parse_dates=True)
ref     = pd.read_excel(EXCEL_PATH, sheet_name='Reference_Data')
trades  = pd.read_excel(EXCEL_PATH, sheet_name='Trade_Log',      parse_dates=['Date', 'Settlement'])

print(f"  Market_Data  : {market.shape}  ({market.index[0].date()} → {market.index[-1].date()})")
print(f"  Daily_Units  : {units.shape}")
print(f"  Daily_Cash   : {cash.shape}")
print(f"  Reference_Data: {ref.shape}")
print(f"  Trade_Log    : {trades.shape}")


# ─────────────────────────────────────────────
# 1. MIGRATE TRADES
# ─────────────────────────────────────────────
print("\n[1/4] Migrating trades...")

# Detect column names (flexible mapping)
col_map = {}
for col in trades.columns:
    c = col.strip().lower()
    if c in ('date', 'trade date', 'tradedate'):
        col_map['date'] = col
    elif c in ('settlement', 'settle', 'settlement date'):
        col_map['settlement'] = col
    elif c in ('symbol', 'ticker', 'stock'):
        col_map['ticker'] = col
    elif c in ('action', 'type', 'buy/sell', 'transaction'):
        col_map['action'] = col
    elif c in ('quantity', 'qty', 'shares'):
        col_map['quantity'] = col
    elif c in ('price', 'execution price', 'fill price'):
        col_map['price'] = col
    elif c in ('amount', 'net amount', 'value', 'total'):
        col_map['amount'] = col

print(f"  Column mapping: {col_map}")

trade_rows = []
for _, row in trades.iterrows():
    trade_date   = safe_date(row.get(col_map.get('date')))
    settlement   = safe_date(row.get(col_map.get('settlement')))
    ticker       = str(row.get(col_map.get('ticker', ''), '')).strip().upper()
    action       = str(row.get(col_map.get('action', ''), '')).strip().upper()
    quantity     = abs(safe_float(row.get(col_map.get('quantity', 0))))
    price        = abs(safe_float(row.get(col_map.get('price', 0))))
    amount       = safe_float(row.get(col_map.get('amount', 0)))

    if not trade_date or not ticker or action not in ('BUY', 'SELL'):
        continue
    if quantity == 0 or price == 0:
        continue

    trade_rows.append({
        'date':       trade_date,
        'settlement': settlement,
        'ticker':     ticker,
        'action':     action,
        'quantity':   quantity,
        'price':      price,
        'amount':     amount,
    })

print(f"  Inserting {len(trade_rows)} trades...")
sql_trade = text("""
    INSERT INTO trades (date, settlement, ticker, action, quantity, price, amount)
    VALUES (:date, :settlement, :ticker, :action, :quantity, :price, :amount)
    ON CONFLICT DO NOTHING
""")
with engine.connect() as c:
    c.executemany(sql_trade, trade_rows)
    c.commit()
print(f"  Done.")


# ─────────────────────────────────────────────
# 2. MIGRATE CASH FLOWS
# ─────────────────────────────────────────────
print("\n[2/4] Deriving cash_flows from Daily_Cash...")

# Daily_Cash has daily total cash balance.
# External cash flows = daily change in cash balance MINUS trade cash impact on that day.
# trades 'amount' column: negative=buy (cash out), positive=sell (cash in).

cash_series   = cash.iloc[:, 0].sort_index()
common_dates  = cash_series.index.intersection(market.index).intersection(units.index)
cash_series   = cash_series.loc[common_dates]

# Day 0: treat the entire first-day balance as an initial deposit
cf_rows = [{
    'date':        cash_series.index[0].date(),
    'amount':      round(float(cash_series.iloc[0]), 2),
    'description': 'Opening balance (migrated from Excel)',
}]

# Build daily trade cash impact series
if not trades.empty and col_map.get('date') and col_map.get('amount'):
    trades_dated = trades.copy()
    trades_dated.index = pd.to_datetime(trades_dated[col_map['date']])
    trade_daily_cash = (
        trades_dated[col_map['amount']]
        .apply(safe_float)
        .groupby(trades_dated.index.date)
        .sum()
    )
    trade_daily_cash.index = pd.to_datetime(trade_daily_cash.index)
else:
    trade_daily_cash = pd.Series(dtype=float)

for i in range(1, len(cash_series)):
    d     = cash_series.index[i]
    prev  = cash_series.index[i - 1]
    delta = float(cash_series.iloc[i]) - float(cash_series.iloc[i - 1])
    tc    = float(trade_daily_cash.get(d, 0.0))
    ext   = delta - tc  # external deposit/withdrawal
    if abs(ext) > 0.01:
        cf_rows.append({
            'date':        d.date(),
            'amount':      round(ext, 2),
            'description': 'Migrated from Excel Daily_Cash',
        })

print(f"  Inserting {len(cf_rows)} cash flow records...")
sql_cf = text("""
    INSERT INTO cash_flows (date, amount, description)
    VALUES (:date, :amount, :description)
    ON CONFLICT DO NOTHING
""")
with engine.connect() as c:
    c.executemany(sql_cf, cf_rows)
    c.commit()
print(f"  Done.")


# ─────────────────────────────────────────────
# 3. MIGRATE PRICE CACHE
# ─────────────────────────────────────────────
print("\n[3/4] Migrating price_cache from Market_Data...")

price_rows = []
for ticker in market.columns:
    series = market[ticker].dropna()
    for d, p in series.items():
        price_rows.append({
            'ticker':      str(ticker).strip().upper(),
            'date':        d.date() if hasattr(d, 'date') else d,
            'close_price': round(float(p), 4),
        })

print(f"  Inserting {len(price_rows):,} price records...")

# Batch insert in chunks to avoid parameter limits
batch_size = 500
sql_price = text("""
    INSERT INTO price_cache (ticker, date, close_price, updated_at)
    VALUES (:ticker, :date, :close_price, NOW())
    ON CONFLICT (ticker, date) DO UPDATE SET
        close_price = EXCLUDED.close_price,
        updated_at  = NOW()
""")
with engine.connect() as c:
    for i in range(0, len(price_rows), batch_size):
        batch = price_rows[i:i + batch_size]
        c.executemany(sql_price, batch)
    c.commit()
print(f"  Done.")


# ─────────────────────────────────────────────
# 4. MIGRATE TICKER INFO
# ─────────────────────────────────────────────
print("\n[4/4] Migrating ticker_info from Reference_Data...")

info_rows = []
if not ref.empty:
    ref_cols = {c.strip().lower(): c for c in ref.columns}

    def find_col(candidates):
        for cand in candidates:
            if cand in ref_cols:
                return ref_cols[cand]
        return None

    ticker_col  = find_col(['ticker', 'symbol', 'stock'])
    company_col = find_col(['company', 'name', 'company name', 'longname'])
    sector_col  = find_col(['sector', 'industry'])

    if ticker_col:
        for _, row in ref.iterrows():
            ticker = str(row[ticker_col]).strip().upper()
            if not ticker or ticker == 'NAN':
                continue
            info_rows.append({
                'ticker':  ticker,
                'company': str(row[company_col]).strip() if company_col else '',
                'sector':  str(row[sector_col]).strip()  if sector_col  else '',
            })

print(f"  Inserting {len(info_rows)} ticker info records...")
sql_info = text("""
    INSERT INTO ticker_info (ticker, company, sector, updated_at)
    VALUES (:ticker, :company, :sector, NOW())
    ON CONFLICT (ticker) DO UPDATE SET
        company    = EXCLUDED.company,
        sector     = EXCLUDED.sector,
        updated_at = NOW()
""")
with engine.connect() as c:
    c.executemany(sql_info, info_rows)
    c.commit()
print(f"  Done.")


# ─────────────────────────────────────────────
# VERIFICATION
# ─────────────────────────────────────────────
print("\n── Verification ──────────────────────────")
with engine.connect() as c:
    n_trades    = c.execute(text("SELECT COUNT(*) FROM trades")).scalar()
    n_cf        = c.execute(text("SELECT COUNT(*) FROM cash_flows")).scalar()
    n_prices    = c.execute(text("SELECT COUNT(*) FROM price_cache")).scalar()
    n_tickers   = c.execute(text("SELECT COUNT(*) FROM ticker_info")).scalar()

print(f"  trades     : {n_trades:,} rows  (Excel had {len(trade_rows)})")
print(f"  cash_flows : {n_cf:,} rows")
print(f"  price_cache: {n_prices:,} rows")
print(f"  ticker_info: {n_tickers} rows")
print("\nMigration complete.")
