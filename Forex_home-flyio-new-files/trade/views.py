import random
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from datetime import datetime, time, timedelta
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
from django.db.models import Avg,Sum,Count, StdDev, Q, Case, When, Value, FloatField, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_POST,require_GET
from .models import Trades, Pairs,Advice,  Mood
from .services import restrict_trade
from .forms import NewTradeForm, TradeUpdateForm
import joblib
import os, pytz
import json  

from .market_session import is_market_open, get_trading_session, get_market_volatility, get_major_news_impact,get_session_pairs,get_pair_recommendations


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
    # 2️⃣ Calculate overall statistics
    stats = calculate_overall_stats()
    
    # 3️⃣ Get pairs summary
    pairs_summary = get_pairs_summary()
    
    # 4️⃣ Analyze losing reasons - NOW HANDLES DICTIONARY RETURN
    analysis = analyze_losing_reasons()  # This returns a dictionary
    
    # Extract values from analysis
    most_common_reason = analysis['most_common_reason']
    most_common_count = analysis['most_common_count']
    most_common_percentage = analysis['most_common_percentage']
    message = analysis['message']
    reason_breakdown = analysis['reason_breakdown']
    total_losing_analyzed = analysis['total_losing_analyzed']
    unique_reasons = analysis['unique_reasons']
    
    # 5️⃣ Get today's trading data
    today_data = get_today_trading_data()
    
    # 6️⃣ Calculate consistency grade
    grade_consistency = calculate_consistency_grade(
        today_data['todays_trades'],
        stats['avg_rvs'],
        stats['std_dev_rr'],
        most_common_reason  # This still works with the extracted value
    )
    
    # 7️⃣ Prepare performance chart data
    chart_data = prepare_chart_data()
    
    return render(request, 'trade/performance.html', {
        'grade_consistency': grade_consistency,
        'expectancy': stats['expectancy'],
        'avg_rvs': stats['avg_rvs'],
        'avg_risk_reward': stats['avg_risk_reward'],
        "pairs_summary": pairs_summary,
        
        # Loss reason analysis data
        'most_common_reason': most_common_reason,
        'most_common_count': most_common_count,
        'most_common_percentage': most_common_percentage,
        'message': message,
        'reason_breakdown': reason_breakdown,
        'total_losing_analyzed': total_losing_analyzed,
        'unique_reasons': unique_reasons,
        
        # Performance stats
        "overallwinrate": stats['overallwinrate'],
        "overalllossrate": stats['overalllossrate'],
        'todays_trades': today_data['todays_trades'],
        'todays_profit': today_data['todays_profit'],
        'std_dev_rr': stats['std_dev_rr'],
        
        # Chart data
        'performance': chart_data['performance'],
        'dates': chart_data['dates'],
    })

