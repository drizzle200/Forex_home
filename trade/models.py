from django.db import models
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

    PAIR_CHOICES = [("EUR/USD","EUR/USD"),
    				("NZD/USD","NZD/USD"),
    				("AUD/JPY","AUD/JPY"),
    				("GBP/USD","GBP/USD"),
    				("EUR/JPY","EUR/JPY"),

    ]

    H4_CHOICES = 	[("Up Strong","Up Strong"),
    				("Down Strong","Down Strong"),
    				("Up Very strong","Up Very strong"),
    				("Down Very strong","Down Very strong "),
    				("Up weak","Up weak"),
    				("Down weak","Down weak"),

    ]

    ENTRY_PLACE_CHOICES = 	[("key level","Key level"),
    				("POI","POI"),
    				("BRT","BRT"),
    				("Other","Other")

    ]
    BUY_CHOICES = 	[("BUY","BUY"),
    				("SELL","SELL"),
    				
    ]
    SETUP_QUALITY_CHOICES = 	[(5,"5 Stars"),
    				(4,"4 Stars"),
    				(3,"3 Stars"),
    				(2,"2 Stars"),
    				(1,"1 Star"),
    				
    ]

    TRADE_TYPE_CHOICES = 	[("Scalping (1M)","Scalping (1M)"),
    				("Day trading (5M)","Day trading (5M)"),
    				("Intraday trading (15M)","Intraday trading (15M)"),
    				("Swing (H1)","Swing (H1) "),
    				
    ]
    
    CONFIRMATION_CHOICES = 	[("Big maru/pin bar","Big maru/pin bar"),
    				("Triple top","Triple top"),
    				("Double top","Double top"),
    				("No confirmation","No confirmation"),
    				
    ]
    
    MOOD_CHOICES = 	[("Calm","Calm"),
    				("FOMO","FOMO"),
    				("Frustrated","Frustrated"),
    				("Tired","Tired"),
    				
    ]

    TP_CHOICES = 	[("Below recent high","Below recent high"),
    				("At recent high","At recent high"),
    				("Above recent high","Above recent high"),
    				    				
    ]

    TP_REASON_CHOICES = 	[(" Everything OK"," Everything OK"),
    				("Fake BO at KL","Fake BO at KL"),
    				("Strong opposite KL","Strong opposite KL"),
    				("Strong opposite POIL","Strong opposite POI"),
    				("Strong maru/pin","Strong maru/pin (Price rejection)"),
    				("Double top","Double top"),
    				("Triple top","Triple top"),
    				("Strong opposite volume","Strong opposite volume"),
    				    				
    ]

    TARGET_CHOICES = 	[(1,"Win"),
    				(0,"Lose"),
    	   				
    ]

    REASON_CHOICES = 	[("Psycho/Mood","Psycho/Mood"),
    				("Wrong Structure","Wrong Structure"),
    				("Trend","Trend"),
    				("FOMO","FOMO"),
    				("Greed","Greed"),
    				("No Confirmation","No Confirmation"),
    				("Momentum","Momentum"),
    				("News","News"),
    				("Other","Other"),
    	   				
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
