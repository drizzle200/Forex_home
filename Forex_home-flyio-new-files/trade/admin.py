from django.contrib import admin
from . import models

class TradeView(admin.ModelAdmin):
    list_display = ['trade_id', 'buy_or_sell', 'pair', 'risk_reward', 'target', 'timestamp']
    list_filter = ['timestamp', 'pair', 'buy_or_sell', 'target', 'reason']
    search_fields = ['trade_id', 'pair__name', 'reason']
    list_per_page = 25
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('trade_id', 'pair', 'buy_or_sell', 'timestamp')
        }),
        ('Momentum Analysis', {
            'fields': ('momentum_h4', 'momentum_h1', 'momentum_15m', 'momentum_5m', 'momentum_1m'),
            'classes': ('collapse',)
        }),
        ('Trade Setup', {
            'fields': ('session', 'entry_place', 'setup_quality', 'trade_type', 'confirmation')
        }),
        ('Psychology', {
            'fields': ('mood',)
        }),
        ('Take Profit Analysis', {
            'fields': ('tp', 'tp_reason'),
            'classes': ('collapse',)
        }),
        ('Outcome', {
            'fields': ('risk_reward', 'rvs', 'rvs_grade', 'target', 'reason', 'holding_time', 'narration')
        }),
    )

class PairView(admin.ModelAdmin):
    list_display = ['name', 'trades_count']
    search_fields = ['name']
    
    def trades_count(self, obj):
        return obj.trades.count()
    trades_count.short_description = 'Number of Trades'

class AdviceView(admin.ModelAdmin):
    list_display = ['id', 'quote_preview', 'author', 'category_display', 'is_active', 'usage_count', 'last_shown']
    list_filter = ['is_active', 'category']
    search_fields = ['quote', 'author']
    list_editable = ['is_active']
    list_per_page = 20
    readonly_fields = ['usage_count', 'last_shown', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Advice Content', {
            'fields': ('quote', 'author', 'category')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('usage_count', 'last_shown', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'reset_usage']
    
    def quote_preview(self, obj):
        return obj.quote[:75] + "..." if len(obj.quote) > 75 else obj.quote
    quote_preview.short_description = 'Quote'
    
    def category_display(self, obj):
        if obj.category:
            return dict(obj.CATEGORY_CHOICES).get(obj.category, obj.category)
        return '-'
    category_display.short_description = 'Category'
    category_display.admin_order_field = 'category'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} advice entries marked as active.')
    mark_active.short_description = "Mark selected as active"
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} advice entries marked as inactive.')
    mark_inactive.short_description = "Mark selected as inactive"
    
    def reset_usage(self, request, queryset):
        updated = queryset.update(usage_count=0, last_shown=None)
        self.message_user(request, f'Usage count reset for {updated} advice entries.')
    reset_usage.short_description = "Reset usage count"

# Register your models
admin.site.register(models.Trades, TradeView)
admin.site.register(models.Pairs, PairView)
admin.site.register(models.Advice, AdviceView)

@admin.register(models.Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'mood', 'trades_count', 'profit_loss']
    list_filter = ['mood', 'date']
    search_fields = ['user__username', 'notes']
    date_hierarchy = 'date'