#@login_required
#@csrf_exempt
def save_mood(request):
    """Save user's mood with gamified response"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mood = data.get('mood')
            notes = data.get('notes', '')
            
            # Check if already have mood for today
            today = timezone.now().date()
            existing_mood = Mood.objects.filter(user=request.user, date=today).first()
            
            if existing_mood:
                # Update existing mood
                existing_mood.mood = mood
                existing_mood.notes = notes
                existing_mood.save()
                created = False
            else:
                # Create new mood
                existing_mood = Mood.objects.create(
                    user=request.user,
                    mood=mood,
                    notes=notes
                )
                created = True
            
            # Get recommendation
            recommendation = Mood.get_mood_recommendation(mood)
            
            # Get today's stats (you can calculate these from your trade data)
            today_trades = Trades.objects.filter(
                timestamp__date=today,
                user=request.user
            )
            
            # Update mood with trading data (optional)
            existing_mood.trades_count = today_trades.count()
            existing_mood.profit_loss = calculate_daily_profit(today_trades)
            existing_mood.save()
            
            # Gamified response
            response_data = {
                'success': True,
                'mood': mood,
                'emoji': Mood.MOOD_EMOJIS.get(mood, '😐'),
                'color': Mood.MOOD_COLORS.get(mood, '#6b7280'),
                'message': recommendation['message'],
                'action': recommendation['action'],
                'animation': recommendation['animation'],
                'created': created,
                'streak': get_mood_streak(request.user),
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def get_mood_stats(request):
    """Get mood statistics for charts"""
    days = int(request.GET.get('days', 30))
    stats = Mood.get_mood_stats(days)
    
    # Get today's mood
    today_mood = Mood.get_today_mood(request.user if request.user.is_authenticated else None)
    
    # Prepare chart data
    chart_data = {
        'labels': [],
        'values': [],
        'colors': [],
    }
    
    for mood_code, data in stats.items():
        chart_data['labels'].append(data['name'])
        chart_data['values'].append(data['count'])
        chart_data['colors'].append(data['color'])
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'chart_data': chart_data,
        'today_mood': {
            'mood': today_mood.mood if today_mood else None,
            'emoji': Mood.MOOD_EMOJIS.get(today_mood.mood, '') if today_mood else '',
        } if today_mood else None
    })


def get_mood_streak(user):
    """Calculate user's mood logging streak"""
    moods = Mood.objects.filter(user=user).order_by('-date')
    if not moods.exists():
        return 0
    
    streak = 1
    last_date = moods.first().date
    
    for mood in moods[1:]:
        if (last_date - mood.date).days == 1:
            streak += 1
            last_date = mood.date
        else:
            break
    
    return streak


def calculate_daily_profit(trades_queryset):
    """Calculate profit for a day's trades"""
    profit = 0
    for trade in trades_queryset.filter(target__in=[0, 1]):
        if trade.target == 1:
            profit += trade.risk_reward or 0
        else:
            profit -= 1
    return round(profit, 2)

def calculate_overall_stats():
    """Calculate overall statistics from trades"""
    # Aggregate stats from last 20 trades
     # 1️⃣ Get last 20 closed trades
    last_20_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:30]
    last_2_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:2]
    
    stats = last_20_trades.aggregate(
        total_trades=Count("id"),
        all_won=Count("id", filter=Q(target=1)),
        all_lost=Count("id", filter=Q(target=0)),
        avg_risk_reward=Avg("risk_reward", filter=Q(target=1)),
        std_dev_rr=StdDev("risk_reward"),
    )
    
    # Aggregate RVS from last 2 trades
    rvs_stats = last_2_trades.aggregate(        
        avg_rvs=Avg("rvs"),
    )
    
    total_trades = stats["total_trades"] or 0
    all_won = stats["all_won"] or 0
    all_lost = stats["all_lost"] or 0
    
    # Calculate winrate safely
    if total_trades > 0:
        overallwinrate = round((all_won / total_trades) * 100, 2)
        overalllossrate = round((all_lost / total_trades) * 100, 2)
    else:
        overallwinrate = 0
        overalllossrate = 0
    
    avg_risk_reward = round(stats["avg_risk_reward"] or 0, 2)
    std_dev_rr = round(stats["std_dev_rr"] or 0, 2)
    avg_rvs = round(rvs_stats["avg_rvs"] or 0, 2)
    
    # Calculate expectancy
    expectancy = round(
        ((overallwinrate / 100) * avg_risk_reward) -
        ((overalllossrate / 100) * 1),
        2
    )
    
    return {
        'total_trades': total_trades,
        'all_won': all_won,
        'all_lost': all_lost,
        'overallwinrate': overallwinrate,
        'overalllossrate': overalllossrate,
        'avg_risk_reward': avg_risk_reward,
        'std_dev_rr': std_dev_rr,
        'avg_rvs': avg_rvs,
        'expectancy': expectancy,
    }


def get_pairs_summary():
    """Generate summary statistics for each trading pair"""
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
    
        # Sum of winning RR
        total_win_rr = trades.filter(target=1).aggregate(
            total_rr=Sum("risk_reward")
        )["total_rr"] or 0
    
        # Total loss R (each loss = -1R)
        total_loss_rr = lost * 1
    
        # Net Profit in R
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
    
    return pairs_summary


