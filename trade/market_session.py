from datetime import datetime, timedelta
import pytz
from django.utils import timezone

def get_trading_session():
    """
    Get current trading session based on time in EST (forex standard)
    with local Tanzania time conversion.
    """
    # Timezones
    est = pytz.timezone('US/Eastern')
    eat = pytz.timezone('Africa/Dar_es_Salaam')
    
    # Get current times
    now_est = timezone.now().astimezone(est)
    now_eat = timezone.now().astimezone(eat)
    
    hour_est = now_est.hour
    minute_est = now_est.minute
    time_decimal_est = hour_est + minute_est / 60.0
    
    print(f"DEBUG - Hour EST: {hour_est}, Minute: {minute_est}, Decimal: {time_decimal_est}")
    
    # Define trading sessions in EST (in chronological order)
    sessions = [
        {
            'name': 'London Session',
            'icon': '🇬🇧',
            'description': 'London Open',
            'volatility': 'High',
            'color': '#f59e0b',
            'start': 3,   # 3:00 AM EST
            'end': 8,     # 8:00 AM EST (before NY overlap)
            'start_local': '10:00 AM',
            'end_local': '3:00 PM',
            'active_hours_local': '10:00 AM - 3:00 PM',
            'pairs': '🇬🇧 GBP, 🇪🇺 EUR, 🇨🇭 CHF pairs',
            'active_pairs': [
                {'pair': 'EUR/USD', 'spread': 'Tight', 'volatility': 'High'},
                {'pair': 'GBP/USD', 'spread': 'Tight', 'volatility': 'High'},
                {'pair': 'USD/CHF', 'spread': 'Tight', 'volatility': 'High'},
            ],
            'best_pairs': ['EUR/USD', 'GBP/USD', 'USD/CHF']
        },
        {
            'name': 'London-NY Overlap',
            'icon': '🇬🇧🇺🇸',
            'description': 'Peak Volatility',
            'volatility': 'Extreme',
            'color': '#ef4444',
            'start': 8,   # 8:00 AM EST
            'end': 12,    # 12:00 PM EST
            'start_local': '3:00 PM',
            'end_local': '7:00 PM',
            'active_hours_local': '3:00 PM - 7:00 PM',
            'pairs': '🌐 All major pairs',
            'active_pairs': [
                {'pair': 'EUR/USD', 'spread': 'Ultra Tight', 'volatility': 'Extreme'},
                {'pair': 'GBP/USD', 'spread': 'Ultra Tight', 'volatility': 'Extreme'},
                {'pair': 'USD/JPY', 'spread': 'Ultra Tight', 'volatility': 'Extreme'},
            ],
            'best_pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY']
        },
        {
            'name': 'New York Session',
            'icon': '🇺🇸',
            'description': 'NY Open',
            'volatility': 'Very High',
            'color': '#10b981',
            'start': 12,  # 12:00 PM EST
            'end': 17,    # 5:00 PM EST
            'start_local': '7:00 PM',
            'end_local': '12:00 AM',
            'active_hours_local': '7:00 PM - 12:00 AM',
            'pairs': '🇺🇸 USD, 🇨🇦 CAD pairs',
            'active_pairs': [
                {'pair': 'EUR/USD', 'spread': 'Tight', 'volatility': 'Very High'},
                {'pair': 'GBP/USD', 'spread': 'Tight', 'volatility': 'Very High'},
                {'pair': 'USD/CAD', 'spread': 'Tight', 'volatility': 'High'},
            ],
            'best_pairs': ['USD/CAD', 'EUR/USD', 'GBP/USD']
        },
        {
            'name': 'Pacific Session',
            'icon': '🌊',
            'description': 'Late Night',
            'volatility': 'Low',
            'color': '#6b7280',
            'start': 17,  # 5:00 PM EST
            'end': 19,    # 7:00 PM EST
            'start_local': '12:00 AM',
            'end_local': '2:00 AM',
            'active_hours_local': '12:00 AM - 2:00 AM',
            'pairs': 'Limited activity',
            'active_pairs': [
                {'pair': 'USD/JPY', 'spread': 'Wide', 'volatility': 'Low'},
            ],
            'best_pairs': ['USD/JPY']
        },
        {
            'name': 'Asian Session',
            'icon': '🌏',
            'description': 'Tokyo & Sydney',
            'volatility': 'Low to Medium',
            'color': '#3b82f6',
            'start': 19,  # 7:00 PM EST
            'end': 3,     # 3:00 AM EST (next day) - CHANGED FROM 4 TO 3
            'start_local': '2:00 AM',
            'end_local': '10:00 AM',
            'active_hours_local': '2:00 AM - 10:00 AM',
            'pairs': '🇯🇵 JPY, 🇦🇺 AUD, 🇳🇿 NZD pairs',
            'active_pairs': [
                {'pair': 'USD/JPY', 'spread': 'Low', 'volatility': 'Medium'},
                {'pair': 'AUD/USD', 'spread': 'Low', 'volatility': 'Medium'},
                {'pair': 'NZD/USD', 'spread': 'Low', 'volatility': 'Medium'},
            ],
            'best_pairs': ['AUD/USD', 'USD/JPY', 'NZD/USD']
        }
    ]
    
    # Determine current session based on EST time
    current_session = None
    
    # Check each session in order
    for session in sessions:
        start = session['start']
        end = session['end']
        
        print(f"Checking {session['name']}: {start} - {end}")
        
        # Handle sessions that DON'T span midnight (start < end)
        if start < end:
            if start <= time_decimal_est < end:
                current_session = session.copy()
                print(f"✓ MATCHED: {session['name']} at {time_decimal_est}")
                break
        
        # Handle sessions that DO span midnight (start > end, like Asian Session)
        else:  # start > end (e.g., 19 to 3)
            if time_decimal_est >= start or time_decimal_est < end:
                current_session = session.copy()
                print(f"✓ MATCHED (overnight): {session['name']} at {time_decimal_est}")
                break
    
    # If still no session found (shouldn't happen), default to Asian
    if not current_session:
        print(f"⚠ No session matched, defaulting to Asian")
        current_session = sessions[4].copy()  # Asian Session
    
    # Add time info
    current_session['current_time_est'] = now_est.strftime('%I:%M %p')
    current_session['current_time_local'] = now_eat.strftime('%I:%M %p')
    current_session['local_timezone'] = 'EAT (UTC+3)'
    current_session['hour_est'] = hour_est
    current_session['minute_est'] = minute_est
    current_session['start'] = start
    current_session['end'] = end
    
    # Calculate next session
    next_session = get_next_session_simple(hour_est)
    current_session['next_session'] = next_session['name']
    current_session['time_until_next'] = next_session['time_until']
    
    print(f"✅ FINAL SESSION: {current_session['name']}")
    print("-" * 50)
    
    return current_session


