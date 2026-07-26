import random
from django.db import transaction
from django.core.exceptions import ValidationError

from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
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

@ensure_csrf_cookie
@csrf_protect
def login_view(request):
    """Handle both login and registration"""
    
    # Redirect if already logged in #
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
            
            if not all([username, email, password1, password2]):
                errors.append('All fields are required')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters')
            elif not re.match('^[a-zA-Z0-9_]+$', username):
                errors.append('Username can only contain letters, numbers, and underscores')
            elif email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append('Please enter a valid email address')
            elif len(password1) < 4:
                errors.append('Password must be at least 4 characters')
            elif password1 != password2:
                errors.append('Passwords do not match')
            elif User.objects.filter(username=username).exists():
                errors.append('Username already taken')
            elif email and User.objects.filter(email=email).exists():
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
                messages.success(request, f'Welcome to Forex Home, {username}!')
                return redirect('home')
                
            except Exception:
                messages.error(request, 'Registration failed. Please try again.')
                return redirect('login')
    
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
    
    # Check if this should be a draft
    is_draft = form.cleaned_data.get('draft', False)
    
    # Get draft_id from form or POST
    draft_id = request.POST.get('draft_id') or getattr(form, 'draft_id', None)
    
    # Check if we're editing an existing draft
    existing_draft = None
    if draft_id:
        try:
            existing_draft = Trades.objects.get(
                id=draft_id,
                user=request.user,
                is_draft=True
            )
            print(f"📝 Editing existing draft #{existing_draft.trade_id}")
        except Trades.DoesNotExist:
            pass
    
    try:
        with transaction.atomic():
            # For drafts, skip restrictions
            # For new trades, apply restrictions but exclude the draft being edited
            if not is_draft and not existing_draft:
                
                restrict_trade(
                    request,
                    pair=new_trade.pair,
                    new_trade_type=new_trade.trade_type,
                    exclude_draft_id=draft_id
                )
           
            
               
            
            # Set basic trade info
            if existing_draft:
                # Use existing draft's trade_id and timestamps
                new_trade.trade_id = existing_draft.trade_id
                new_trade.id = existing_draft.id
                new_trade.timestamp = existing_draft.timestamp
                new_trade.draft_created_at = existing_draft.draft_created_at
                new_trade.draft_updated_at = timezone.now()

            else:
                new_trade.trade_id = generate_unique_trade_id()
                new_trade.timestamp = timezone.now()
                new_trade.draft_created_at = timezone.now() if is_draft else None
                new_trade.draft_updated_at = timezone.now() if is_draft else None
               
            
            if not new_trade.session:
                try:
                    session_data = get_trading_session()
                    new_trade.session = session_data.get('name', 'Unknown Session')
                except Exception as e:

                    new_trade.session = 'Unknown Session'
              
            
            # Normalize empty fields to None
            new_trade = normalize_empty_fields(new_trade)
            
            # Calculate RVS
            new_trade = calculate_rvs(new_trade)

            
            # Initialize prediction variables
            probability = None
            rating = None
            
            # Make prediction if model exists and not a draft
            if model and not is_draft and not existing_draft:
                try:
                    pred_df = prepare_prediction_data(new_trade, FEATURES)
                    probability = model.predict_proba(pred_df)[0][1] * 100
                    rating = calculate_trade_rating(probability)

                except Exception as e:

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
            
            # Check if user confirmed save or wants to save as draft
            if "confirm_save" in request.POST:

                
                # IMPORTANT: Remove draft flag and save
                new_trade.is_draft = False
                new_trade.draft_created_at = None
                new_trade.draft_updated_at = None
                
                # If this was a draft being confirmed, we're updating it
                if existing_draft:

                    # Update the existing record
                    existing_draft.is_draft = False
                    existing_draft.draft_created_at = None
                    existing_draft.draft_updated_at = None
                    
                    # Copy all form data to existing draft
                    for field in form.cleaned_data:
                        if field not in ['draft', 'draft_id']:
                            setattr(existing_draft, field, form.cleaned_data[field])
                    
                    # Recalculate RVS with updated data
                    existing_draft = calculate_rvs(existing_draft)
                    existing_draft.save()
                    
                    messages.success(request, f"✅ Trade #{existing_draft.trade_id} confirmed from draft!")
                    return redirect("journal")
                else:
                    # New trade
                    new_trade.save()
                    messages.success(request, f"✅ Trade #{new_trade.trade_id} saved successfully!")
                    return redirect("journal")
            
            elif "save_draft" in request.POST:

                # Save as draft
                new_trade.is_draft = True
                if not new_trade.draft_created_at:
                    new_trade.draft_created_at = timezone.now()
                new_trade.draft_updated_at = timezone.now()
                # Set target to None since it's not completed
                new_trade.target = None
                
                if existing_draft:
                    # Update existing draft
                    for field in form.cleaned_data:
                        if field not in ['draft', 'draft_id']:
                            setattr(existing_draft, field, form.cleaned_data[field])
                    existing_draft.is_draft = True
                    existing_draft.draft_updated_at = timezone.now()
                    existing_draft.target = None
                    existing_draft = calculate_rvs(existing_draft)
                    existing_draft.save()
                    messages.success(request, f"📝 Draft #{existing_draft.trade_id} updated successfully!")
                else:
                    new_trade.save()
                    messages.success(request, f"📝 Trade #{new_trade.trade_id} saved as draft!")
                return redirect("drafts")
            
            # Return preview for confirmation

            return render(request, "trade/trade.html", {
                "form": form,
                "show_confirm": True,
                "trade_preview": preview_data,
                "probability": probability,
                "rating": rating,
                "is_draft": is_draft,
                "is_editing_draft": bool(existing_draft),
                "draft_id": existing_draft.id if existing_draft else None,
                "draft_trade_id": existing_draft.trade_id if existing_draft else None,
            })
            
    except ValidationError as e:

        form.add_error(None, e.message)
        return render(request, "trade/trade.html", {
            "form": form,
            "show_confirm": False,
            "is_editing_draft": bool(existing_draft),
            "draft_id": draft_id,
        })
    except Exception as e:
        # Catch any unexpected error and log it

        import traceback
        traceback.print_exc()
        
        # Add error to form
        form.add_error(None, f"An unexpected error occurred: {str(e)}")
        return render(request, "trade/trade.html", {
            "form": form,
            "show_confirm": False,
            "is_editing_draft": bool(existing_draft),
            "draft_id": draft_id,
        })

