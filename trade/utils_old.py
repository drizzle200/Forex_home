# trade/utils.py
import numpy as np
from django.db import models
from datetime import datetime
from .models import Trades  # Import your models

def calculate_overall_stats(trades_queryset):
    """Calculate overall statistics from a filtered trades queryset."""
    total_trades = trades_queryset.count()
    if total_trades == 0:
        return {
            'overallwinrate': 0,
            'overalllossrate': 0,
            'expectancy': 0,
            'avg_rvs': 0,
            'avg_risk_reward': 0,
            'std_dev_rr': 0,
        }
    
    winning_trades = trades_queryset.filter(profit_r__gt=0).count()
    losing_trades = trades_queryset.filter(profit_r__lt=0).count()
    
    overallwinrate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    overalllossrate = (losing_trades / total_trades) * 100 if total_trades > 0 else 0
    
    total_profit = trades_queryset.aggregate(total=models.Sum('profit_r'))['total'] or 0
    expectancy = total_profit / total_trades if total_trades > 0 else 0
    
    avg_rvs = trades_queryset.aggregate(avg=models.Avg('rvs'))['avg'] or 0
    avg_risk_reward = trades_queryset.aggregate(avg=models.Avg('risk_reward'))['avg'] or 0
    std_dev_rr = calculate_std_dev(trades_queryset.values_list('profit_r', flat=True))
    
    return {
        'overallwinrate': round(overallwinrate, 1),
        'overalllossrate': round(overalllossrate, 1),
        'expectancy': round(expectancy, 2),
        'avg_rvs': round(avg_rvs, 2),
        'avg_risk_reward': round(avg_risk_reward, 2),
        'std_dev_rr': round(std_dev_rr, 2),
    }

def get_pairs_summary(trades_queryset):
    """Get summary by trading pair from filtered trades."""
    pairs = trades_queryset.values('pair').distinct()
    summary = []
    
    for pair in pairs:
        pair_trades = trades_queryset.filter(pair=pair['pair'])
        total = pair_trades.count()
        won = pair_trades.filter(profit_r__gt=0).count()
        lost = pair_trades.filter(profit_r__lt=0).count()
        
        summary.append({
            'pair': pair['pair'],
            'won': won,
            'lost': lost,
            'winrate': round((won / total * 100) if total > 0 else 0, 1),
            'profit_r': round(pair_trades.aggregate(avg=models.Avg('profit_r'))['avg'] or 0, 2),
        })
    
    return summary

def analyze_losing_reasons(trades_queryset):
    """Analyze losing reasons from filtered trades."""
    losing_trades = trades_queryset.filter(profit_r__lt=0)
    total_losing = losing_trades.count()
    
    if total_losing == 0:
        return {
            'most_common_reason': 'No losing trades',
            'most_common_count': 0,
            'most_common_percentage': 0,
            'message': 'No losing trades to analyze. Great job!',
            'reason_breakdown': {},
            'total_losing_analyzed': 0,
            'unique_reasons': 0,
        }
    
    reason_counts = losing_trades.values('loss_reason').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    most_common = reason_counts.first()
    reason_breakdown = {item['loss_reason']: item['count'] for item in reason_counts}
    
    return {
        'most_common_reason': most_common['loss_reason'] if most_common else 'Unknown',
        'most_common_count': most_common['count'] if most_common else 0,
        'most_common_percentage': round((most_common['count'] / total_losing * 100), 1) if most_common else 0,
        'message': f"Your most common losing reason is '{most_common['loss_reason']}'" if most_common else "No losing trades analyzed",
        'reason_breakdown': reason_breakdown,
        'total_losing_analyzed': total_losing,
        'unique_reasons': reason_counts.count(),
    }

def get_today_trading_data(trades_queryset):
    """Get today's trading data from filtered trades."""
    today = datetime.now().date()
    today_trades = trades_queryset.filter(timestamp__date=today)
    
    todays_profit = today_trades.aggregate(total=models.Sum('profit_r'))['total'] or 0
    
    return {
        'todays_trades': today_trades.count(),
        'todays_profit': round(todays_profit, 2),
    }

def prepare_chart_data(trades_queryset):
    """Prepare chart data from filtered trades."""
    daily_performance = trades_queryset.values('timestamp__date').annotate(
        daily_profit=models.Sum('profit_r')
    ).order_by('timestamp__date')
    
    dates = [item['timestamp__date'].strftime('%Y-%m-%d') for item in daily_performance]
    performance = [round(item['daily_profit'], 2) for item in daily_performance]
    
    return {
        'dates': dates,
        'performance': performance,
    }

def calculate_consistency_grade(todays_trades, avg_rvs, std_dev_rr, most_common_reason):
    """Calculate consistency grade."""
    score = 0
    
    if todays_trades > 0:
        score += 1
    if avg_rvs < 5:
        score += 1
    if std_dev_rr < 2:
        score += 1
    if most_common_reason and most_common_reason != 'Unknown' and most_common_reason != 'No losing trades':
        score += 1
    
    tiers = {4: 'A', 3: 'B', 2: 'C', 1: 'D', 0: 'F'}
    
    return {
        'consistency_score': score,
        'consistency_tier': tiers.get(score, 'F'),
        'consistency_level': score,
    }

def calculate_std_dev(values):
    """Calculate standard deviation from a list of values."""
    values_list = list(values)
    if len(values_list) < 2:
        return 0
    
    return np.std(values_list)