from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from random import choice
import string



# Create your models here.
class Pairs(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
     

    def __str__(self):
        return self.name

class Trades(models.Model):
    trade_id = models.IntegerField(null=True, blank=True)

    PAIR_CHOICES = [
    ("EUR/USD", "🇪🇺 EUR/USD"),
    ("NZD/USD", "🇳🇿 NZD/USD"),
    ("AUD/JPY", "🇦🇺 AUD/JPY"),
    ("GBP/USD", "🇬🇧 GBP/USD"),
    ("EUR/JPY", "🇪🇺🇯🇵 EUR/JPY"),
    ]
    
    H4_CHOICES = [
        ("Up Strong", "🚀 Up Strong"),
        ("Down Strong", "💥 Down Strong"),
        ("Up Very strong", "⚡ Up Very strong"),
        ("Down Very strong", "🌊 Down Very strong"),
        ("Up weak", "↗️ Up weak"),
        ("Down weak", "↘️ Down weak"),
    ]
    
    ENTRY_PLACE_CHOICES = [
        ("key level", "🎯 Key level"),
        ("POI", "📍 POI"),
        ("BRT", "🔄 BRT"),
        ("Other", "❓ Other")
    ]
    
    BUY_CHOICES = [
        ("BUY", "🟢 BUY"),
        ("SELL", "🔴 SELL"),
    ]
    
    SETUP_QUALITY_CHOICES = [
        (5, "🌟🌟🌟🌟🌟"),
        (4, "🌟🌟🌟🌟"),
        (3, "🌟🌟🌟"),
        (2, "🌟🌟"),
        (1, "🌟"),
    ]
    
    TRADE_TYPE_CHOICES = [
        ("Scalping (1M)", "⚡ Scalping (1M)"),
        ("Day trading (5M)", "📊 Day trading (5M)"),
        ("Intraday trading (15M)", "📈 Intraday trading (15M)"),
        ("Swing (H1)", "🔄 Swing (H1)"),
    ]
    
    CONFIRMATION_CHOICES = [
        ("Big maru/pin bar", "📌 Big maru/pin bar"),
        ("Triple top", "🔝🔝🔝 Triple top"),
        ("Double top", "🔝🔝 Double top"),
        ("No confirmation", "❌ No confirmation"),
    ]
    
    MOOD_CHOICES = [
        ("Calm", "😌 Calm"),
        ("FOMO", "😰 FOMO"),
        ("Frustrated", "😤 Frustrated"),
        ("Tired", "😴 Tired"),
    ]
    
    TP_CHOICES = [
        ("Below recent high", "⬇️ Below recent high"),
        ("At recent high", "⚖️ At recent high"),
        ("Above recent high", "⬆️ Above recent high"),
    ]
    
    TP_REASON_CHOICES = [
        ("Everything OK", "✅ Everything OK"),
        ("Fake BO at KL", "🎭 Fake BO at KL"),
        ("Strong opposite KL", "🛑 Strong opposite KL"),
        ("Strong opposite POI", "🚧 Strong opposite POI"),
        ("Strong maru/pin", "📌 Strong maru/pin (Price rejection)"),
        ("Double top", "🔝🔝 Double top"),
        ("Triple top", "🔝🔝🔝 Triple top"),
        ("Strong opposite volume", "📉 Strong opposite volume"),
    ]
    
    TARGET_CHOICES = [
        (1, "✅ Win 🏆"),
        (0, "❌ Lose 💔"),
    ]
    
    REASON_CHOICES = [
        ("Psycho/Mood", "🧠 Psycho/Mood"),
        ("Wrong Structure", "📐 Wrong Structure"),
        ("Trend", "📈 Trend"),
        ("FOMO", "🎯 FOMO"),
        ("Greed", "💰 Greed"),
        ("No Confirmation", "⏳ No Confirmation"),
        ("Momentum", "⚡ Momentum"),
        ("News", "📰 News"),
        ("Other", "❓ Other"),
    ]






    pair   = models.ForeignKey(Pairs, on_delete=models.CASCADE, related_name="trades")
    momentum_h4   = models.CharField(max_length=20, null=True,blank=True, choices=H4_CHOICES)
    momentum_h1   = models.CharField(max_length=20, null=True, blank=True, choices=H4_CHOICES)
    momentum_15m  = models.CharField(max_length=20, null=True,blank=True,  choices=H4_CHOICES)
    momentum_5m   = models.CharField(max_length=20, null=True, blank=True, choices=H4_CHOICES)
    momentum_1m   = models.CharField(max_length=20, null=True,blank=True,  choices=H4_CHOICES)
    session   = models.CharField(max_length=20, blank=True, null=True)
    entry_place   = models.CharField(max_length=20, null=True,blank=True,  choices=ENTRY_PLACE_CHOICES)
    buy_or_sell   = models.CharField(max_length=20, null=True,blank=True, choices=BUY_CHOICES)
    setup_quality   = models.IntegerField(null=True, blank=True, choices=SETUP_QUALITY_CHOICES)
    trade_type   = models.CharField(max_length=50, null=True,blank=True,  choices=TRADE_TYPE_CHOICES)
    confirmation   = models.CharField(max_length=20, null=True, blank=True, choices=CONFIRMATION_CHOICES)
    mood		   = models.CharField(max_length=20, null=True,blank=True, choices=MOOD_CHOICES)
    tp  		 = models.CharField(max_length=20, null=True, blank=True, choices= TP_CHOICES)
    tp_reason   = models.CharField(max_length=50, null=True, blank=True, choices= TP_REASON_CHOICES)
    risk_reward = models.FloatField(null=True, blank=True)
    rvs 		   = models.IntegerField(null=True, blank=True)
    rvs_grade   = models.CharField(max_length=20,blank=True,  null=True)
    target 		   = models.IntegerField(null=True, blank=True, choices=TARGET_CHOICES)
    reason 		   = models.CharField(max_length=20, null=True,blank=True,  choices=REASON_CHOICES)
    holding_time   = models.IntegerField(null=True, blank=True)
    narration   = models.CharField(max_length=500, null=True,blank=True,  )
    timestamp   = models.DateTimeField(auto_now_add=True)
    

    @property
    def holding_time_display(self):
        if not self.holding_time:
            return ""

        hours, minutes = divmod(self.holding_time, 60)

        if hours and minutes:
            return f"{hours}h {minutes}m"
        if hours:
            return f"{hours}h"
        return f"{minutes}m"

    def __str__(self):
        return f'{self.trade_id} - {self.buy_or_sell}'

class Advice(models.Model):
    CATEGORY_CHOICES = [
        ('motivation', '💪 Motivation'),
        ('discipline', '🎯 Discipline'),
        ('psychology', '🧠 Psychology'),
        ('risk', '⚠️ Risk Management'),
        ('trading', '📊 Trading Wisdom'),
        ('mindset', '🌅 Mindset'),
        ('patience', '⏳ Patience'),
    ]
    
    quote = models.TextField(help_text="The advice or motivational quote")
    author = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Author of the quote (leave blank if unknown)"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
        help_text="Category of advice"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this advice should be displayed"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this advice was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last updated"
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="How many times this advice has been shown"
    )
    last_shown = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this advice was last displayed"
    )
    
    class Meta:
        db_table = 'trade_advice'
        verbose_name = "Advice"
        verbose_name_plural = "Advice"
        ordering = ['-is_active', 'usage_count', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['usage_count']),
        ]
    
    def __str__(self):
        if self.author:
            return f"“{self.quote[:50]}...” - {self.author}"
        return f"“{self.quote[:50]}...”"
    
    def increment_usage(self):
        """Increment usage count and update last_shown"""
        self.usage_count += 1
        self.last_shown = timezone.now()
        self.save(update_fields=['usage_count', 'last_shown'])
    
    @classmethod
    def get_daily_advice(cls):
        """
        Get advice for the day - prefers less-shown advice first.
        This is the default fallback for average performance.
        """
        advice = cls.objects.filter(
            is_active=True
        ).order_by('usage_count', '?').first()
        
        if advice:
            advice.increment_usage()
        
        return advice
    
    @classmethod
    def get_random_advice(cls):
        """Get completely random active advice (backup method)"""
        advice = cls.objects.filter(is_active=True).order_by('?').first()
        
        if advice:
            advice.increment_usage()
        
        return advice
    
    @classmethod
    def get_advice_by_category(cls, category):
        """
        Get random advice from specific category.
        Used for targeted advice based on performance.
        """
        if not category:
            return cls.get_daily_advice()
        
        advice = cls.objects.filter(
            is_active=True, 
            category=category
        ).order_by('usage_count', '?').first()
        
        if advice:
            advice.increment_usage()
        
        return advice
    
    @classmethod
    def analyze_performance(cls, stats):
        """Analyze performance and return issue list and severity"""
        winrate = stats.get('overallwinrate', 0)
        std_dev_rr = stats.get('std_dev_rr', 999)
        avg_rvs = stats.get('avg_rvs', 999)
        
        issues = []
        severity = 'good'  # default
        
        # Check each metric
        if avg_rvs >= 4:
            issues.append({
                'metric': 'rvs',
                'value': avg_rvs,
                'threshold': 4,
                'issue': 'High rule violation score',
                'category': 'discipline'
            })
            severity = 'critical'
        
        if std_dev_rr > 1:
            issues.append({
                'metric': 'consistency',
                'value': std_dev_rr,
                'threshold': 1,
                'issue': 'Inconsistent risk-reward execution',
                'category': 'risk'
            })
            if severity != 'critical':
                severity = 'serious'
        
        if winrate < 40:
            issues.append({
                'metric': 'winrate',
                'value': winrate,
                'threshold': 40,
                'issue': 'Very low win rate',
                'category': 'psychology'
            })
            if severity not in ['critical', 'serious']:
                severity = 'poor'
        elif winrate < 50:
            if severity not in ['critical', 'serious', 'poor']:
                severity = 'below_average'
        elif winrate > 60:
            if severity == 'good':
                severity = 'excellent'
        
        return issues, severity
    
    @classmethod
    def get_performance_based_advice(cls, stats):
        """
        Get advice based on comprehensive performance analysis
        """
        issues, severity = cls.analyze_performance(stats)
        
        # Priority based on severity and issues
        if severity == 'critical':
            # Multiple serious issues
            advice = (cls.get_advice_by_category('discipline') or 
                     cls.get_advice_by_category('psychology'))
        elif severity == 'serious':
            # Single serious issue
            if issues and issues[0]['category'] == 'risk':
                advice = cls.get_advice_by_category('risk')
            else:
                advice = cls.get_advice_by_category('discipline')
        elif severity == 'poor':
            advice = cls.get_advice_by_category('psychology')
        elif severity == 'below_average':
            advice = cls.get_advice_by_category('trading')
        elif severity == 'excellent':
            advice = cls.get_advice_by_category('motivation')
        else:
            advice = cls.get_daily_advice()
        
        # Ultimate fallback
        if not advice:
            advice = cls.get_random_advice()
        
        return advice