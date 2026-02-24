import os
import django
import pandas as pd

# --------------------------
# Setup Django environment
# --------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradingfx.settings")
django.setup()

from trade.models import Trades, Pairs

# --------------------------
# Configuration
# --------------------------
excel_file = "trades.xlsx"  # Path to your Excel file

# Read Excel file
df = pd.read_excel(excel_file)
df = df.where(pd.notnull(df), None)  # Replace NaN with None

# --------------------------
# Step 1: Preload existing pairs (normalize names)
# --------------------------
existing_pairs = {pair.name.strip().upper(): pair for pair in Pairs.objects.all() if pair.name}

# --------------------------
# Step 2: Find unique pairs in Excel
# --------------------------
excel_pairs = set(str(name).strip().upper() for name in df['PAIR'].dropna())
pairs_to_create = [Pairs(name=name) for name in excel_pairs if name not in existing_pairs]

# Bulk create missing pairs
if pairs_to_create:
    Pairs.objects.bulk_create(pairs_to_create)
    # Refresh the existing_pairs dict
    for pair in Pairs.objects.filter(name__in=[p.name for p in pairs_to_create]):
        existing_pairs[pair.name.strip().upper()] = pair

# --------------------------
# Step 3: Create Trades objects
# --------------------------
trades_list = []

for _, row in df.iterrows():
    # Clean the pair name from Excel
    pair_name = row.get("PAIR")
    pair_obj = None
    if pair_name:
        pair_name_clean = str(pair_name).strip().upper()
        pair_obj = existing_pairs.get(pair_name_clean)
        if not pair_obj:
            # Safety fallback
            pair_obj = Pairs.objects.create(name=pair_name_clean)
            existing_pairs[pair_name_clean] = pair_obj

    trade = Trades(
        pair=pair_obj,  # MUST be a Pairs instance
        momentum_h4=row.get("H4 MOMENTUM"),
        momentum_h1=row.get("H1 MOMENTUM"),
        momentum_15m=row.get("15M MOMENTUM"),
        momentum_5m=row.get("5M MOMENTUM"),
        momentum_1m=row.get("1M MOMENTUM"),
        session=row.get("SESSION"),
        entry_place=row.get("ENTRY PLACE"),
        buy_or_sell=row.get("BUY/SELL"),
        setup_quality=row.get("SETUP QUALITY"),
        trade_type=row.get("TRADE TYPE"),
        confirmation=row.get("CONFIRMATION"),
        mood=row.get("MOOD"),
        tp=row.get("TP"),
        tp_reason=row.get("TP REASON"),
        risk_reward=row.get("RISK REWARD"),
        rvs=row.get("RVS"),
        rvs_grade=row.get("RVS GRADE"),
        target=row.get("target"),
        reason=row.get("REASON"),
        holding_time_hrs=row.get("HOLDING TIME (H)"),
        holding_time_mns=row.get("HOLDING TIME (M)"),
        narration=row.get("NARRATION"),
        timestamp=row.get("TRADE DATE TIME")
    )
    trades_list.append(trade)

# --------------------------
# Step 4: Bulk insert trades
# --------------------------
if trades_list:
    Trades.objects.bulk_create(trades_list)
    print(f"{len(trades_list)} trades imported successfully!")
else:
    print("No trades to import.")