@login_required
def drafts_view(request):
    """View for draft trades."""
    drafts = Trades.objects.filter(
        user=request.user,
        is_draft=True
    ).order_by('-draft_updated_at')
    
    # Calculate draft age for display
    for draft in drafts:
        if draft.draft_created_at:
            days = (timezone.now() - draft.draft_created_at).days
            if days == 0:
                draft.age_display = "Today"
            elif days == 1:
                draft.age_display = "Yesterday"
            else:
                draft.age_display = f"{days} days ago"
        else:
            draft.age_display = "Recently"
    
    return render(request, 'trade/drafts.html', {
        'drafts': drafts,
        'draft_count': drafts.count(),
    })

@login_required
def delete_draft_confirm(request, draft_id):
    """Confirm draft deletion."""
    draft = get_object_or_404(Trades, id=draft_id, user=request.user, is_draft=True)
    return render(request, "trade/delete_draft_confirm.html", {
        "draft": draft
    })

@require_POST
@login_required
def delete_draft(request, draft_id):
    """Delete a draft."""
    draft = get_object_or_404(Trades, id=draft_id, user=request.user, is_draft=True)
    trade_id = draft.trade_id
    draft.delete()
    messages.success(request, f"Draft #{trade_id} deleted successfully.")
    return redirect("drafts")


@login_required
def complete_draft(request, draft_id):
    """
    Complete a draft trade - saves it to the journal immediately
    like the Confirm Trade button in the preview modal.
    """
    # Get the draft
    draft = get_object_or_404(Trades, id=draft_id, user=request.user, is_draft=True)
    
    try:
        with transaction.atomic():
            # Check trade restrictions
            restrict_trade(
                request,
                pair=draft.pair,
                new_trade_type=draft.trade_type
            )
            
            # Mark as not a draft
            draft.is_draft = False
            
            # Set timestamp if not set
            if not draft.timestamp:
                draft.timestamp = datetime.now()
            
            # Set target to None if not set (user will journal it later)
            if draft.target is None:
                draft.target = None
            
            # Save the trade
            draft.save()
            
            messages.success(request, f"Trade #{draft.trade_id} confirmed successfully! 🎉")
            
            # Redirect to journal to journal the trade
            return redirect('journal')
            
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('drafts')
    except Exception as e:
        messages.error(request, f"Error completing trade: {str(e)}")
        return redirect('drafts')
        
               