def analyze_losing_reasons():
    """Analyze most common reasons for losing trades and generate advice"""
    # Get last 50 losing trades for better sample size (or all if you prefer)
    losing_trades = Trades.objects.filter(target=0).order_by("-timestamp")[:50]
    reasons = list(losing_trades.values_list("reason", flat=True))
    
    # Filter out None values
    reasons = [r for r in reasons if r]
    
    if reasons:
        # Count occurrences
        reason_counts = Counter(reasons)
        most_common_reason, count = reason_counts.most_common(1)[0]
        
        # Calculate percentage
        total_reasons = len(reasons)
        percentage = round((count / total_reasons) * 100, 1) if total_reasons > 0 else 0
    else:
        most_common_reason = None
        count = 0
        percentage = 0
        reason_counts = Counter()

    # Message mapping
    message_map = {
        "Psycho/Mood": "🧠 Refresh your psychology, avoid emotional trading and take rest if necessary",
        "Wrong Structure": "📐 Review trade structures, ensure proper analysis before executing trade",
        "Trend": "📈 Follow the Trend carefully, avoid forcing trades against it",
        "FOMO": "🎯 Avoid fear of missing out, there are plenty of chances to come, just trade your plan",
        "Greed": "💰 Control Greed, just take profit according to your plan",
        "No Confirmation": "⏳ Wait for confirmation, patience increases your probability for success",
        "Momentum": "⚡ Avoid weak Momentums, always wait for the best setups",
        "News": "📰 Be cautious around News, it is very risky",
        "Other": "🛑 Stop trading for a while, review your strategy and evaluate yourself!",
    }
    
    # Get message with emoji
    message = message_map.get(most_common_reason, "🌟 You are doing great! Keep up the good work!")
    
    # Also get the full breakdown of all reasons (optional)
    reason_breakdown = []
    for reason, reason_count in reason_counts.most_common():
        reason_breakdown.append({
            'reason': reason,
            'count': reason_count,
            'percentage': round((reason_count / total_reasons) * 100, 1) if total_reasons > 0 else 0,
            'message': message_map.get(reason, "Review your strategy for this issue")
        })
    
    return {
        'most_common_reason': most_common_reason,
        'most_common_count': count,
        'most_common_percentage': percentage,
        'message': message,
        'total_losing_analyzed': len(reasons),
        'reason_breakdown': reason_breakdown,  # Full breakdown of all reasons
        'unique_reasons': len(reason_counts),   # Number of different reasons
    }


def get_today_trading_data():
    """Get today's trading statistics"""
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()
    
    todays_trades = Trades.objects.filter(timestamp__date=today).count()
    
    # Today's closed trades profit/loss
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
    
    return {
        'todays_trades': todays_trades,
        'todays_profit': todays_profit,
        'today_date': today,
    }
