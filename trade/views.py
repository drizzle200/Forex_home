import random
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from datetime import datetime, time
from django.utils.timezone import localtime,now
from collections import Counter
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.forms.models import model_to_dict
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from django.db.models import Avg,Sum,Count, StdDev, Q, Case, When, Value, FloatField
from django.utils import timezone
from django.views.decorators.http import require_POST,require_GET
from .models import Trades, Pairs
from .services import restrict_trade
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

    # --- Check number of classes ---
    if len(y.unique()) < 2:
        print("⚠ Not enough classes to train model. Need at least 2 classes.")
        return None

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
        ("classifier", LogisticRegression(max_iter=2000, solver="lbfgs"))
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

    try:
        if os.path.exists(MODEL_PATH):
            MODEL = joblib.load(MODEL_PATH)
            print("✅ Loaded model from disk.")
            return MODEL
    except Exception as e:
        print("⚠ Model load failed. Retraining...", e)
        return train_model()

    return train_model()
 



def get_trading_session() -> str:
    """
    Returns the current trading session based on the user's local timezone,
    using standard FX market session windows.
    """

    # --- Get local timezone (your country) ---
    local_tz = pytz.timezone(settings.TIME_ZONE)

    # --- Current local time ---
    now_local = timezone.now().astimezone(local_tz)
    hour = now_local.hour

    # --- FX Session Windows (LOCAL TIME) ---
    # These are approximate and intentionally overlapping
    ASIA = range(0, 9)        # 00:00 – 08:59
    LONDON = range(8, 17)     # 08:00 – 16:59
    NEW_YORK = range(13, 22)  # 13:00 – 21:59

    # --- Determine active session ---
    if hour in LONDON and hour in NEW_YORK:
        return "London / New York Overlap"
    elif hour in LONDON:
        return "London Session"
    elif hour in NEW_YORK:
        return "New York Session"
    else:
        return "Asia Session"



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

############

#restrict trade for correlated pairs



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
# ---------------------------[]


def index_view(request):
    model = get_model()
   
    if request.method == "POST":
        form = NewTradeForm(request.POST)

        if form.is_valid():
            new_trade = form.save(commit=False)

            try:
                with transaction.atomic():

                    # 🔒 Restrict trade BEFORE doing any heavy work
                    restrict_trade(
                        pair=new_trade.pair,
                        new_trade_type=new_trade.trade_type
                    )

                    # Unique trade ID
                    existing_ids = set(
                        Trades.objects.values_list("trade_id", flat=True)
                    )
                    new_id = random.randint(1000, 9999)
                    while new_id in existing_ids:
                        new_id = random.randint(1000, 9999)

                    new_trade.trade_id = new_id
                    new_trade.timestamp = datetime.now()

                    if not new_trade.session:
                        new_trade.session = get_trading_session()

                    # Normalize empty fields
                    for field in Trades._meta.get_fields():
                        if hasattr(new_trade, field.name):
                            if getattr(new_trade, field.name) in ["", None]:
                                setattr(new_trade, field.name, None)

                    # Prediction
                    probability = None
                    rating = None
                    if model:
                        pred_data = {
                            col: [getattr(new_trade, col, "Blank")]
                            for col in FEATURES
                        }
                        pred_df = pd.DataFrame(pred_data)
                        pred_df["risk_reward"] = pd.to_numeric(
                            pred_df["risk_reward"], errors="coerce"
                        ).fillna(0)

                        probability = model.predict_proba(pred_df)[0][1] * 100
                        rating = (
                            "A" if probability >= 70 else
                            "B" if probability >= 60 else
                            "C" if probability >= 50 else
                            "D"
                        )

                    # RVS calculation
                    new_trade = calculate_rvs(new_trade)

                    # Trade preview
                    trade_preview_data = {}
                    exclude_fields = {
                        "id", "momentum_h4", "momentum_h1", "momentum_15m",
                        "momentum_5m", "momentum_1m", "rvs", "rvs_grade","risk_reward",
                        "trade_id", "timestamp", "trade_type", "buy_or_sell",
                        "session", "entry_place", "confirmation", "mood",
                        "tp", "tp_reason", "setup_quality", "target",
                        "reason", "holding_time_hrs", "holding_time",
                        "narration"
                    }

                    for field in Trades._meta.get_fields():
                        if field.name not in exclude_fields:
                            trade_preview_data[field.verbose_name.title()] = \
                                getattr(new_trade, field.name, None)

                    trade_preview_data["RVS"] = new_trade.rvs
                    trade_preview_data["RVS Grade"] = new_trade.rvs_grade

                    if probability is not None:
                        trade_preview_data["Win Probability (%)"] = round(probability, 1)
                        trade_preview_data["Trade Rating"] = rating

                    if "confirm_save" in request.POST:
                        new_trade.save()
                        return redirect("index")

            except ValidationError as e:
                form.add_error(None, e.message)

            return render(request, "trade/index.html", {
                "form": form,
                "show_confirm": True,
                "trade_preview": trade_preview_data if "trade_preview_data" in locals() else None,
            })

    else:
        form = NewTradeForm()
   
    return render(request, "trade/index.html", {
        "form": form,
        "show_confirm": False,
    })