def get_next_session_simple(current_hour_est):
    """Simple next session calculation"""
    if current_hour_est < 3:
        return {'name': 'London Session', 'time_until': f"{3 - current_hour_est:.1f}h"}
    elif current_hour_est < 8:
        return {'name': 'London-NY Overlap', 'time_until': f"{8 - current_hour_est:.1f}h"}
    elif current_hour_est < 12:
        return {'name': 'New York Session', 'time_until': f"{12 - current_hour_est:.1f}h"}
    elif current_hour_est < 17:
        return {'name': 'Pacific Session', 'time_until': f"{17 - current_hour_est:.1f}h"}
    elif current_hour_est < 19:
        return {'name': 'Asian Session', 'time_until': f"{19 - current_hour_est:.1f}h"}
    else:
        # After 19:00, next is Asian? Actually no, next would be London at 3:00
        return {'name': 'London Session', 'time_until': f"{24 - current_hour_est + 3:.1f}h"}


def get_session_pairs(session_name=None):
    """
    Get active pairs for a specific session or current session
    """
    sessions = {
        'Asian Session': {
            'pairs': ['AUD/USD', 'NZD/USD', 'USD/JPY', 'AUD/JPY', 'NZD/JPY'],
            'major_pairs': ['USD/JPY'],
            'cross_pairs': ['AUD/JPY', 'NZD/JPY', 'GBP/JPY'],
            'commodity_pairs': ['AUD/USD', 'NZD/USD'],
            'liquidity': 'Medium',
            'best_time': 'First 4 hours of session',
            'local_time': '2:00 AM - 11:00 AM'
        },
        'London Session': {
            'pairs': ['EUR/USD', 'GBP/USD', 'USD/CHF', 'EUR/GBP', 'EUR/CHF'],
            'major_pairs': ['EUR/USD', 'GBP/USD', 'USD/CHF'],
            'cross_pairs': ['EUR/GBP', 'EUR/CHF', 'GBP/CHF'],
            'commodity_pairs': [],
            'liquidity': 'High',
            'best_time': 'First 3 hours of session',
            'local_time': '10:00 AM - 7:00 PM'
        },
        'London-NY Overlap': {
            'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'AUD/USD', 'NZD/USD'],
            'major_pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD'],
            'cross_pairs': ['EUR/GBP', 'EUR/JPY', 'GBP/JPY'],
            'commodity_pairs': ['AUD/USD', 'NZD/USD', 'USD/CAD'],
            'liquidity': 'Extreme',
            'best_time': 'First 2 hours of overlap',
            'local_time': '3:00 PM - 7:00 PM'
        },
        'New York Session': {
            'pairs': ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY', 'USD/CHF'],
            'major_pairs': ['EUR/USD', 'GBP/USD', 'USD/CAD', 'USD/JPY'],
            'cross_pairs': ['EUR/GBP'],
            'commodity_pairs': ['USD/CAD'],
            'liquidity': 'Very High',
            'best_time': 'First 3 hours of session',
            'local_time': '8:00 PM - 12:00 AM'
        },
        'Pacific Session': {
            'pairs': ['USD/JPY', 'AUD/JPY', 'NZD/JPY', 'GBP/JPY'],
            'major_pairs': ['USD/JPY'],
            'cross_pairs': ['AUD/JPY', 'NZD/JPY', 'GBP/JPY'],
            'commodity_pairs': [],
            'liquidity': 'Low',
            'best_time': 'Last 2 hours of session',
            'local_time': '12:00 AM - 7:00 AM'
        }
    }
    
    if session_name and session_name in sessions:
        return sessions[session_name]
    
    # Get current session
    current = get_trading_session()
    return sessions.get(current['name'], sessions['London Session'])