def get_yesterday_trading_data():
    """Get yesterday's trading statistics"""
    local_now = timezone.localtime(timezone.now())
    yesterday = local_now.date() - timedelta(days=1)
    
    yesterday_trades = Trades.objects.filter(timestamp__date=yesterday).count()
    
    # Yesterday's closed trades profit/loss
    yesterday_profit = Trades.objects.filter(
        timestamp__date=yesterday,
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
    yesterday_profit = round(yesterday_profit, 2)
    
    # Get winrate for yesterday
    yesterday_wins = Trades.objects.filter(
        timestamp__date=yesterday,
        target=1
    ).count()
    
    yesterday_total = Trades.objects.filter(
        timestamp__date=yesterday,
        target__in=[0, 1]
    ).count()
    
    yesterday_winrate = round((yesterday_wins / yesterday_total * 100), 2) if yesterday_total > 0 else 0
    
    return {
        'yesterday_trades': yesterday_trades,
        'yesterday_profit': yesterday_profit,
        'yesterday_date': yesterday,
        'yesterday_wins': yesterday_wins,
        'yesterday_losses': yesterday_total - yesterday_wins if yesterday_total > 0 else 0,
        'yesterday_total': yesterday_total,
        'yesterday_winrate': yesterday_winrate,
    }

def get_all_time_stats():
    """Get all-time trading statistics"""
    # All closed trades
    all_trades = Trades.objects.filter(target__in=[0, 1])
    
    total_trades = all_trades.count()
    
    if total_trades == 0:
        return {
            'total_trades': 0,
            'total_wins': 0,
            'total_losses': 0,
            'winrate': 0,
            'lossrate': 0,
            'total_profit_r': 0,
            'avg_risk_reward': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'longest_win_streak': 0,
            'longest_loss_streak': 0,
            'total_days_traded': 0,
            'avg_trades_per_day': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'total_r_multiple': 0,
        }
    
    # Basic counts
    total_wins = all_trades.filter(target=1).count()
    total_losses = all_trades.filter(target=0).count()
    
    # Winrate
    winrate = round((total_wins / total_trades) * 100, 2)
    lossrate = round((total_losses / total_trades) * 100, 2)
    
    # Profit calculations
    total_win_rr = all_trades.filter(target=1).aggregate(
        total=Sum("risk_reward")
    )["total"] or 0
    
    total_loss_rr = total_losses * 1  # Each loss = -1R
    
    total_profit_r = round(total_win_rr - total_loss_rr, 2)
    
    # Average risk-reward on winning trades
    avg_risk_reward = round(
        all_trades.filter(target=1).aggregate(
            avg=Avg("risk_reward")
        )["avg"] or 0, 2
    )
    
    # Best and worst trades
    best_trade = round(
        all_trades.filter(target=1).aggregate(
            best=Max("risk_reward")
        )["best"] or 0, 2
    )
    
    worst_trade = round(
        all_trades.filter(target=0).aggregate(
            worst=Min("risk_reward")  # This will be the smallest loss (closest to 0)
        )["worst"] or 0, 2
    )
    
    # Get the actual biggest loss (lowest value)
    biggest_loss = round(
        all_trades.filter(target=0).aggregate(
            biggest=Min("risk_reward")  # Most negative
        )["biggest"] or 0, 2
    )
    
    # Calculate streaks
    trades_chrono = all_trades.order_by('timestamp').values_list('target', flat=True)
    
    longest_win_streak = 0
    longest_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for target in trades_chrono:
        if target == 1:  # Win
            current_win_streak += 1
            current_loss_streak = 0
            longest_win_streak = max(longest_win_streak, current_win_streak)
        else:  # Loss
            current_loss_streak += 1
            current_win_streak = 0
            longest_loss_streak = max(longest_loss_streak, current_loss_streak)
    
    # Days traded
    trading_days = all_trades.dates('timestamp', 'day').count()
    avg_trades_per_day = round(total_trades / trading_days, 2) if trading_days > 0 else 0
    
    # Profit factor (Gross Profit / Gross Loss)
    gross_profit = total_win_rr
    gross_loss = total_loss_rr
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float('inf')
    
    # Expectancy
    expectancy = round(
        ((winrate / 100) * avg_risk_reward) - ((lossrate / 100) * 1),
        2
    )
    
    # Total R multiple (how many times you've grown your account)
    total_r_multiple = round(total_profit_r, 2)
    
    # Performance by month
    monthly_performance = []
    months = all_trades.dates('timestamp', 'month').distinct()
    
    for month in months:
        month_trades = all_trades.filter(timestamp__year=month.year, timestamp__month=month.month)
        month_wins = month_trades.filter(target=1).count()
        month_total = month_trades.count()
        
        month_win_rr = month_trades.filter(target=1).aggregate(
            total=Sum("risk_reward")
        )["total"] or 0
        
        month_loss_rr = month_trades.filter(target=0).count() * 1
        
        monthly_performance.append({
            'month': month.strftime('%B %Y'),
            'trades': month_total,
            'wins': month_wins,
            'losses': month_total - month_wins,
            'winrate': round((month_wins / month_total) * 100, 2) if month_total > 0 else 0,
            'profit_r': round(month_win_rr - month_loss_rr, 2),
        })
    
    # Performance by pair
    pair_performance = []
    pairs = Pairs.objects.all()
    
    for pair in pairs:
        pair_trades = pair.trades.filter(target__in=[0, 1])
        if pair_trades.exists():
            pair_wins = pair_trades.filter(target=1).count()
            pair_total = pair_trades.count()
            
            pair_win_rr = pair_trades.filter(target=1).aggregate(
                total=Sum("risk_reward")
            )["total"] or 0
            
            pair_loss_rr = pair_trades.filter(target=0).count() * 1
            
            pair_performance.append({
                'pair': pair.name,
                'trades': pair_total,
                'wins': pair_wins,
                'losses': pair_total - pair_wins,
                'winrate': round((pair_wins / pair_total) * 100, 2),
                'profit_r': round(pair_win_rr - pair_loss_rr, 2),
                'avg_rr': round(
                    pair_trades.filter(target=1).aggregate(
                        avg=Avg("risk_reward")
                    )["avg"] or 0, 2
                ),
            })
    
    # Sort pair performance by profit
    pair_performance.sort(key=lambda x: x['profit_r'], reverse=True)
    
    return {
        # Basic stats
        'total_trades': total_trades,
        'total_wins': total_wins,
        'total_losses': total_losses,
        'winrate': winrate,
        'lossrate': lossrate,
        
        # Profit stats
        'total_profit_r': total_profit_r,
        'total_win_rr': round(total_win_rr, 2),
        'total_loss_rr': total_loss_rr,
        'avg_risk_reward': avg_risk_reward,
        
        # Trade extremes
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'biggest_loss': biggest_loss,
        
        # Streaks
        'longest_win_streak': longest_win_streak,
        'longest_loss_streak': longest_loss_streak,
        'current_win_streak': current_win_streak,
        'current_loss_streak': current_loss_streak,
        
        # Time-based
        'total_days_traded': trading_days,
        'avg_trades_per_day': avg_trades_per_day,
        
        # Key metrics
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'total_r_multiple': total_r_multiple,
        
        # Detailed breakdowns
        'monthly_performance': monthly_performance,
        'pair_performance': pair_performance,
        
        # Best and worst pairs
        'best_pair': pair_performance[0] if pair_performance else None,
        'worst_pair': pair_performance[-1] if len(pair_performance) > 1 else None,
    }


def get_recent_activity(days=7):
    """Get trading activity for the last X days"""
    end_date = timezone.localtime(timezone.now()).date()
    start_date = end_date - timedelta(days=days)
    
    daily_stats = []
    
    for i in range(days):
        current_date = end_date - timedelta(days=i)
        day_trades = Trades.objects.filter(
            timestamp__date=current_date,
            target__in=[0, 1]
        )
        
        if day_trades.exists():
            wins = day_trades.filter(target=1).count()
            total = day_trades.count()
            
            day_win_rr = day_trades.filter(target=1).aggregate(
                total=Sum("risk_reward")
            )["total"] or 0
            
            day_loss_rr = day_trades.filter(target=0).count() * 1
            
            daily_stats.append({
                'date': current_date,
                'date_formatted': current_date.strftime('%a, %b %d'),
                'trades': total,
                'wins': wins,
                'losses': total - wins,
                'winrate': round((wins / total) * 100, 2),
                'profit_r': round(day_win_rr - day_loss_rr, 2),
            })
        else:
            daily_stats.append({
                'date': current_date,
                'date_formatted': current_date.strftime('%a, %b %d'),
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'winrate': 0,
                'profit_r': 0,
            })
    
    # Reverse to have oldest first
    daily_stats.reverse()
    
    return daily_stats

def calculate_consistency_grade(todays_trades, avg_rvs, std_dev_rr, most_common_reason):
    """Calculate trader consistency grade based on multiple factors"""
    score = 0
    max_score = 4

    # Rule 1: Overtrading check
    if todays_trades <= 2:
        score += 1

    # Rule 2: RVS control
    if avg_rvs < 4:
        score += 1

    # Rule 3: RR execution consistency
    if std_dev_rr <= 1:
        score += 1

    # Rule 4: No strategy breaking
    if most_common_reason is None:
        score += 1

    # Tier mapping
    tier_map = {
        4: ("Mastery", 4),
        3: ("High", 3),
        2: ("Medium", 2),
    }
    
    tier, level = tier_map.get(score, ("Low", 1))

    return {
        "consistency_score": score,
        "consistency_max": max_score,
        "consistency_level": level,
        "consistency_tier": tier,
        "consistency_percent": int((score / max_score) * 100),
    }


def prepare_chart_data(trade_count=40):
    """Prepare data for performance chart"""
    last_trades = Trades.objects.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:trade_count]  # latest first
    
    # Reverse for chronological order
    trades_list = list(last_trades)[::-1]
    
    risk_rewards = [t.risk_reward for t in trades_list]
    targets = [t.target for t in trades_list]
    
    # Format dates (platform independent)
    dates = []
    for t in trades_list:
        try:
            # Windows
            dates.append(t.timestamp.strftime("%#m/%#d"))
        except ValueError:
            # Unix/Linux/Mac
            dates.append(t.timestamp.strftime("%-m/%-d"))
    
    # Build cumulative performance
    performance = []
    cum_value = 0
    for rr, t in zip(risk_rewards, targets):
        if t == 1:
            cum_value += rr
        else:
            cum_value -= 1
        performance.append(round(cum_value, 2))  # Round to 2 decimal places
    
    return {
        'performance': performance,
        'dates': dates,
        'risk_rewards': risk_rewards,
        'targets': targets,
    }   