def journal_view(request):
    trades = Trades.objects.filter(target__isnull=True)
    return render( request, 'trade/journal.html', {
    'trades':trades,
        })


def update_trade_view(request, trade_id):
    trade = get_object_or_404(Trades, trade_id=trade_id)

    old_target = trade.target

    if request.method == "POST":
        form = TradeUpdateForm(request.POST, instance=trade)

        if form.is_valid():
            updated_trade = form.save(commit=False)

            # Convert empty strings to NULL
            for field in Trades._meta.fields:
                if field.is_relation:
                    continue
                if getattr(updated_trade, field.name) == "":
                    setattr(updated_trade, field.name, None)

            # ✅ SET holding time ONLY when target is updated first time
            if (
                old_target is None
                and updated_trade.target is not None
                and updated_trade.holding_time is None
            ):
                delta = now() - updated_trade.timestamp
                updated_trade.holding_time = int(
                    delta.total_seconds() // 60
                )

            updated_trade.save()
            return redirect("journal")

    else:
        form = TradeUpdateForm(instance=trade)

    return render(
        request,
        "trade/update_trade.html",
        {
            "form": form,
            "trade": trade,
        }
    )


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
    
    # 1️⃣ Get last 20 closed trades
    last_20_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:20]
    last_2_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:2]
    
    # 2️⃣ Aggregate everything from the SAME queryset
    stats = last_20_trades.aggregate(
        total_trades=Count("id"),
        all_won=Count("id", filter=Q(target=1)),
        all_lost=Count("id", filter=Q(target=0)),
        avg_risk_reward=Avg("risk_reward", filter=Q(target=1)),
        std_dev_rr=StdDev("risk_reward"),
        avg_rvs=Avg("rvs"),
    )
    stat = last_2_trades.aggregate(        
        avg_rvs=Avg("rvs"),
    )
    
    total_trades = stats["total_trades"] or 0
    all_won = stats["all_won"] or 0
    all_lost = stats["all_lost"] or 0
    avg_risk_reward = round(stats["avg_risk_reward"] or 0, 2)
    std_dev_rr = round(stats["std_dev_rr"] or 0, 2)
    avg_rvs = round(stat["avg_rvs"] or 0, 2)
    
    # 3️⃣ Calculate winrate safely
    if total_trades > 0:
        overallwinrate = round((all_won / total_trades) * 100, 2)
        overalllossrate = round((all_lost / total_trades) * 100, 2)
    else:
        overallwinrate = 0
        overalllossrate = 0
    
    # 4️⃣ Expectancy formula
    expectancy = round(
        ((overallwinrate / 100) * avg_risk_reward) -
        ((overalllossrate / 100) * 1),
        2
    )
    
    pairs_summary = []

    pairs = Pairs.objects.all()

    for pair in pairs:
        trades = pair.trades.filter(target__in=[0, 1])
    
        if not trades.exists():
            continue
    
        won = trades.filter(target=1).count()
        lost = trades.filter(target=0).count()
        total = won + lost
    
        winrate = round((won / total) * 100, 2) if total > 0 else 0
    
        # ✅ Sum of winning RR
        total_win_rr = trades.filter(target=1).aggregate(
            total_rr=Sum("risk_reward")
        )["total_rr"] or 0
    
        # ✅ Total loss R (each loss = -1R)
        total_loss_rr = lost * 1
    
        # ✅ Net Profit in R
        net_profit = round(total_win_rr - total_loss_rr, 2)
      
    
        avg_rr = trades.filter(target=1).aggregate(
            avg_rr=Avg("risk_reward")
        )["avg_rr"] or 0
    
        avg_rr = round(avg_rr, 2)
    
        pairs_summary.append({
            "id": pair.id,
            "pair": pair.name,
            "won": won,
            "lost": lost,
            "avg_rr": avg_rr,
            "winrate": winrate,
            "profit_r": net_profit,   
        })

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

    #################### geting today's trades
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()
    
    todays_trades = Trades.objects.filter(timestamp__date=today).count()
    
    
    
    def grade_consistency(
        todays_trades: int,
        avg_rvs: float,
        std_dev_rr: float,
        most_common_reason
        ):
        score = 0
        max_score = 4
    
        # Rule 1: Overtrading 
        if todays_trades <= 2:
            score += 1
    
        # Rule 2: RVS control
        if avg_rvs < 4:
            score += 1
    
        # Rule 3: RR execution consistency
        if std_dev_rr <= 1:
            score += 1
    
        # Rule 4: no strategy breaking
        if most_common_reason is None:
            score += 1
    
        # ---- Tier mapping ----
        if score == 4:
            tier = "Mastery"
            level = 4
        elif score == 3:
            tier = "High"
            level = 3
        elif score == 2:
            tier = "Medium"
            level = 2
        else:
            tier = "Low"
            level = 1
    
        return {
            "consistency_score": score,
            "consistency_max": max_score,
            "consistency_level": level,
            "consistency_tier": tier,
            "consistency_percent": int((score / max_score) * 100),
        }

    grade_consistency= grade_consistency( 
        todays_trades,
        avg_rvs,
        std_dev_rr,
        most_common_reason)
    
    # Today's closed trades only
    todays_profit = Trades.objects.filter(
        timestamp__date=today,
        target__in=[0, 1]
    ).aggregate(
        total_profit=Sum(
            Case(
                When(target=1, then="risk_reward"),  # Win = +RR
                When(target=0, then=Value(-1)),      # Loss = -1R
                output_field=FloatField(),
            )
        )
    )["total_profit"] or 0
    todays_profit = round(todays_profit, 2)
    
    last_16_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:40]  # latest first
    
    # Reverse the lists for chronological plotting
    trades_list = list(last_16_trades)[::-1]
    
    risk_rewards = [t.risk_reward for t in trades_list]
    targets = [t.target for t in trades_list]
    dates = [t.timestamp.strftime("%Y-%m-%d") for t in trades_list]  # now oldest → newest
    
    # Build cumulative performance
    performance = []
    cum_value = 0
    for rr, t in zip(risk_rewards, targets):
        if t == 1:
            cum_value += rr
        else:
            cum_value -= 1
        performance.append(cum_value)
  

    return render(request, 'trade/performance.html', {
   
    'grade_consistency': grade_consistency,
    'expectancy':expectancy,
    'avg_rvs':avg_rvs,
    'avg_risk_reward':avg_risk_reward,    
    "pairs_summary": pairs_summary, 
    'messege':messege,
    "overallwinrate":overallwinrate,
    "overalllossrate":overalllossrate,
    'todays_trades':todays_trades,
    'todays_profit':todays_profit,
    'std_dev_rr':std_dev_rr,
    'performance':performance,
    'dates':dates,
    })

                                                                                                             