def get_pair_recommendations():
    """
    Get pair recommendations based on current session
    """
    current = get_trading_session()
    session_pairs = get_session_pairs(current['name'])
    
    return {
        'session': current['name'],
        'best_pairs': current.get('best_pairs', session_pairs.get('major_pairs', [])),
        'all_active': session_pairs['pairs'],
        'major_pairs': session_pairs['major_pairs'],
        'cross_pairs': session_pairs['cross_pairs'],
        'commodity_pairs': session_pairs['commodity_pairs'],
        'liquidity': session_pairs['liquidity'],
        'best_time': session_pairs['best_time'],
        'local_time': session_pairs['local_time'],
        'avoid_pairs': get_pairs_to_avoid(current['name'])
    }


def get_pairs_to_avoid(session_name):
    """
    Get pairs that should be avoided during specific session
    """
    avoid_map = {
        'Asian Session': ['USD/CAD', 'USD/CHF'],
        'London Session': ['AUD/JPY', 'NZD/JPY'],
        'London-NY Overlap': [],  # All pairs are good
        'New York Session': ['AUD/JPY', 'NZD/JPY'],
        'Pacific Session': ['EUR/USD', 'GBP/USD', 'USD/CAD']
    }
    
    return avoid_map.get(session_name, [])


def is_market_open():
    """
    Check if forex market is currently open.
    """
    est = pytz.timezone('US/Eastern')
    eat = pytz.timezone('Africa/Dar_es_Salaam')
    
    now_est = timezone.now().astimezone(est)
    now_eat = timezone.now().astimezone(eat)
    
    day_of_week = now_est.weekday()  # 0=Monday, 6=Sunday
    hour = now_est.hour
    minute = now_est.minute
    current_time_decimal = hour + minute / 60.0
    
    # Default values
    market_open = True
    next_open = None
    next_close = None
    time_until_str = None
    
    # Check if market is closed
    if day_of_week == 5:  # Saturday - closed all day
        market_open = False
        # Opens Sunday at 5:00 PM
        next_open = now_est + timedelta(days=1)
        next_open = next_open.replace(hour=17, minute=0, second=0, microsecond=0)
        
    elif day_of_week == 6:  # Sunday
        if current_time_decimal < 17:  # Before 5:00 PM - closed
            market_open = False
            # Opens today at 5:00 PM
            next_open = now_est.replace(hour=17, minute=0, second=0, microsecond=0)
        else:  # After 5:00 PM - open
            market_open = True
            # Closes Friday at 5:00 PM
            days_until_friday = (4 - day_of_week) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            next_close = now_est + timedelta(days=days_until_friday)
            next_close = next_close.replace(hour=17, minute=0, second=0, microsecond=0)
            
    elif day_of_week == 4:  # Friday
        if current_time_decimal >= 17:  # After 5:00 PM - closed for weekend
            market_open = False
            # Opens Sunday at 5:00 PM
            days_until_sunday = 2
            next_open = now_est + timedelta(days=days_until_sunday)
            next_open = next_open.replace(hour=17, minute=0, second=0, microsecond=0)
        else:  # Before 5:00 PM - open
            market_open = True
            # Closes today at 5:00 PM
            next_close = now_est.replace(hour=17, minute=0, second=0, microsecond=0)
            
    else:  # Monday - Thursday
        market_open = True
        # Closes Friday at 5:00 PM
        days_until_friday = (4 - day_of_week)
        next_close = now_est + timedelta(days=days_until_friday)
        next_close = next_close.replace(hour=17, minute=0, second=0, microsecond=0)
    
    # Calculate time until next open/close
    if not market_open and next_open:
        time_until = next_open - now_est
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            time_until_str = f"{days}d {hours}h {minutes}m"
        else:
            time_until_str = f"{hours}h {minutes}m"
            
    elif market_open and next_close:
        time_until = next_close - now_est
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            time_until_str = f"{days}d {hours}h {minutes}m"
        else:
            time_until_str = f"{hours}h {minutes}m"
    
    return {
        'is_open': market_open,
        'current_time_local': now_eat.strftime('%I:%M %p'),
        'current_time_est': now_est.strftime('%I:%M %p'),
        'market_status': 'OPEN' if market_open else 'CLOSED',
        'market_icon': '🟢' if market_open else '🔴',
        'time_until_next': time_until_str,
        'next_event': 'closes' if market_open else 'opens',
    }

