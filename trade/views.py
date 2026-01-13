import random
from django.http import HttpResponse
from datetime import datetime
from django.utils.timezone import localtime
from collections import Counter
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.forms.models import model_to_dict
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from django.db.models import Avg
from django.views.decorators.http import require_POST
from .models import Trades
from .forms import NewTradeForm, TradeUpdateForm
import joblib
import os
import pytz

# ---------------------------
# Global model cache
# ---------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pkl")
MODEL = None
FEATURES = [
    "pair", "momentum_h4", "momentum_h1", "momentum_15m", "momentum_5m", "momentum_1m",
    "session", "entry_place", "buy_or_sell", "setup_quality",
    "trade_type", "confirmation", "mood", "tp", "tp_reason", "risk_reward"
]

# ---------------------------
# Model training / loading
# ---------------------------
def train_model():
    global MODEL
    trades_qs = Trades.objects.filter(target__in=[0, 1])
    trades_list = list(trades_qs.values(*FEATURES, "target"))

    if not trades_list:
        print("⚠ No valid trades with target found. Model not trained.")
        return None

    X = pd.DataFrame(trades_list)
    y = X.pop("target")

    # Ensure numeric values are proper
    X["risk_reward"] = pd.to_numeric(X["risk_reward"], errors="coerce")
    X["setup_quality"] = pd.to_numeric(X["setup_quality"], errors="coerce")

    categorical_features = [
        "pair", "momentum_h4", "momentum_h1", "momentum_15m",
        "momentum_5m", "momentum_1m", "session", "entry_place",
        "buy_or_sell", "trade_type", "confirmation", "mood", "tp", "tp_reason"
    ]
    numeric_features = ["risk_reward", "setup_quality"]

    # Pipelines
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="mean"))
    ])

    preprocessor = ColumnTransformer([
        ("cat", categorical_pipeline, categorical_features),
        ("num", numeric_pipeline, numeric_features)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=2000, solver="liblinear"))
    ])

    model.fit(X, y)
    print("✅ Model trained successfully.")

    joblib.dump(model, MODEL_PATH)  # Save for future fast loading
    MODEL = model
    return model

def get_model():
    global MODEL
    if MODEL is not None:
        return MODEL
    if os.path.exists(MODEL_PATH):
        MODEL = joblib.load(MODEL_PATH)
        print("✅ Loaded model from disk.")
        return MODEL
    return train_model()



def get_trading_session():
    """Returns the current trading session based on local time."""
    
    # Set timezones
    london = pytz.timezone("Europe/London")
    newyork = pytz.timezone("America/New_York")
    asia = pytz.timezone("Asia/Tokyo")  # You can adjust to your preferred Asia market

    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Convert UTC to respective sessions
    london_time = now_utc.astimezone(london)
    newyork_time = now_utc.astimezone(newyork)
    asia_time = now_utc.astimezone(asia)

    hour = now_utc.hour  # Use UTC hour for simple logic

    # Simple mapping based on typical market sessions (adjust as needed)
    if 8 <= london_time.hour < 16:
        return "London 10 AM"
    elif 13 <= newyork_time.hour < 21:
        return "Newyork 4 PM"
    else:
        return "Asia 2 AM"



# ---------------------------
# RVS calculation
# ---------------------------
def calculate_rvs(trade):
    rvs = 0
    row = model_to_dict(trade)

    if row.get("confirmation", "").lower() == "no":
        rvs += 2

    momentums = [
        row.get("momentum_h4"), row.get("momentum_h1"),
        row.get("momentum_15m"), row.get("momentum_5m")
    ]
    momentums = [m for m in momentums if m]
    if len(set(momentums)) > 1:
        rvs += 3

    if row.get("entry_place", "").lower() == "other":
        rvs += 2

    if row.get("setup_quality") and row["setup_quality"] <= 4:
        rvs += 2

    if row.get("mood", "").lower() != "calm":
        rvs += 3

    if rvs == 0:
        rvs_grade = "A+"
    elif rvs <= 2:
        rvs_grade = "A"
    elif rvs <= 5:
        rvs_grade = "B"
    elif rvs <= 8:
        rvs_grade = "C"
    else:
        rvs_grade = "F"

    trade.rvs = rvs
    trade.rvs_grade = rvs_grade
    return trade