def trades_view(request):

    trades = Trades.objects.filter(target__in=[0, 1]).order_by("-timestamp")[:16]
    
    return render(request, "trade/trades.html",{
    'trades':trades,
        })

def home_view(request):

    reasons = Trades.objects.filter(target=0).order_by("-timestamp").values_list("reason",flat=True)[:10]


    if reasons:
        most_common_reason = Counter(reasons).most_common(1)[0][0]
    else:
        most_common_reason = None
    trading_session = get_trading_session()
    return  render(request, 'trade/home.html', {
    'trading_session':trading_session,
    'most_common_reason':most_common_reason,
    })

    

def performance_by_pair_view(request, pair_id):

    pair = get_object_or_404(Pairs, id=pair_id)
    ###############
    # Get trades (ascending timestamp)
    trades = list(pair.trades.filter(target__isnull=False).order_by("timestamp")[:40])
    
    # Prepare lists
    risk_rewards = [t.risk_reward for t in trades]
    targets = [t.target for t in trades]
    dates = [t.timestamp.strftime("%Y-%m-%d") for t in trades]
    
    # Build cumulative performance in chronological order
    performance = []
    cum_value = 0
    
    for rr, t in zip(risk_rewards, targets):
        if t == 1:
            cum_value += rr
        elif t == 0:
            cum_value -= 1
        performance.append(cum_value)
    
    # ✅ last 20 winning trades with holding_time    
    trades = pair.trades.filter(target__isnull=False).order_by("-timestamp")[:20]
    # --- categorical stats ---
    session = trades.values_list("session", flat=True)
    trade_type = trades.values_list("trade_type", flat=True)
    entry_place = trades.values_list("entry_place", flat=True)

    # --- average holding time (minutes) ---
    average_minutes = trades.aggregate(
        avg_ht=Avg("holding_time")
    )["avg_ht"]

    # --- format holding time ---
    average_holding_time = ""

    if average_minutes:
        average_minutes = int(average_minutes)
        hours, minutes = divmod(average_minutes, 60)

        if hours and minutes:
            average_holding_time = f"{hours}h {minutes}m"
        elif hours:
            average_holding_time = f"{hours}h"
        else:
            average_holding_time = f"{minutes}m"
    
 
    # --- most common values ---
    try:
        best_trade_type = Counter(trade_type).most_common(1)[0][0]
    except IndexError:
        best_trade_type = "N/A"

    try:
        most_winning_session = Counter(session).most_common(1)[0][0]
    except IndexError:
        most_winning_session = "N/A"

    try:
        best_entry_place = Counter(entry_place).most_common(1)[0][0]
    except IndexError:
        best_entry_place = "N/A"
    

    def get_max_treaks(trades):
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        for trade in trades:
            if trade.target == 1:
                current_wins += 1
                current_losses =0
                max_wins = max(max_wins,current_wins)
            elif trade.target == 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses,current_losses)
        return max_wins,max_losses
    max_wins, max_losses = get_max_treaks(trades)    

    return render(
        request,
        "trade/performance_by_pair.html",
        {
            "max_wins":max_wins,
            "max_losses":max_losses,
            "average_holding_time": average_holding_time,
            "best_entry_place": best_entry_place,
            "best_trade_type": best_trade_type,
            "most_winning_session": most_winning_session,
            "pair": pair,
            "dates": dates,
            "performance": performance,
        }
    )

def academy_view(request):

    return  render(request, 'trade/academy/academy.html', {
    
    })


def p(request):

    return render(request, 'trade/p.html', {

    })
@require_GET
def performance_overview(request):
    """
    Returns overall performance metrics for dashboard.
    """

    data = {
        "winrate": 62,          # %
        "lossrate": 38,         # %
        "expectancy": 1.8,      # R
        "avg_rr": 2.4,          # R
        "avg_risk": -1.0,       # R
        "rvs": 12,              # sample size
    }

    return JsonResponse(data)
