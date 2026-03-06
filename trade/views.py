import random
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from datetime import datetime, time, timedelta
from django.utils.timezone import localtime, now
from collections import Counter
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.forms.models import model_to_dict
from django.db.models import Avg, Sum, Count, StdDev, Q, Case, When, Value, FloatField, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import os
import json
import re

from .models import Trades, Pairs, Advice, Mood
from .services import restrict_trade
from .forms import NewTradeForm, TradeUpdateForm
from .market_session import (
    is_market_open, get_trading_session, get_market_volatility, 
    get_major_news_impact, get_session_pairs, get_pair_recommendations
)
from .utils import (
    # Model functions
    get_model, train_model,
    
    # Trade ID and data normalization
    generate_unique_trade_id, normalize_empty_fields,
    
    # Prediction helpers
    prepare_prediction_data, calculate_trade_rating, get_trade_preview_data,
    
    # RVS calculation
    calculate_rvs,
    
    # Statistics functions (all accept queryset parameter)
    calculate_overall_stats, get_pairs_summary, analyze_losing_reasons,
    get_today_trading_data, get_yesterday_trading_data, get_all_time_stats,
    get_recent_activity, calculate_consistency_grade, prepare_chart_data,
    
    # Mood tracking functions
    get_mood_streak, get_mood_achievements, get_mood_stats_for_dashboard
)


FEATURES = [
    "pair", "momentum_h4", "momentum_h1", "momentum_15m", "momentum_5m", "momentum_1m",
    "session", "entry_place", "buy_or_sell", "setup_quality",
    "trade_type", "confirmation", "mood", "tp", "tp_reason", "risk_reward"
]

# ---------------------------
# Authentication Views
# ---------------------------

def login_view(request):
    """Handle both login and registration"""
    
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('index')
    
    context = {}
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # ===== LOGIN HANDLING =====
        if action == 'login':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            
            # Validate inputs
            if not username or not password:
                messages.error(request, 'Please fill in all fields')
                return redirect('login')
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                
                # Redirect to next page if specified
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password')
        
        # ===== REGISTRATION HANDLING =====
        elif action == 'register':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            
            # Validation
            errors = []
            
            # Check if all fields are filled
            if not all([username, email, password1, password2]):
                errors.append('All fields are required')
            
            # Username validation
            if len(username) < 3:
                errors.append('Username must be at least 3 characters')
            elif not re.match('^[a-zA-Z0-9_]+$', username):
                errors.append('Username can only contain letters, numbers, and underscores')
            
            # Email validation
            if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append('Please enter a valid email address')
            
            # Password validation
            if len(password1) < 6:
                errors.append('Password must be at least 6 characters')
            
            if password1 != password2:
                errors.append('Passwords do not match')
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                errors.append('Username already taken')
            
            # Check if email exists
            if email and User.objects.filter(email=email).exists():
                errors.append('Email already registered')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('login')
            
            # Create user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                
                # Log the user in
                login(request, user)
                messages.success(request, f'Welcome to Trade Entry, {username}!')
                return redirect('home')
                
            except Exception as e:
                messages.error(request, 'An error occurred. Please try again.')
    
    return render(request, 'trade/login.html', context)


def logout_view(request):
    """Handle logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@login_required
def profile_view(request):
    """View and edit user profile"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            # Validate email
            if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                messages.error(request, 'Please enter a valid email address')
                return redirect('profile')
            
            # Update user
            user = request.user
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
        
        elif action == 'change_password':
            current = request.POST.get('current_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')
            
            # Verify current password
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect')
                return redirect('profile')
            
            # Validate new password
            if len(new1) < 6:
                messages.error(request, 'New password must be at least 6 characters')
                return redirect('profile')
            
            if new1 != new2:
                messages.error(request, 'New passwords do not match')
                return redirect('profile')
            
            # Change password
            request.user.set_password(new1)
            request.user.save()
            
            # Re-authenticate to keep user logged in
            user = authenticate(
                request, 
                username=request.user.username, 
                password=new1
            )
            login(request, user)
            
            messages.success(request, 'Password changed successfully')
            return redirect('profile')
    
    return render(request, 'trade/profile.html', {'user': request.user})


# ---------------------------
# Trade Management Views
# ---------------------------