def export_trades_to_excel(request):
    """
    Export Trades data to Excel file and return as download response.
    Handles timezone-aware datetimes by converting them to naive local time.
    """
    # Fetch all trades
    trades_qs = Trades.objects.all()
    
    # Convert queryset to list of dicts
    trades_list = list(trades_qs.values())
    
    # Convert timezone-aware datetimes to naive
    for trade in trades_list:
        for key, value in trade.items():
            if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                trade[key] = localtime(value).replace(tzinfo=None)
    
    # Convert to DataFrame
    df = pd.DataFrame(trades_list)
    
    # Optional: remove unwanted columns
    exclude_cols = ['id']
    df = df[[col for col in df.columns if col not in exclude_cols]]
    
    # Prepare Excel response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="trades.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
    
    return response


# ---------------------------
# Index view
# ---------------------------
def index_view(request):
    model = get_model()

    if request.method == "POST":
        form = NewTradeForm(request.POST)
        if form.is_valid():
            new_trade = form.save(commit=False)

            # Unique ID
            existing_ids = Trades.objects.values_list("trade_id", flat=True)
            new_id = random.randint(1000, 9999)
            while new_id in existing_ids:
                new_id = random.randint(1000, 9999)
            new_trade.trade_id = new_id
            new_trade.timestamp = datetime.now()

            if not new_trade.session:
                new_trade.session = get_trading_session()

            # Fill empty fields
            for field in Trades._meta.get_fields():
                if getattr(new_trade, field.name, None) in ["", None]:
                    setattr(new_trade, field.name, None)

            # Prediction
            probability = None
            rating = None
            if model:
                pred_data = {col: [getattr(new_trade, col, "Blank")] for col in FEATURES}
                pred_df = pd.DataFrame(pred_data)
                pred_df["risk_reward"] = pd.to_numeric(pred_df["risk_reward"], errors="coerce").fillna(0)
                probability = model.predict_proba(pred_df)[0][1] * 100
                rating = "A" if probability >= 70 else "B" if probability >= 60 else "C" if probability >= 50 else "D"

            # RVS
            new_trade = calculate_rvs(new_trade)

            # Trade preview
            trade_preview_data = {}
            exclude_field = [
                "id","momentum_h4","momentum_h1","momentum_15m","rvs","risk_reward",
                "momentum_5m","momentum_1m","trade_id","timestamp","trade_type",
                "buy_or_sell","session","entry_place","confirmation","mood",
                "tp","tp_reason","setup_quality","target","reason","holding_time_hrs",
                "holding_time_mns","narration"
            ]
            for field in Trades._meta.get_fields():
                if field.name in exclude_field:
                    continue
                trade_preview_data[field.verbose_name.title()] = getattr(new_trade, field.name, None)

            trade_preview_data["RVS"] = new_trade.rvs
            trade_preview_data["RVS Grade"] = new_trade.rvs_grade
            if probability:
                trade_preview_data["Win Probability (%)"] = round(probability, 1)
                trade_preview_data["Trade Rating"] = rating

            if "confirm_save" in request.POST:
                new_trade.save()
                print(f"✅ New trade saved with ID {new_trade.trade_id}")
                return redirect("index")

            return render(request, 'trade/index.html', {
                'form': form,
                'show_confirm': True,
                'trade_preview': trade_preview_data,
            })

    else:
        form = NewTradeForm()

    return render(request, 'trade/index.html', {
        'form': form,
        'show_confirm': False,
    })

def journal_view(request):
    trades = Trades.objects.filter(target__isnull=True)
    return render( request, 'trade/journal.html', {
    'trades':trades,
        })


