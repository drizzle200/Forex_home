import os
import django
import pandas as pd
from datetime import datetime

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tradingfx.settings")
django.setup()

from trade.models import Trades  # your model

# Path to your Excel file
excel_file = "trades.xlsx"  # <-- your Excel file

# Read the Excel file
df = pd.read_excel(excel_file)  # automatically handles Excel formats

# Optional: replace NaN with None
df = df.where(pd.notnull(df), None)

# Create a list of Trades objects
trades_list = []
for _, row in df.iterrows():
    trade = Trades(
        trade_id=row.get("ID"),
        pair=row.get("PAIR"),
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
        timestamp=row.get("TRADE DATE TIME")  # make sure Excel datetime is correct
    )
    trades_list.append(trade)

# Bulk create all trades in DB
Trades.objects.bulk_create(trades_list)
print(f"{len(trades_list)} trades imported successfully!")