def get_mood_streak(user):
    """Calculate user's mood logging streak"""
    moods = Mood.objects.filter(user=user).order_by('-date')
    if not moods.exists():
        return 0
    
    streak = 1
    last_date = moods.first().date
    
    for mood in moods[1:]:
        if (last_date - mood.date).days == 1:
            streak += 1
            last_date = mood.date
        else:
            break
    
    return streak


def get_mood_achievements(user):
    """Calculate mood logging achievements"""
    streak = get_mood_streak(user)
    total_logs = Mood.objects.filter(user=user).count()
    
    achievements = []
    
    # Streak achievements
    if streak >= 30:
        achievements.append({'icon': '👑', 'title': 'Mood Legend', 'desc': '30 day streak!'})
    elif streak >= 14:
        achievements.append({'icon': '🏆', 'title': 'Mood Champion', 'desc': '14 day streak!'})
    elif streak >= 7:
        achievements.append({'icon': '🔥', 'title': 'Week Warrior', 'desc': '7 day streak!'})
    elif streak >= 3:
        achievements.append({'icon': '⚡', 'title': 'On Fire', 'desc': '3 day streak!'})
    
    # Total logs achievements
    if total_logs >= 100:
        achievements.append({'icon': '🌟', 'title': 'Mood Master', 'desc': '100 mood logs'})
    elif total_logs >= 50:
        achievements.append({'icon': '💫', 'title': 'Mood Expert', 'desc': '50 mood logs'})
    elif total_logs >= 30:
        achievements.append({'icon': '🎯', 'title': 'Getting Consistent', 'desc': '30 mood logs'})
    elif total_logs >= 10:
        achievements.append({'icon': '📊', 'title': 'Just Started', 'desc': '10 mood logs'})
    
    return achievements[:3]  # Return top 3 achievements


