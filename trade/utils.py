import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils.timezone import now, localtime
from django.db.models import Avg, Sum, Count, StdDev, Q, Case, When, Value, FloatField, Max, Min
from django.forms.models import model_to_dict
from collections import Counter
import os
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from .models import Trades, Pairs, Mood

# ---------------------------
# Model training / loading
# ---------------------------

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pkl")
MODEL = None
FEATURES = [
    "pair", "momentum_h4", "momentum_h1", "momentum_15m", "momentum_5m", "momentum_1m",
    "session", "entry_place", "buy_or_sell", "setup_quality",
    "trade_type", "confirmation", "mood", "tp", "tp_reason", "risk_reward"
]

def train_model():
    """Train the ML model on existing trades."""
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
    """Load or train the ML model."""
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
# Trade ID Generation
# ---------------------------

def generate_unique_trade_id():
    """Generate a unique 4-digit trade ID."""
    existing_ids = set(Trades.objects.values_list("trade_id", flat=True))
    while True:
        new_id = random.randint(1000, 9999)
        if new_id not in existing_ids:
            return new_id


# ---------------------------
# Data Normalization
# ---------------------------

def normalize_empty_fields(trade_instance):
    """Convert empty strings to None for all fields."""
    for field in Trades._meta.get_fields():
        if hasattr(trade_instance, field.name):
            value = getattr(trade_instance, field.name)
            if value == "":
                setattr(trade_instance, field.name, None)
    return trade_instance


# ---------------------------
# Prediction Helpers
# ---------------------------

def prepare_prediction_data(trade_instance, features):
    """
    Prepare data for model prediction.
    Properly handles data types to avoid sklearn encoding issues.
    """
    pred_data = {}
    
    for col in features:
        # Get the value and ensure it's a primitive type, not a dict
        value = getattr(trade_instance, col, "Blank")
        
        # Handle different data types
        if value is None:
            value = "Blank"
        elif isinstance(value, (dict, list)):
            value = str(value)  # Convert complex types to string
        elif not isinstance(value, (str, int, float, bool, np.number)):
            value = str(value)  # Convert any other non-primitive to string
        
        pred_data[col] = [value]
    
    pred_df = pd.DataFrame(pred_data)
    
    # Convert risk_reward to numeric safely
    if "risk_reward" in pred_df.columns:
        pred_df["risk_reward"] = pd.to_numeric(
            pred_df["risk_reward"], errors="coerce"
        ).fillna(0)
    
    # Convert all object columns to string to avoid encoding issues
    for col in pred_df.select_dtypes(include=['object']).columns:
        pred_df[col] = pred_df[col].astype(str)
    
    return pred_df


def calculate_trade_rating(probability):
    """Calculate trade rating based on win probability."""
    if probability >= 70:
        return "A"
    elif probability >= 60:
        return "B"
    elif probability >= 50:
        return "C"
    return "D"


def get_trade_preview_data(trade_instance, rvs_value, rvs_grade, probability=None, rating=None):
    """Prepare trade preview data for confirmation."""
    exclude_fields = {
        "id", "momentum_h4", "momentum_h1", "momentum_15m", "momentum_5m", 
        "momentum_1m", "rvs", "rvs_grade", "risk_reward", "trade_id", 
        "timestamp", "trade_type", "buy_or_sell", "session", "entry_place", 
        "confirmation", "mood", "tp", "tp_reason", "setup_quality", "target",
        "reason", "holding_time_hrs", "holding_time", "narration", "user"
    }
    
    preview_data = {}
    
    for field in Trades._meta.get_fields():
        if field.name not in exclude_fields:
            value = getattr(trade_instance, field.name, None)
            # Handle None values
            if value is None or value == "":
                display_value = "Not specified"
            else:
                display_value = value
            
            # Use field name or verbose_name
            field_label = getattr(field, 'verbose_name', field.name)
            preview_data[str(field_label).title()] = display_value
    
    preview_data["RVS"] = rvs_value if rvs_value is not None else 0
    preview_data["RVS Grade"] = rvs_grade if rvs_grade is not None else "N/A"
    
    if probability is not None:
        preview_data["Win Probability (%)"] = round(probability, 1)
        preview_data["Trade Rating"] = rating
    
    return preview_data


# ---------------------------
# RVS Calculation
# ---------------------------

def calculate_rvs(trade):
    """Calculate Rule Violation Score for a trade."""
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