@login_required
def trade_view(request):
    """Main view for creating new trades."""
    model = get_model()
    
    if request.method == "POST":
       
        
        form = NewTradeForm(request.POST)
        
        # Store draft_id in form for processing
        draft_id = request.POST.get('draft_id')
        if draft_id:
            form.draft_id = draft_id
        
        if form.is_valid():
            return process_trade_submission(request, form, model)
        else:
            # Form invalid - show errors
            print(f"❌ Form errors: {form.errors}")
            return render(request, "trade/trade.html", {
                "form": form,
                "show_confirm": False,
                "is_editing_draft": bool(draft_id),
                "draft_id": draft_id,
            })
    else:
        # GET request - check if editing a draft
        draft_id = request.GET.get('draft_id')
        if draft_id:
            try:
                draft = Trades.objects.get(
                    id=draft_id, 
                    user=request.user, 
                    is_draft=True
                )
                # Pre-populate form with draft data
                form = NewTradeForm(instance=draft)
                
                # Add the draft_id to the form
                form.draft_id = draft_id
                
                return render(request, "trade/trade.html", {
                    "form": form,
                    "show_confirm": False,
                    "is_editing_draft": True,
                    "draft_id": draft_id,
                    "draft": draft,  # Pass full draft for display
                    "draft_trade_id": draft.trade_id,
                })
            except Trades.DoesNotExist:
                messages.error(request, "Draft not found.")
                return redirect('drafts')
        
        form = NewTradeForm()
        
    return render(request, "trade/trade.html", {
        "form": form,
        "show_confirm": False,
        "is_editing_draft": False,
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
    # Filter by logged-in user and prefetch account data to avoid N+1 queries
    trades = Trades.objects.filter(
        user=request.user,
        target__in=[0, 1]
    ).select_related('account').order_by("-timestamp")[:12]
    
    # Enhance trades with account info and calculated values for display
    enhanced_trades = []
    for trade in trades:
        # Safely access account info
        account_name = trade.account.account_name if trade.account else "N/A"
        account_balance = trade.account.account_balance if trade.account else None
        
        # Safely access calculator fields
        lot_size_display = None
        if trade.calculated_lot_size:
            if trade.calculated_lot_size >= 1:
                lot_size_display = f"{trade.calculated_lot_size} 📊"  # Standard lots
            elif trade.calculated_lot_size >= 0.1:
                lot_size_display = f"{trade.calculated_lot_size} 📈"  # Mini lots
            else:
                lot_size_display = f"{trade.calculated_lot_size} 📉"  # Micro lots
        
        # Add enhanced data to trade object
        trade.account_name = account_name
        trade.account_balance_display = f"${account_balance:,.2f}" if account_balance else None
        trade.lot_size_display = lot_size_display
        trade.risk_info = None
        
        if trade.risk_percent and trade.stop_loss_pips:
            trade.risk_info = f"{trade.risk_percent}% / {trade.stop_loss_pips} pips"
        
        enhanced_trades.append(trade)
    
    return render(request, "trade/trades.html", {
        'trades': enhanced_trades,
    })

# ---------------------------
# Performance Views
# ---------------------------
@login_required
def performance_view(request):
    """Performance dashboard - user specific."""
    # Filter all queries by logged-in user
    user_trades = Trades.objects.filter(user=request.user)
    
    # Check if user has any trades
    has_trades = user_trades.exists()
    total_user_trades = user_trades.filter(target__in=[0, 1]).count()
    
    # If no trades yet, show empty/welcome dashboard
    if total_user_trades == 0:
        return render(request, 'trade/performance.html', {
            'grade_consistency': {
                "consistency_score": 0, 
                "consistency_max": 4, 
                "consistency_level": 0, 
                "consistency_tier": "--", 
                "consistency_percent": 0
            },
            'expectancy': 0,
            'avg_rvs': 0,
            'avg_risk_reward': 0,
            "pairs_summary": [],
            'most_common_reason': None,
            'most_common_count': 0,
            'most_common_percentage': 0,
            'message': "Welcome to Forex Home! Start logging your trades to see your performance data.",
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
            'total_trades': 0,
            'has_trades': False,
            'total_user_trades': 0,
        })
    
    # Calculate overall statistics (user-specific) - ALWAYS calculate, even with few trades
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
    
    # ===== SHOW ALL METRICS FROM FIRST TRADE =====
    # Calculate consistency grade regardless of trade count
    # But use a more lenient message for new users
    if total_user_trades < 5:
        grade_consistency = calculate_consistency_grade(
            today_data['todays_trades'],
            stats['avg_rvs'],
            stats['std_dev_rr'],
            most_common_reason
        )
        # Override the tier to show "Building data" instead of "Low"
        grade_consistency['consistency_tier'] = f"Building ({total_user_trades}/5 trades)"
        grade_consistency['consistency_level'] = 1
        grade_consistency['consistency_percent'] = int((total_user_trades / 5) * 20)  # 20% per trade up to 100%
    else:
        grade_consistency = calculate_consistency_grade(
            today_data['todays_trades'],
            stats['avg_rvs'],
            stats['std_dev_rr'],
            most_common_reason
        )
    
    # ALWAYS show real metrics, even with few trades
    expectancy = stats['expectancy']
    avg_rvs = stats['avg_rvs']
    avg_risk_reward = stats['avg_risk_reward']
    overallwinrate = stats['overallwinrate']
    overalllossrate = stats['overalllossrate']
    std_dev_rr = stats['std_dev_rr']
    
    # Prepare performance chart data (user-specific)
    chart_data = prepare_chart_data(user_trades)
    
    return render(request, 'trade/performance.html', {
        # Consistency grade (shows building message for <5 trades)
        'grade_consistency': grade_consistency,
        
        # Core metrics - ALWAYS show real values
        'expectancy': expectancy,
        'avg_rvs': avg_rvs,
        'avg_risk_reward': avg_risk_reward,
        "pairs_summary": pairs_summary,
        
        # Loss reason analysis data
        'most_common_reason': most_common_reason,
        'most_common_count': most_common_count,
        'most_common_percentage': most_common_percentage,
        'message': message,
        'reason_breakdown': reason_breakdown,
        'total_losing_analyzed': total_losing_analyzed,
        'unique_reasons': unique_reasons,
        
        # Performance stats - ALWAYS show real values
        "overallwinrate": overallwinrate,
        "overalllossrate": overalllossrate,
        'todays_trades': today_data['todays_trades'],
        'todays_profit': today_data['todays_profit'],
        'std_dev_rr': std_dev_rr,
        
        # Chart data
        'performance': chart_data['performance'],
        'dates': chart_data['dates'],
        
        # Additional context for template
        'total_trades': total_user_trades,
        'has_trades': has_trades,
        'total_user_trades': total_user_trades,
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
    
    # Get all trades for this pair and user (remove limit for accurate stats)
    all_pair_trades = user_trades.filter(
        pair=pair,
        target__isnull=False
    ).order_by("timestamp")
    
    # Calculate overall statistics
    total_trades = all_pair_trades.count()
    
    if total_trades == 0:
        # No trades for this pair yet
        return render(
            request,
            "trade/performance_by_pair.html",
            {
                "next_pair": next_pair,
                "previous_pair": previous_pair,
                "pair": pair,
                "total_trades": 0,
                "winrate": 0,
                "pnl": 0,
                "avg_risk_reward": 0,
                "expectancy": 0,
                "common_losing_reason": "N/A",
                "losing_reason_count": 0,
                "max_wins": 0,
                "max_losses": 0,
                "average_holding_time": "",
                "best_entry_place": "N/A",
                "best_trade_type": "N/A",
                "most_winning_session": "N/A",
                "dates": [],
                "performance": [],
            }
        )
    
    # Calculate winrate
    winning_trades = all_pair_trades.filter(target=1).count()
    winrate = round((winning_trades / total_trades) * 100, 2)
    
    # Calculate P&L (cumulative risk_reward sum where wins add RR, losses subtract 1)
    pnl = 0
    total_rr_sum = 0
    for trade in all_pair_trades:
        if trade.target == 1:
            pnl += trade.risk_reward
            total_rr_sum += trade.risk_reward
        else:  # target == 0 (loss)
            pnl -= 1
    pnl = round(pnl, 2)
    
    # Calculate average risk reward (using all trades)
    avg_risk_reward = round(total_rr_sum / total_trades, 2)
    
    # Calculate expectancy
    # Expectancy = (Win Rate × Average Win) - (Loss Rate × Average Loss)
    # Average loss is always 1R (since losses subtract 1)
    loss_rate = 1 - (winning_trades / total_trades)
    avg_win = total_rr_sum / winning_trades if winning_trades > 0 else 0
    expectancy = round((winrate/100 * avg_win) - (loss_rate * 1), 2)
    
    # Find common losing reasons
    losing_trades = all_pair_trades.filter(target=0)
    losing_reasons = losing_trades.values_list("reason", flat=True).exclude(reason__isnull=True).exclude(reason__exact='')
    
    if losing_reasons:
        reason_counter = Counter(losing_reasons)
        common_reason = reason_counter.most_common(1)[0]
        common_losing_reason = common_reason[0]
        losing_reason_count = common_reason[1]
    else:
        common_losing_reason = "N/A"
        losing_reason_count = 0
    
    # Prepare lists for chart data (last 40 trades for performance chart)
    recent_for_chart = list(all_pair_trades[:40])
    
    risk_rewards = [t.risk_reward for t in recent_for_chart]
    targets = [t.target for t in recent_for_chart]
    dates = [t.timestamp.strftime("%Y-%m-%d") for t in recent_for_chart]
    
    # Build cumulative performance in chronological order
    performance = []
    cum_value = 0
    
    for rr, t in zip(risk_rewards, targets):
        if t == 1:
            cum_value += rr
        elif t == 0:
            cum_value -= 1
        performance.append(round(cum_value, 2))
    
    # Get last 20 trades for this pair and user for categorical stats
    recent_trades = all_pair_trades.order_by("-timestamp")[:20]
    
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
            "pair": pair,
            # Core metrics
            "total_trades": total_trades,
            "winrate": winrate,
            "pnl": pnl,
            "avg_risk_reward": avg_risk_reward,
            "expectancy": expectancy,
            "common_losing_reason": common_losing_reason,
            "losing_reason_count": losing_reason_count,
            "total_losses": losing_trades.count(),
            # Existing metrics
            "max_wins": max_wins,
            "max_losses": max_losses,
            "average_holding_time": average_holding_time,
            "best_entry_place": best_entry_place,
            "best_trade_type": best_trade_type,
            "most_winning_session": most_winning_session,
            "dates": dates,
            "performance": performance,
        }
    )


# ---------------------------
# Home Dashboard View
# ---------------------------

def test_view(request):
    """Test view to debug session issues"""
    try:
        from .market_session import get_trading_session, is_market_open
        
        session_data = get_trading_session()
        market_info = is_market_open()
        
        return render(request, 'trade/test.html', {
            'session_data': session_data,
            'market_info': market_info,
            'success': True
        })
    except Exception as e:
        import traceback
        return render(request, 'trade/test.html', {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'success': False
        })


# trade/views.py - Complete fixed home_view

@login_required
def home_view(request):
    """Home dashboard - OPTIMIZED for speed."""
    import pytz
    from django.db.models import Count, Sum, Q, Avg, StdDev, Case, When, Value, FloatField
    from django.core.cache import cache
    from collections import Counter
    
    # ============================================
    # 1. CACHE MARKET DATA (5 minutes)
    # ============================================
    cache_key_market = f'market_data_{timezone.now().strftime("%Y%m%d%H%M")[:11]}'
    market_data = cache.get(cache_key_market)
    
    if not market_data:
        try:
            eat = pytz.timezone('Africa/Dar_es_Salaam')
            now_eat = timezone.now().astimezone(eat)
            current_time_local = now_eat.strftime('%I:%M %p')
            current_date_local = now_eat.strftime('%A, %B %d, %Y')
            
            market_info = is_market_open()
            trading_session_data = get_trading_session()
            market_volatility = get_market_volatility()
            news_impact = get_major_news_impact()
            
            market_data = {
                'current_time_local': current_time_local,
                'current_date_local': current_date_local,
                'market_info': market_info,
                'trading_session_data': trading_session_data,
                'market_volatility': market_volatility,
                'news_impact': news_impact,
            }
            cache.set(cache_key_market, market_data, 300)  # 5 minutes
        except Exception as e:
            print(f"Market data error: {e}")
            market_data = {}
    
    # ============================================
    # 2. OPTIMIZED TRADE QUERIES (Single query)
    # ============================================
    user_trades = Trades.objects.filter(user=request.user)
    
    # SINGLE QUERY: Get all trade data at once
    trade_stats = user_trades.aggregate(
        total_closed=Count('id', filter=Q(target__in=[0, 1])),
        total_wins=Count('id', filter=Q(target=1)),
        total_losses=Count('id', filter=Q(target=0)),
        total_profit=Sum(
            Case(
                When(target=1, then='risk_reward'),
                When(target=0, then=Value(-1)),
                output_field=FloatField(),
            )
        ),
        total_trades=Count('id'),
    )
    
    total_user_trades = trade_stats['total_closed'] or 0
    has_trades = total_user_trades > 0
    
    # Calculate winrate
    if total_user_trades > 0:
        overallwinrate = round((trade_stats['total_wins'] / total_user_trades) * 100, 2)
        overalllossrate = round((trade_stats['total_losses'] / total_user_trades) * 100, 2)
    else:
        overallwinrate = 0
        overalllossrate = 0
    
    overall_profit = trade_stats['total_profit'] or 0
    overall_profit = round(overall_profit, 2)
    
    # ============================================
    # 3. OPTIMIZED TODAY/YESTERDAY QUERIES
    # ============================================
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    today_trades = user_trades.filter(timestamp__date=today)
    yesterday_trades = user_trades.filter(timestamp__date=yesterday)
    
    # Today's stats
    today_closed = today_trades.filter(target__in=[0, 1])
    todays_profit = today_closed.aggregate(
        total=Sum(
            Case(
                When(target=1, then='risk_reward'),
                When(target=0, then=Value(-1)),
                output_field=FloatField(),
            )
        )
    )['total'] or 0
    todays_profit = round(todays_profit, 2)
    
    # Yesterday's stats
    yesterday_closed = yesterday_trades.filter(target__in=[0, 1])
    yesterday_profit = yesterday_closed.aggregate(
        total=Sum(
            Case(
                When(target=1, then='risk_reward'),
                When(target=0, then=Value(-1)),
                output_field=FloatField(),
            )
        )
    )['total'] or 0
    yesterday_profit = round(yesterday_profit, 2)
    
    # ============================================
    # 4. OPTIMIZED PERFORMANCE STATS
    # ============================================
    if total_user_trades >= 5:
        # Get last 20 trades for stats
        last_20 = user_trades.filter(target__in=[0, 1]).order_by('-timestamp')[:20]
        
        stats = last_20.aggregate(
            avg_risk_reward=Avg('risk_reward', filter=Q(target=1)),
            std_dev_rr=StdDev('risk_reward'),
            avg_rvs=Avg('rvs'),
        )
        
        avg_risk_reward = round(stats['avg_risk_reward'] or 0, 2)
        std_dev_rr = round(stats['std_dev_rr'] or 0, 2)
        avg_rvs = round(stats['avg_rvs'] or 0, 2)
        expectancy = round(
            ((overallwinrate / 100) * avg_risk_reward) - 
            ((overalllossrate / 100) * 1), 2
        )
    else:
        avg_risk_reward = 0
        std_dev_rr = 0
        avg_rvs = 0
        expectancy = 0
    
    # ============================================
    # 5. OPTIMIZED LOSS REASON ANALYSIS
    # ============================================
    if total_user_trades > 0:
        losing_trades = user_trades.filter(target=0).order_by('-timestamp')[:50]
        losing_reasons = list(losing_trades.values_list('reason', flat=True))
        losing_reasons = [r for r in losing_reasons if r]
        
        if losing_reasons:
            reason_counts = Counter(losing_reasons)
            most_common_reason, count = reason_counts.most_common(1)[0]
            percentage = round((count / len(losing_reasons)) * 100, 1) if losing_reasons else 0
        else:
            most_common_reason = None
            count = 0
            percentage = 0
    else:
        most_common_reason = None
        count = 0
        percentage = 0
    
    # ============================================
    # 6. OPTIMIZED CHART DATA (Last 40 trades)
    # ============================================
    chart_trades = user_trades.filter(target__in=[0, 1]).order_by('timestamp')[:40]
    
    performance = []
    dates = []
    cum_value = 0
    
    for trade in chart_trades:
        if trade.target == 1:
            cum_value += trade.risk_reward or 0
        else:
            cum_value -= 1
        performance.append(round(cum_value, 2))
        dates.append(trade.timestamp.strftime("%Y-%m-%d"))
    
    # ============================================
    # 7. CALCULATE SEVERITY AND ISSUES (FIXED)
    # ============================================
    issues = []
    severity = 'good'  # default
    severity_display = 'Good'
    severity_light = 'green-light'
    
    if total_user_trades >= 5:
        # Check each metric
        if avg_rvs >= 4:
            issues.append({
                'metric': 'rvs',
                'value': avg_rvs,
                'threshold': 4,
                'issue': 'High Rule Violation Score',
                'category': 'discipline'
            })
            severity = 'serious'
        
        if std_dev_rr > 1:
            issues.append({
                'metric': 'consistency',
                'value': std_dev_rr,
                'threshold': 1,
                'issue': 'Inconsistent Risk-Reward Execution',
                'category': 'risk'
            })
            if severity == 'good':
                severity = 'serious'
        
        if overallwinrate < 40 and overallwinrate > 0:
            issues.append({
                'metric': 'winrate',
                'value': overallwinrate,
                'threshold': 40,
                'issue': 'Very Low Win Rate',
                'category': 'psychology'
            })
            if severity in ['good', 'serious']:
                severity = 'critical'
        elif overallwinrate < 50 and overallwinrate > 0:
            if severity == 'good':
                severity = 'below_average'
        elif overallwinrate > 60:
            if severity == 'good':
                severity = 'excellent'
        
        # Set severity display names
        severity_map = {
            'critical': ('Critical', 'red-light'),
            'serious': ('Serious', 'orange-light'),
            'poor': ('Poor', 'yellow-light'),
            'below_average': ('Below Average', 'blue-light'),
            'good': ('Good', 'green-light'),
            'excellent': ('Excellent', 'purple-light'),
        }
        
        if severity in severity_map:
            severity_display, severity_light = severity_map[severity]
    elif total_user_trades == 0:
        severity = 'new_user'
        severity_display = '🌟 New Trader'
        severity_light = 'blue-light'
    else:
        severity = 'insufficient_data'
        severity_display = f'📊 Building Data ({total_user_trades}/5 trades)'
        severity_light = 'yellow-light'
    
    # ============================================
    # 8. CACHED ADVICE (1 hour)
    # ============================================
    cache_key_advice = f'advice_{request.user.id}_{timezone.now().date()}'
    advice = cache.get(cache_key_advice)
    
    if not advice:
        if has_trades and total_user_trades >= 5:
            try:
                stats_dict = {
                    'overallwinrate': overallwinrate,
                    'std_dev_rr': std_dev_rr,
                    'avg_rvs': avg_rvs,
                }
                # Get performance-based advice
                advice_obj = Advice.get_performance_based_advice(stats_dict)
                if advice_obj:
                    advice = {
                        'quote': advice_obj.quote,
                        'author': advice_obj.author or 'Forex Home'
                    }
                else:
                    advice = {'quote': 'Keep trading!', 'author': 'Forex Home'}
            except Exception as e:
                print(f"Advice error: {e}")
                advice = {'quote': 'Keep trading!', 'author': 'Forex Home'}
        else:
            if total_user_trades == 0:
                advice = {
                    'quote': 'Start logging your trades to get personalized insights!',
                    'author': 'Forex Home Team'
                }
            else:
                advice = {
                    'quote': f"You have {total_user_trades} trade(s) logged. Keep going!",
                    'author': 'Forex Home Team'
                }
        cache.set(cache_key_advice, advice, 3600)  # 1 hour
    
    # ============================================
    # 9. OPTIMIZED MOOD DATA
    # ============================================
    today = timezone.now().date()
    today_mood = None
    mood_streak = 0
    mood_achievements = []
    
    if request.user.is_authenticated:
        try:
            today_mood = Mood.objects.filter(user=request.user, date=today).first()
            mood_streak = get_mood_streak(request.user)
            mood_achievements = get_mood_achievements(request.user)
        except Exception as e:
            print(f"Mood data error: {e}")
            pass
    
    # ============================================
    # 10. RENDER WITH OPTIMIZED DATA
    # ============================================
    return render(request, 'trade/home.html', {
        'user': request.user,
        'current_time_local': market_data.get('current_time_local', timezone.now().strftime('%I:%M %p')),
        'current_date_local': market_data.get('current_date_local', timezone.now().strftime('%A, %B %d, %Y')),
        
        # Market data
        'trading_session': market_data.get('trading_session_data', {}).get('name', 'Unknown'),
        'market_open': market_data.get('market_info', {}).get('is_open', False),
        'session_icon': market_data.get('trading_session_data', {}).get('icon', '📊'),
        'session_description': market_data.get('trading_session_data', {}).get('description', ''),
        'session_volatility': market_data.get('trading_session_data', {}).get('volatility', 'N/A'),
        'market_info': market_data.get('market_info', {}),
        'market_volatility': market_data.get('market_volatility', {}),
        'news_impact': market_data.get('news_impact', {}),
        
        # Session features
        'current_kill_zone': market_data.get('trading_session_data', {}).get('current_kill_zone'),
        'current_dead_zone': market_data.get('trading_session_data', {}).get('current_dead_zone'),
        'is_dead_zone': market_data.get('trading_session_data', {}).get('is_dead_zone', False),
        'trading_recommendation': market_data.get('trading_session_data', {}).get('trading_recommendation', ''),
        'recommendation_color': market_data.get('trading_session_data', {}).get('recommendation_color', 'yellow'),
        'correlation_warnings': market_data.get('trading_session_data', {}).get('correlation_warnings', []),
        'news_drivers': market_data.get('trading_session_data', {}).get('news_drivers', []),
        'active_hours_local': market_data.get('trading_session_data', {}).get('active_hours_local', ''),
        'next_session': market_data.get('trading_session_data', {}).get('next_session', 'Unknown'),
        'time_until_next': market_data.get('trading_session_data', {}).get('time_until_next', ''),
        'active_pairs': market_data.get('trading_session_data', {}).get('active_pairs', []),
        'best_pairs': market_data.get('trading_session_data', {}).get('best_pairs', []),
        'session_pairs': market_data.get('trading_session_data', {}),
        
        # Trade stats
        'total_trades': total_user_trades,
        'overallwinrate': overallwinrate,
        'overalllossrate': overalllossrate,
        'overall_profit': overall_profit,
        'todays_profit': todays_profit,
        'yesterday_profit': yesterday_profit,
        'avg_risk_reward': avg_risk_reward,
        'std_dev_rr': std_dev_rr,
        'avg_rvs': avg_rvs,
        'expectancy': expectancy,
        'has_trades': has_trades,
        'total_user_trades': total_user_trades,
        
        # Loss analysis
        'most_common_reason': most_common_reason,
        'most_common_count': count,
        'most_common_percentage': percentage,
        'reason_message': get_reason_message(most_common_reason),
        'reason_breakdown': [],
        
        # Chart data
        'performance': performance,
        'dates': dates,
        
        # ===== PERFORMANCE STATUS - NOW PROPERLY CALCULATED =====
        'advice': advice,
        'issues': issues,
        'severity': severity,
        'severity_display': severity_display,
        'severity_light': severity_light,
        
        # Mood
        'today_mood': today_mood,
        'mood_selected_today': today_mood is not None,
        'selected_mood': today_mood.mood if today_mood else None,
        'selected_mood_emoji': Mood.MOOD_EMOJIS.get(today_mood.mood, '😐') if today_mood else None,
        'selected_mood_color': Mood.MOOD_COLORS.get(today_mood.mood, '#6b7280') if today_mood else None,
        'mood_streak': mood_streak,
        'mood_achievements': mood_achievements,
        'mood_stats': {},
        
        # Other
        'current_date': timezone.now().strftime('%A, %B %d, %Y'),
        'local_timezone': 'EAT',
        'tomorrow_date': (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'news_headline': 'Fed maintains interest rates • EURUSD volatility expected • Oil prices surge',
    })


def get_reason_message(reason):
    """Helper function for loss reason messages."""
    messages = {
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
    return messages.get(reason, "Keep improving your trading!")


def get_reason_message(reason):
    """Helper function for loss reason messages."""
    messages = {
        "Psycho/Mood": "🧠 Refresh your psychology, avoid emotional trading",
        "Wrong Structure": "📐 Review trade structures before executing",
        "Trend": "📈 Follow the Trend carefully",
        "FOMO": "🎯 Avoid fear of missing out",
        "Greed": "💰 Control Greed, follow your plan",
        "No Confirmation": "⏳ Wait for confirmation",
        "Momentum": "⚡ Avoid weak Momentums",
        "News": "📰 Be cautious around News",
        "Other": "🛑 Review your strategy",
    }
    return messages.get(reason, "Keep improving your trading!")

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