def process_trade_submission(request, form, model):
    """Process the trade form submission."""
    new_trade = form.save(commit=False)
    
    # Assign trade to logged-in user
    new_trade.user = request.user
   
    try:
        with transaction.atomic():
            # Restrict trade before doing any heavy work
            restrict_trade(
                pair=new_trade.pair,
                new_trade_type=new_trade.trade_type
            )
            
            # Set basic trade info
            new_trade.trade_id = generate_unique_trade_id()
            new_trade.timestamp = datetime.now()
            
            if not new_trade.session:
                new_trade.session = get_trading_session()
            
            # Normalize empty fields to None
            new_trade = normalize_empty_fields(new_trade)
            
            # Calculate RVS
            new_trade = calculate_rvs(new_trade)
            
            # Initialize prediction variables
            probability = None
            rating = None
            
            # Make prediction if model exists
            if model:
                try:
                    pred_df = prepare_prediction_data(new_trade, FEATURES)
                    probability = model.predict_proba(pred_df)[0][1] * 100
                    rating = calculate_trade_rating(probability)
                except Exception as e:
                    print(f"Prediction error: {e}")
                    probability = None
                    rating = None
            
            # Prepare preview data
            preview_data = get_trade_preview_data(
                new_trade, 
                new_trade.rvs, 
                new_trade.rvs_grade,
                probability, 
                rating
            )
            
            # Check if user confirmed save
            if "confirm_save" in request.POST:
                new_trade.save()
                return redirect("journal")
            
            # Return preview for confirmation
            return render(request, "trade/trade.html", {
                "form": form,
                "show_confirm": True,
                "trade_preview": preview_data,
            })
            
    except ValidationError as e:
        form.add_error(None, e.message)
        return render(request, "trade/trade.html", {
            "form": form,
            "show_confirm": False,
        })


@login_required
def trade_view(request):
    """Main view for creating new trades."""
    model = get_model()
    
    if request.method == "POST":
        form = NewTradeForm(request.POST)
        
        if form.is_valid():
            return process_trade_submission(request, form, model)
    else:
        form = NewTradeForm()
        
    return render(request, "trade/trade.html", {
        "form": form,
        "show_confirm": False,
    })


@login_required
def journal_view(request):
    """View for open trades (target is null)."""
    # Filter by logged-in user
    trades = Trades.objects.filter(
        user=request.user,
        target__isnull=True
    ).order_by('-timestamp')

    return render(request, 'trade/journal.html', {
        'trades': trades,
    })


@login_required
def update_trade_view(request, trade_id):
    """Update an existing trade."""
    # Ensure user can only update their own trades
    trade = get_object_or_404(Trades, trade_id=trade_id, user=request.user)

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


@login_required
def delete_trade_view(request, trade_id):
    """Confirm trade deletion."""
    # Ensure user can only delete their own trades
    trade = get_object_or_404(Trades, trade_id=trade_id, user=request.user)
    return render(request, "trade/delete_trade_confirm.html", {
        "trade": trade
    })
    

@require_POST
@login_required
def delete_trade(request, trade_id):
    """Delete a trade."""
    # Ensure user can only delete their own trades
    trade = get_object_or_404(Trades, trade_id=trade_id, user=request.user)
    trade.delete()
    return redirect("journal")


@login_required
def trades_view(request):
    """View for closed trades (target is not null)."""
    # Filter by logged-in user
    trades = Trades.objects.filter(
        user=request.user,
        target__in=[0, 1]
    ).order_by("-timestamp")[:12]
    
    return render(request, "trade/trades.html", {
        'trades': trades,
    })


# ---------------------------
# Performance Views
# ---------------------------

@login_required
def performance_view(request):
    """Performance dashboard - user specific."""
    # Filter all queries by logged-in user
    user_trades = Trades.objects.filter(user=request.user)
    
    # If no trades yet, show empty dashboard
    if not user_trades.exists():
        return render(request, 'trade/performance.html', {
            'grade_consistency': {"consistency_score": 0, "consistency_max": 4, 
                                 "consistency_level": 1, "consistency_tier": "Low", 
                                 "consistency_percent": 0},
            'expectancy': 0,
            'avg_rvs': 0,
            'avg_risk_reward': 0,
            "pairs_summary": [],
            'most_common_reason': None,
            'most_common_count': 0,
            'most_common_percentage': 0,
            'message': "No trades yet. Start trading to see performance data!",
            'reason_breakdown': [],
            'total_losing_analyzed': 0,
            'unique_reasons': 0,
            "overallwinrate": 0,
            "overalllossrate": 0,
            'todays_trades': 0,
            'todays_profit': 0,
            'std_dev_rr': 0,
            'performance': [],
            'dates': [],
        })
    
    # Calculate overall statistics (user-specific)
    stats = calculate_overall_stats(user_trades)
    
    # Get pairs summary (user-specific)
    pairs_summary = get_pairs_summary(user_trades)
    
    # Analyze losing reasons (user-specific)
    analysis = analyze_losing_reasons(user_trades)
    
    # Extract values from analysis
    most_common_reason = analysis['most_common_reason']
    most_common_count = analysis['most_common_count']
    most_common_percentage = analysis['most_common_percentage']
    message = analysis['message']
    reason_breakdown = analysis['reason_breakdown']
    total_losing_analyzed = analysis['total_losing_analyzed']
    unique_reasons = analysis['unique_reasons']
    
    # Get today's trading data (user-specific)
    today_data = get_today_trading_data(user_trades)
    
    # Calculate consistency grade (user-specific)
    grade_consistency = calculate_consistency_grade(
        today_data['todays_trades'],
        stats['avg_rvs'],
        stats['std_dev_rr'],
        most_common_reason
    )
    
    # Prepare performance chart data (user-specific)
    chart_data = prepare_chart_data(user_trades)
    
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