def get_mood_stats_for_dashboard(user, days=30):
    """Get mood statistics for dashboard charts"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    moods = Mood.objects.filter(
        user=user, 
        date__gte=start_date, 
        date__lte=end_date
    ).order_by('date')
    
    # Prepare data for charts
    mood_counts = {}
    daily_moods = []
    
    for mood_code, _ in Mood.MOOD_CHOICES:
        count = moods.filter(mood=mood_code).count()
        if count > 0:
            mood_counts[mood_code] = {
                'count': count,
                'percentage': round((count / moods.count()) * 100, 1) if moods.count() > 0 else 0,
                'emoji': Mood.MOOD_EMOJIS.get(mood_code, '😐'),
                'color': Mood.MOOD_COLORS.get(mood_code, '#6b7280'),
                'name': dict(Mood.MOOD_CHOICES).get(mood_code, mood_code)
            }
    
    # Get last 7 days for trend
    for i in range(7):
        day = end_date - timedelta(days=i)
        day_mood = moods.filter(date=day).first()
        daily_moods.append({
            'date': day.strftime('%a'),
            'mood': day_mood.mood if day_mood else None,
            'emoji': Mood.MOOD_EMOJIS.get(day_mood.mood, '❌') if day_mood else '❌',
        })
    
    return {
        'total_logs': moods.count(),
        'mood_counts': mood_counts,
        'daily_moods': daily_moods,
        'most_common': max(mood_counts.items(), key=lambda x: x[1]['count'])[0] if mood_counts else None,
    }



def trades_view(request):

    trades = Trades.objects.filter(target__in=[0, 1]).order_by("-timestamp")[:12]
    
    return render(request, "trade/trades.html",{
    'trades':trades,
        })

from .market_session import is_market_open, get_trading_session

from .market_session import is_market_open, get_trading_session, get_market_volatility, get_major_news_impact

def home_view(request):
    import pytz
    eat = pytz.timezone('Africa/Dar_es_Salaam')
    now_eat = timezone.now().astimezone(eat)
    current_time_local = now_eat.strftime('%I:%M %p')
    current_date_local = now_eat.strftime('%A, %B %d, %Y')
    
    # Get all-time stats
    all_time_stats = get_all_time_stats()
    
    # Get last 7 days activity
    weekly_activity = get_recent_activity(days=7)
    
    # Get last 30 days activity
    monthly_activity = get_recent_activity(days=30)
    
    today_data = get_today_trading_data()
    yesterday_data = get_yesterday_trading_data()
    stats = calculate_overall_stats()

    # Get losing reasons analysis
    analysis = analyze_losing_reasons()
    
    # Extract values from analysis
    most_common_reason = analysis['most_common_reason']
    most_common_count = analysis['most_common_count']
    most_common_percentage = analysis['most_common_percentage']
    message = analysis['message']
    reason_breakdown = analysis['reason_breakdown']
    
    # Get market session information
    market_info = is_market_open()
    trading_session_data = get_trading_session()
    market_volatility = get_market_volatility()
    news_impact = get_major_news_impact()
    
    # Get session pairs and recommendations
    session_pairs_data = get_session_pairs()
    pair_recommendations = get_pair_recommendations()
    
    # Get comprehensive performance analysis
    issues, severity = Advice.analyze_performance(stats)
    advice = Advice.get_performance_based_advice(stats)
    
    # Severity mapping for display
    severity_display_map = {
        'critical': '🔴 Critical Issues',
        'serious': '🟠 Serious Issues',
        'poor': '🟡 Needs Improvement',
        'below_average': '🔵 Below Average',
        'good': '🟢 Good Performance',
        'excellent': '🌟 Excellent Performance',
    }
    severity_display = severity_display_map.get(severity, '⚪ Average')
    
    # Format market data for template
    market_open = market_info['is_open']
    current_session = trading_session_data['name']
    session_icon = trading_session_data['icon']
    session_description = trading_session_data['description']
    session_volatility = trading_session_data['volatility']
    
    # Extract active pairs and best pairs from trading_session_data
    active_pairs = trading_session_data.get('active_pairs', [])
    best_pairs = trading_session_data.get('best_pairs', [])
    
    # Calculate next session
    next_session = trading_session_data.get('next_session', 'Unknown')
    next_session_time = trading_session_data.get('next_session_time', '')
    time_until_next = trading_session_data.get('time_until_next', '')
    
    # ===== MOOD TRACKING INTEGRATION =====
    # Check if user already selected mood today
    today = timezone.now().date()
    today_mood = None
    mood_streak = 0
    mood_achievements = []
    tomorrow_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    
    if request.user.is_authenticated:
        today_mood = Mood.objects.filter(user=request.user, date=today).first()
        mood_streak = get_mood_streak(request.user)
        mood_achievements = get_mood_achievements(request.user)
    
    # Get mood statistics for charts (last 30 days)
    mood_stats = get_mood_stats_for_dashboard(request.user) if request.user.is_authenticated else {}
    
    # DEBUG: Print to console
    est = pytz.timezone('US/Eastern')
    now_est = timezone.now().astimezone(est)
    

    
    return render(request, 'trade/home.html', {
        # Trading session & market info
        'trading_session': current_session,
        'market_open': market_open,
        'session_icon': session_icon,
        'session_description': session_description,
        'session_volatility': session_volatility,
        'next_session': next_session,
        'next_session_time': next_session_time,
        'time_until_next': time_until_next,
        'market_info': market_info,
        'market_volatility': market_volatility,
        'news_impact': news_impact,
        
        # Session pairs data
        'session_pairs': trading_session_data,
        'active_pairs': active_pairs,
        'best_pairs': best_pairs,
        'pair_recommendations': pair_recommendations,
        
        # Loss reason analysis
        'most_common_reason': most_common_reason,
        'most_common_count': most_common_count,
        'most_common_percentage': most_common_percentage,
        'reason_message': message,
        'reason_breakdown': reason_breakdown,
        
        # Daily performance
        'todays_profit': today_data['todays_profit'],
        'yesterday_profit': yesterday_data['yesterday_profit'],
        
        # Overall stats
        'overallwinrate': stats['overallwinrate'],
        'overalllossrate': stats['overalllossrate'],
        'total_trades': all_time_stats['total_trades'],
        'avg_risk_reward': stats['avg_risk_reward'],
        'std_dev_rr': stats.get('std_dev_rr', 0),
        'avg_rvs': stats.get('avg_rvs', 0),
        'expectancy': stats['expectancy'],
        
        # Best streak
        'best_streak': all_time_stats.get('longest_win_streak', 0),
        
        # All-time stats
        'all_time_stats': all_time_stats,
        
        # Activity
        'weekly_activity': weekly_activity,
        'monthly_activity': monthly_activity,
        
        # Performance analysis
        'issues': issues,
        'severity': severity,
        'severity_display': severity_display,
        
        # Advice
        'advice': advice,
        
        # Date and time
        'current_date': timezone.now().strftime('%A, %B %d, %Y'),
        'current_time_local': current_time_local,
        'current_date_local': current_date_local,
        'local_timezone': 'EAT',
        'tomorrow_date': tomorrow_date,
        
        # ===== MOOD TRACKING DATA =====
        'today_mood': today_mood,
        'mood_selected_today': today_mood is not None,
        'selected_mood': today_mood.mood if today_mood else None,
        'selected_mood_emoji': Mood.MOOD_EMOJIS.get(today_mood.mood, '😐') if today_mood else None,
        'selected_mood_color': Mood.MOOD_COLORS.get(today_mood.mood, '#6b7280') if today_mood else None,
        'mood_streak': mood_streak,
        'mood_achievements': mood_achievements,
        'mood_stats': mood_stats,
    })
def performance_by_pair_view(request, pair_id):

    pair = get_object_or_404(Pairs, id=pair_id)
    # Get next pair
    next_pair = Pairs.objects.filter(id__gt=pair.id).order_by("id").first()
    
    # Get previous pair
    previous_pair = Pairs.objects.filter(id__lt=pair.id).order_by("-id").first()
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
    
    #  last 20 winning trades with holding_time    
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
            "next_pair": next_pair,
            "previous_pair": previous_pair,
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