def get_next_market_open(current_time):
    """Calculate the next market open time"""
    est = pytz.timezone('US/Eastern')
    current_day = current_time.strftime('%A')
    current_hour = current_time.hour
    
    # Market opens Sunday at 5:00 PM
    if current_day == 'Sunday' and current_hour < 17:
        # Opens today at 5:00 PM
        next_open = current_time.replace(hour=17, minute=0, second=0, microsecond=0)
    elif current_day == 'Saturday':
        # Opens tomorrow (Sunday) at 5:00 PM
        next_open = current_time + timedelta(days=1)
        next_open = next_open.replace(hour=17, minute=0, second=0, microsecond=0)
    elif current_day == 'Friday' and current_hour >= 17:
        # Opens Sunday at 5:00 PM
        days_until_sunday = (6 - current_time.weekday()) % 7
        next_open = current_time + timedelta(days=days_until_sunday)
        next_open = next_open.replace(hour=17, minute=0, second=0, microsecond=0)
    else:
        # Market is open, return None
        return None
    
    return next_open


def get_next_market_close(current_time):
    """Calculate the next market close time"""
    est = pytz.timezone('US/Eastern')
    current_day = current_time.strftime('%A')
    current_hour = current_time.hour
    
    # Market closes Friday at 5:00 PM
    if current_day == 'Friday':
        if current_hour < 17:
            # Closes today at 5:00 PM
            next_close = current_time.replace(hour=17, minute=0, second=0, microsecond=0)
        else:
            # Already closed for weekend
            return None
    elif current_day == 'Saturday' or current_day == 'Sunday':
        # Closed for weekend
        return None
    else:
        # Monday-Thursday, closes Friday at 5:00 PM
        days_until_friday = (4 - current_time.weekday()) % 7
        next_close = current_time + timedelta(days=days_until_friday)
        next_close = next_close.replace(hour=17, minute=0, second=0, microsecond=0)
    
    return next_close


def get_market_volatility():
    """Get current market volatility level"""
    session = get_trading_session()
    
    # Map volatility to numeric value and color
    volatility_map = {
        'Low': {'level': 2, 'color': '#22c55e', 'icon': '🟢'},
        'Low to Medium': {'level': 3, 'color': '#84cc16', 'icon': '🟢'},
        'Medium': {'level': 5, 'color': '#fbbf24', 'icon': '🟡'},
        'High': {'level': 7, 'color': '#f97316', 'icon': '🟠'},
        'Very High': {'level': 8, 'color': '#ef4444', 'icon': '🔴'},
        'Extreme': {'level': 10, 'color': '#b91c1c', 'icon': '💀'},
    }
    
    volatility_info = volatility_map.get(session['volatility'], 
                                        {'level': 5, 'color': '#fbbf24', 'icon': '🟡'})
    
    return {
        'level': volatility_info['level'],
        'color': volatility_info['color'],
        'icon': volatility_info['icon'],
        'description': session['volatility'],
        'session': session['name'],
        'local_time': session['active_hours_local'],
    }


def get_major_news_impact():
    """Check if there's major news that could impact trading"""
    # This would ideally fetch from an economic calendar API
    # For now, return a placeholder with session context
    session = get_trading_session()
    
    return {
        'has_news': False,
        'news_items': [],
        'impact_level': 'Low',
        'warning': 'No major news in next 2 hours',
        'session_news': f"Regular {session['name']} volatility expected",
        'local_time': session['active_hours_local'],
    }