@login_required
def performance_by_pair_view(request, pair_id):
    """Performance for a specific pair - user specific."""
    pair = get_object_or_404(Pairs, id=pair_id)
    
    # Filter trades by both pair AND user
    user_trades = Trades.objects.filter(user=request.user)
    
    # Get next pair (user doesn't matter for pair navigation)
    next_pair = Pairs.objects.filter(id__gt=pair.id).order_by("id").first()
    previous_pair = Pairs.objects.filter(id__lt=pair.id).order_by("-id").first()
    
    # Get trades for this pair and user
    trades = list(user_trades.filter(
        pair=pair,
        target__isnull=False
    ).order_by("timestamp")[:40])
    
    if not trades:
        # No trades for this pair yet
        return render(
            request,
            "trade/performance_by_pair.html",
            {
                "next_pair": next_pair,
                "previous_pair": previous_pair,
                "max_wins": 0,
                "max_losses": 0,
                "average_holding_time": "",
                "best_entry_place": "N/A",
                "best_trade_type": "N/A",
                "most_winning_session": "N/A",
                "pair": pair,
                "dates": [],
                "performance": [],
            }
        )
    
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
    
    # Get last 20 trades for this pair and user
    recent_trades = user_trades.filter(
        pair=pair,
        target__isnull=False
    ).order_by("-timestamp")[:20]
    
    # --- categorical stats ---
    session = recent_trades.values_list("session", flat=True)
    trade_type = recent_trades.values_list("trade_type", flat=True)
    entry_place = recent_trades.values_list("entry_place", flat=True)

    # --- average holding time (minutes) ---
    average_minutes = recent_trades.aggregate(
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
    
    def get_max_streaks(trades):
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        for trade in trades:
            if trade.target == 1:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.target == 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        return max_wins, max_losses
    
    max_wins, max_losses = get_max_streaks(recent_trades)

    return render(
        request,
        "trade/performance_by_pair.html",
        {
            "next_pair": next_pair,
            "previous_pair": previous_pair,
            "max_wins": max_wins,
            "max_losses": max_losses,
            "average_holding_time": average_holding_time,
            "best_entry_place": best_entry_place,
            "best_trade_type": best_trade_type,
            "most_winning_session": most_winning_session,
            "pair": pair,
            "dates": dates,
            "performance": performance,
        }
    )


# ---------------------------
# Home Dashboard View
# ---------------------------

@login_required
def home_view(request):
    """Home dashboard - user specific."""
    import pytz
    eat = pytz.timezone('Africa/Dar_es_Salaam')
    now_eat = timezone.now().astimezone(eat)
    current_time_local = now_eat.strftime('%I:%M %p')
    current_date_local = now_eat.strftime('%A, %B %d, %Y')
    
    # Filter all trade queries by logged-in user
    user_trades = Trades.objects.filter(user=request.user)
    
    # Get all-time stats (user-specific)
    all_time_stats = get_all_time_stats(user_trades)
    
    # Get last 7 days activity (user-specific)
    weekly_activity = get_recent_activity(user_trades, days=7)
    
    # Get last 30 days activity (user-specific)
    monthly_activity = get_recent_activity(user_trades, days=30)
    
    today_data = get_today_trading_data(user_trades)
    yesterday_data = get_yesterday_trading_data(user_trades)
    stats = calculate_overall_stats(user_trades)

    # Get losing reasons analysis (user-specific)
    analysis = analyze_losing_reasons(user_trades)
    
    # Extract values from analysis
    most_common_reason = analysis['most_common_reason']
    most_common_count = analysis['most_common_count']
    most_common_percentage = analysis['most_common_percentage']
    message = analysis['message']
    reason_breakdown = analysis['reason_breakdown']
    
    # Get market session information (not user-specific - global market data)
    market_info = is_market_open()
    trading_session_data = get_trading_session()
    market_volatility = get_market_volatility()
    news_impact = get_major_news_impact()
    
    # Get session pairs and recommendations (not user-specific)
    session_pairs_data = get_session_pairs()
    pair_recommendations = get_pair_recommendations()
    
    # Get comprehensive performance analysis (user-specific)
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
    
    # Get mood statistics for charts (last 30 days) - user-specific
    mood_stats = get_mood_stats_for_dashboard(request.user) if request.user.is_authenticated else {}
    
    return render(request, 'trade/home.html', {
        'user': request.user,
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


# ---------------------------
# Mood Tracking Views
# ---------------------------

@login_required
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
            
            # Get today's trades for this user
            today_trades = Trades.objects.filter(
                timestamp__date=today,
                user=request.user
            )
            
            # Calculate daily profit (simple version)
            profit_loss = 0
            for trade in today_trades.filter(target__in=[0, 1]):
                if trade.target == 1:
                    profit_loss += trade.risk_reward or 0
                else:
                    profit_loss -= 1
            
            # Update mood with trading data (optional)
            existing_mood.trades_count = today_trades.count()
            existing_mood.profit_loss = round(profit_loss, 2)
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

@login_required
def get_mood_stats(request):
    """Get mood statistics for charts - user specific."""
    days = int(request.GET.get('days', 30))
    
    # Get moods for the current user only
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Filter moods for current user within date range
    user_moods = Mood.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Calculate stats manually instead of calling class method
    total = user_moods.count()
    stats = {}
    
    if total > 0:
        for mood_code, mood_name in Mood.MOOD_CHOICES:
            count = user_moods.filter(mood=mood_code).count()
            if count > 0:
                # Extract just the emoji from the choice if needed
                # mood_name might be "😊 Confident", so we need to clean it
                clean_name = mood_name.split(' ')[-1] if ' ' in mood_name else mood_name
                
                stats[mood_code] = {
                    'name': clean_name,
                    'count': count,
                    'percentage': round((count / total) * 100, 1),
                    'emoji': Mood.MOOD_EMOJIS.get(mood_code, '😐'),
                    'color': Mood.MOOD_COLORS.get(mood_code, '#6b7280'),
                }
    
    # Get today's mood
    today_mood = Mood.get_today_mood(request.user)
    
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
    
    # Get streak
    streak = 0
    if request.user.is_authenticated:
        streak = get_mood_streak(request.user)  # Make sure this function is imported
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'chart_data': chart_data,
        'streak': streak,
        'today_mood': {
            'mood': today_mood.mood if today_mood else None,
            'emoji': Mood.MOOD_EMOJIS.get(today_mood.mood, '') if today_mood else '',
            'name': today_mood.get_mood_display() if today_mood else None,
        } if today_mood else None
    })

# ---------------------------
# Export Views
# ---------------------------

@login_required
def export_trades_to_excel(request):
    """
    Export user's trades to Excel file.
    """
    # Fetch only current user's trades
    trades_qs = Trades.objects.filter(user=request.user)
    
    if not trades_qs.exists():
        messages.error(request, 'No trades to export')
        return redirect('trades_view')
    
    # Convert queryset to list of dicts
    trades_list = list(trades_qs.values())
    
    # Convert timezone-aware datetimes to naive
    for trade in trades_list:
        for key, value in trade.items():
            if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                trade[key] = localtime(value).replace(tzinfo=None)
    
    # Convert to DataFrame
    df = pd.DataFrame(trades_list)
    
    # Remove unwanted columns
    exclude_cols = ['id', 'user_id']  # Don't need user_id in export
    df = df[[col for col in df.columns if col not in exclude_cols]]
    
    # Prepare Excel response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="trades_{request.user.username}_{timezone.now().date()}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
    
    return response


# ---------------------------
# API Views
# ---------------------------

@require_GET
@login_required
def performance_overview(request):
    """
    Returns overall performance metrics for dashboard - user specific.
    """
    user_trades = Trades.objects.filter(user=request.user)
    stats = calculate_overall_stats(user_trades)
    
    data = {
        "winrate": stats.get('overallwinrate', 0),
        "lossrate": stats.get('overalllossrate', 0),
        "expectancy": stats.get('expectancy', 0),
        "avg_rr": stats.get('avg_risk_reward', 0),
        "avg_risk": -1.0,
        "rvs": stats.get('avg_rvs', 0),
    }

    return JsonResponse(data)


# ---------------------------
# Academy Views
# ---------------------------

@login_required
def academy_view(request):
    """Academy page."""
    return render(request, 'trade/academy/academy.html', {})


# ---------------------------
# Test Views
# ---------------------------

def p(request):
    """Test page."""
    return render(request, 'trade/p.html', {})