def update_trade_view(request, trade_id):
    trade = get_object_or_404(Trades, trade_id=trade_id)

    if request.method == "POST":
        form = TradeUpdateForm(request.POST, instance=trade)
        if form.is_valid():
            updated_trade = form.save(commit=False)

            # Ensure empty strings become NULL
            for field in Trades._meta.fields:
                val = getattr(updated_trade, field.name)
                if val == "":
                    setattr(updated_trade, field.name, None)

            updated_trade.save()
            return redirect("journal")
    else:
        form = TradeUpdateForm(instance=trade)

    return render(request, "trade/update_trade.html", {
        "form": form,
        "trade": trade,
    })

def delete_trade_confirm(request, trade_id):
    trade = get_object_or_404(Trades, trade_id=trade_id)
    return render(request, "trade/delete_trade_confirm.html", {
        "trade": trade
    })
    

@require_POST
def delete_trade(request, trade_id):
    trade = get_object_or_404(Trades, trade_id=trade_id)
    trade.delete()
    return redirect("journal")

def performance_view(request):
    eurusd_wins = Trades.objects.filter(
    pair="EUR/USD",
    target=1
    ).count()
    eurusd_lost = Trades.objects.filter(
    pair="EUR/USD",
    target=0
    ).count()
    eurusd_winrate = round(eurusd_wins/(eurusd_wins+eurusd_lost)*100,2)

    gbpusd_wins = Trades.objects.filter(
    pair="GBP/USD",
    target=1
    ).count()
    gbpusd_lost = Trades.objects.filter(
    pair="GBP/USD",
    target=0
    ).count()
    gbpusd_winrate = round(gbpusd_wins/(gbpusd_wins+gbpusd_lost)*100,2)

    nzdusd_wins = Trades.objects.filter(
    pair="NZD/USD",
    target=1
    ).count()
    nzdusd_lost = Trades.objects.filter(
    pair="NZD/USD",
    target=0
    ).count()
    nzdusd_winrate = round(nzdusd_wins/(nzdusd_wins+nzdusd_lost)*100,2) 

    audjpy_wins = Trades.objects.filter(
    pair="AUD/JPY",
    target=1
    ).count()
    audjpy_lost = Trades.objects.filter(
    pair="AUD/JPY",
    target=0
    ).count()
    audjpy_winrate = round(audjpy_wins/(audjpy_wins+audjpy_lost)*100,2) 

    eurjpy_wins = Trades.objects.filter(
    pair="EUR/JPY",
    target=1
    ).count()
    eurjpy_lost = Trades.objects.filter(
    pair="EUR/JPY",
    target=0
    ).count()
    eurjpy_winrate = round(eurjpy_wins/(eurjpy_wins+eurjpy_lost)*100,2)

    total_wins_all = Trades.objects.filter(
    target=1
    ).count()
    total_lost_all = Trades.objects.filter(
    target=0
    ).count()
    
    all_trades = total_wins_all + total_lost_all
    
    ####  avg RR per pair  ######
    rr_eurusd = round(Trades.objects.filter(target=1, pair="EUR/USD").aggregate(rr_eurusd=Avg('risk_reward'))["rr_eurusd"] or 0,2)
    rr_gbpusd = round(Trades.objects.filter(target=1, pair="GBP/USD").aggregate(rr_gbpusd=Avg("risk_reward"))["rr_gbpusd"] or 0,2)
    rr_nzdusd = round(Trades.objects.filter(target=1, pair="NZD/USD").aggregate(rr_nzdusd=Avg("risk_reward"))["rr_nzdusd"] or 0,2)
    rr_audjpy = round(Trades.objects.filter(target=1, pair="AUD/JPY").aggregate(rr_audjpy=Avg("risk_reward"))["rr_audjpy"] or 0,2)
    rr_eurjpy = round(Trades.objects.filter(target=1, pair="EUR/JPY").aggregate(rr_eurjpy=Avg("risk_reward"))["rr_eurjpy"] or 0,2)
    


    trades_qs = Trades.objects.filter(target__in=[0, 1]).order_by("-timestamp")[:30]
    
    df = pd.DataFrame.from_records(trades_qs.values(
        "target",        # 1 = win, 0 = loss
        "risk_reward",   # RR value
        "rvs"            # Rule Violation Score
    ))

    total_trades = len(df)

    if total_trades == 0:
        winrate = lossrate = expectancy = avg_rr_value = avg_rvs = 0
    else:
        wins = df[df["target"] == 1]
        losses = df[df["target"] == 0]
    
        winrate = round((len(wins) / total_trades) * 100, 2)
        lossrate = round((len(losses) / total_trades) * 100, 2)
    
        avg_rr_value = round(df["risk_reward"].mean(), 2)
        avg_rvs = round(df["rvs"].mean(), 2)
    
        # Expectancy formula:
        # E = (Win% × Avg Win RR) − (Loss% × Avg Loss RR)
        avg_win_rr = wins["risk_reward"].mean() if not wins.empty else 0
        #avg_loss_rr = losses["risk_reward"].mean() if not losses.empty else 0
        avg_loss_rr = 1
    
        expectancy = round(
            ((winrate / 100) * avg_win_rr) -
            ((lossrate / 100) * avg_loss_rr),
            2
        )
 
    reasons = Trades.objects.filter(target=0).order_by("-timestamp").values_list("reason",flat=True)[:10]


    if reasons:
        most_common_reason = Counter(reasons).most_common(1)[0][0]
    else:
        most_common_reason = None

    messege = ''
    if most_common_reason == "Psycho/Mood":
        messege="Refresh your psychology, avoid emotional trading and take rest if necessary"
    elif most_common_reason == "Wrong Structure":
        messege = "Review trade structures, ensure proper analysis before executing trade"  
    elif most_common_reason == "Trend":
        messege = "Follow the Trend carefully, avaoid forcing trades against it" 
    elif most_common_reason == "FOMO":
        messege = "Avoid fear of missing out, there are plenty of chances to come, just trade your plan" 

    elif most_common_reason == "Greed":
        messege = "Control Greed, just take profit according to your plan" 

    elif most_common_reason == "No Confirmation":
        messege = "Wait for confirmation, patience increases your probability for success" 

    elif most_common_reason == "Momentum":
        messege = "Avoid weak Momentums, always wait for the best setups" 
    elif most_common_reason == "News":
        messege = "Be cautious around News, it is very risk"
    elif most_common_reason == "Other":
        messege = "Stop trading for a while, review your strategy and evaluate yourself!"
    else:
        messege="You are doing great!" 



    return render(request, 'trade/performance.html', {
    'eurusd_wins':eurusd_wins,
    'eurusd_lost':eurusd_lost,
    'gbpusd_wins':gbpusd_wins,
    'gbpusd_lost':gbpusd_lost,
    'nzdusd_wins':nzdusd_wins,
    'nzdusd_lost':nzdusd_lost,
    'audjpy_wins':audjpy_wins,
    'audjpy_lost':audjpy_lost,
    'eurjpy_wins':eurjpy_wins,
    'eurjpy_lost':eurjpy_lost,
    'total_wins_all':total_wins_all,
    'total_lost_all':total_lost_all,
    'all_trades':all_trades,
    'rr_eurusd':rr_eurusd,
    'rr_gbpusd':rr_gbpusd,
    'rr_nzdusd':rr_nzdusd,
    'rr_audjpy':rr_audjpy,
    'rr_eurjpy':rr_eurjpy,
    'eurusd_winrate':eurusd_winrate,
    'gbpusd_winrate':gbpusd_winrate,
    'nzdusd_winrate':nzdusd_winrate,
    'audjpy_winrate':audjpy_winrate,
    'eurjpy_winrate':eurjpy_winrate,
    'winrate':winrate,
    'lossrate':lossrate,
    'expectancy':expectancy,
    'avg_rr_value':avg_rr_value,
    'avg_rvs':avg_rvs,
    'messege':messege
    })


def trades_view(request):

    trades = Trades.objects.filter(target__in=[0, 1]).order_by("-timestamp")[:10]

    return render(request, "trade/trades.html",{
    'trades':trades,
        })