# ---------------------------
# Statistics Functions
# ---------------------------

def calculate_overall_stats(trades_queryset):
    """Calculate overall statistics from trades queryset."""
    # Aggregate stats from last 20 trades
    last_20_trades = trades_queryset.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:30]
    last_2_trades = trades_queryset.filter(
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


def get_pairs_summary(trades_queryset):
    """Generate summary statistics for each trading pair."""
    pairs_summary = []
    pairs = Pairs.objects.all()

    for pair in pairs:
        trades = trades_queryset.filter(
            pair=pair,
            target__in=[0, 1]
        )
    
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


def analyze_losing_reasons(trades_queryset):
    """Analyze most common reasons for losing trades and generate advice."""
    # Get last 50 losing trades for better sample size
    losing_trades = trades_queryset.filter(target=0).order_by("-timestamp")[:50]
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
        'reason_breakdown': reason_breakdown,
        'unique_reasons': len(reason_counts),
    }


def get_today_trading_data(trades_queryset):
    """Get today's trading statistics."""
    local_now = localtime(now())
    today = local_now.date()
    
    todays_trades = trades_queryset.filter(timestamp__date=today).count()
    
    # Today's closed trades profit/loss
    todays_profit = trades_queryset.filter(
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


def get_yesterday_trading_data(trades_queryset):
    """Get yesterday's trading statistics."""
    local_now = localtime(now())
    yesterday = local_now.date() - timedelta(days=1)
    
    yesterday_trades = trades_queryset.filter(timestamp__date=yesterday).count()
    
    # Yesterday's closed trades profit/loss
    yesterday_profit = trades_queryset.filter(
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
    yesterday_wins = trades_queryset.filter(
        timestamp__date=yesterday,
        target=1
    ).count()
    
    yesterday_total = trades_queryset.filter(
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


def get_all_time_stats(trades_queryset):
    """Get all-time trading statistics."""
    # All closed trades
    all_trades = trades_queryset.filter(target__in=[0, 1])
    
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
            worst=Min("risk_reward")
        )["worst"] or 0, 2
    )
    
    # Get the actual biggest loss (lowest value)
    biggest_loss = round(
        all_trades.filter(target=0).aggregate(
            biggest=Min("risk_reward")
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
        pair_trades = trades_queryset.filter(pair=pair, target__in=[0, 1])
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


def get_recent_activity(trades_queryset, days=7):
    """Get trading activity for the last X days."""
    end_date = localtime(now()).date()
    start_date = end_date - timedelta(days=days)
    
    daily_stats = []
    
    for i in range(days):
        current_date = end_date - timedelta(days=i)
        day_trades = trades_queryset.filter(
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
    """Calculate trader consistency grade based on multiple factors."""
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


def prepare_chart_data(trades_queryset, trade_count=40):
    """Prepare data for performance chart."""
    last_trades = trades_queryset.filter(
        target__in=[0, 1]
    ).order_by("-timestamp")[:trade_count]
    
    # Reverse for chronological order
    trades_list = list(last_trades)[::-1]
    
    risk_rewards = [t.risk_reward for t in trades_list]
    targets = [t.target for t in trades_list]
    
    # Format dates
    dates = []
    for t in trades_list:
        try:
            dates.append(t.timestamp.strftime("%Y-%m-%d"))
        except ValueError:
            dates.append(t.timestamp.strftime("%Y-%m-%d"))
    
    # Build cumulative performance
    performance = []
    cum_value = 0
    for rr, t in zip(risk_rewards, targets):
        if t == 1:
            cum_value += rr
        else:
            cum_value -= 1
        performance.append(round(cum_value, 2))
    
    return {
        'performance': performance,
        'dates': dates,
        'risk_rewards': risk_rewards,
        'targets': targets,
    }


# ---------------------------
# Mood Tracking Functions
# ---------------------------

def get_mood_streak(user):
    """Calculate user's mood logging streak."""
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
    """Calculate mood logging achievements."""
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
    """Get mood statistics for dashboard charts."""
    end_date = now().date()
    start_date = end_date - timedelta(days=days)
    
    moods = Mood.objects.filter(
        user=user, 
        date__gte=start_date, 
        date__lte=end_date
    ).order_by('date')
    
    # Prepare data for charts
    mood_counts = {}
    daily_moods = []
    
    if moods.exists():
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