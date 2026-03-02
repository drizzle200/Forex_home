from django.contrib import admin
from . import models

# Register your models here.

class TradeView(admin.ModelAdmin):
    list_display = ['trade_id', 'buy_or_sell', 'pair', 'timestamp']
    list_filter = ['timestamp', 'pair', 'entry_place', 'buy_or_sell']
    search_fields = ['trade_id', 'pair__name']
    list_per_page = 25
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('trade_id', 'pair', 'buy_or_sell', 'timestamp')
        }),
        ('Trade Details', {
            'fields': ('entry_price', 'exit_price', 'risk_reward', 'rvs')
        }),
        ('Outcome', {
            'fields': ('target', 'reason', 'notes')
        }),
    )

class PairView(admin.ModelAdmin):
    list_display = ['name', 'trades_count']
    search_fields = ['name']
    
    def trades_count(self, obj):
        return obj.trades.count()
    trades_count.short_description = 'Number of Trades'

class AdviceView(admin.ModelAdmin):
    list_display = ['quote_preview', 'author', 'category', 'is_active', 'usage_count', 'last_shown']
    list_filter = ['is_active', 'category', 'author']
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
            'fields': ('usage_count', 'last_shown'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'reset_usage']
    
    def quote_preview(self, obj):
        return obj.quote[:75] + "..." if len(obj.quote) > 75 else obj.quote
    quote_preview.short_description = 'Quote'
    
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