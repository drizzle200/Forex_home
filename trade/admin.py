from django.contrib import admin
from . import models



class TradeView(admin.ModelAdmin):
    list_display = ['trade_id', 'buy_or_sell', 'pair', 'account', 'risk_reward', 'target', 'timestamp']
    list_filter = ['timestamp', 'pair', 'buy_or_sell', 'target', 'reason', 'account']
    search_fields = ['trade_id', 'pair__name', 'reason']
    list_per_page = 25
    date_hierarchy = 'timestamp'
    raw_id_fields = ['account']  # Better for performance with many accounts
    
    # Make timestamp read-only since it's non-editable
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('trade_id', 'pair', 'account', 'buy_or_sell')  # Removed timestamp from here
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
            'fields': ('risk_reward', 'rvs', 'rvs_grade', 'target', 'reason', 
                      'holding_time', 'narration', 'risk_percent', 'stop_loss_pips', 
                      'calculated_lot_size', 'pip_value_used')
        }),
    )
    
    # Add filtering by calculated lot size and risk fields
    list_filter.extend(['risk_percent', 'calculated_lot_size'])

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

# FundedAccount Admin
class FundedAccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'user', 'account_type', 'account_balance', 'currency', 'is_active', 'trades_count', 'created_at']
    list_filter = ['account_type', 'is_active', 'currency', 'created_at']
    search_fields = ['account_name', 'user__username', 'user__email']
    list_per_page = 25
    list_editable = ['is_active', 'account_balance']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'trades_count_display']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_name', 'account_type')
        }),
        ('Financial Details', {
            'fields': ('account_balance', 'currency', 'is_active')
        }),
        ('Statistics', {
            'fields': ('trades_count_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'increase_balance', 'decrease_balance']
    
    def trades_count(self, obj):
        return obj.trades.count()
    trades_count.short_description = 'Trades'
    trades_count.admin_order_field = 'trades_count'
    
    def trades_count_display(self, obj):
        count = obj.trades.count()
        wins = obj.trades.filter(target=1).count()
        losses = obj.trades.filter(target=0).count()
        
        if count > 0:
            winrate = (wins / count) * 100
            return f"{count} total ({wins}W / {losses}L) - {winrate:.1f}% WR"
        return "No trades yet"
    trades_count_display.short_description = 'Trades Summary'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} accounts marked as active.')
    mark_active.short_description = "Mark selected as active"
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} accounts marked as inactive.')
    mark_inactive.short_description = "Mark selected as inactive"
    
    def increase_balance(self, request, queryset):
        amount = request.POST.get('amount', 100)
        for account in queryset:
            account.account_balance += amount
            account.save()
        self.message_user(request, f'Balance increased by ${amount} for {queryset.count()} accounts.')
    increase_balance.short_description = "Increase balance by $100"
    
    def decrease_balance(self, request, queryset):
        amount = request.POST.get('amount', 100)
        for account in queryset:
            if account.account_balance >= amount:
                account.account_balance -= amount
                account.save()
        self.message_user(request, f'Balance decreased by ${amount} for {queryset.count()} accounts.')
    decrease_balance.short_description = "Decrease balance by $100"

# Inline admin for showing trades within account view
class TradeInline(admin.TabularInline):
    model = models.Trades
    fields = ['trade_id', 'pair', 'buy_or_sell', 'risk_reward', 'target', 'timestamp']
    readonly_fields = ['trade_id', 'pair', 'buy_or_sell', 'risk_reward', 'target', 'timestamp']
    extra = 0
    can_delete = False
    max_num = 10
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False

# Enhanced FundedAccount admin with inline trades
class FundedAccountDetailedAdmin(FundedAccountAdmin):
    inlines = [TradeInline]
    list_display = ['account_name', 'user', 'account_type', 'account_balance', 'currency', 
                   'is_active', 'trades_count', 'total_pnl', 'winrate', 'created_at']
    
    def total_pnl(self, obj):
        trades = obj.trades.all()
        pnl = 0
        for trade in trades:
            if trade.target == 1:
                pnl += trade.risk_reward
            elif trade.target == 0:
                pnl -= 1
        return f"{pnl:.2f}R"
    total_pnl.short_description = 'Total P&L'
    
    def winrate(self, obj):
        trades = obj.trades.all()
        total = trades.count()
        if total == 0:
            return "0%"
        wins = trades.filter(target=1).count()
        return f"{(wins/total*100):.1f}%"
    winrate.short_description = 'Win Rate'

# Register your models
admin.site.register(models.Trades, TradeView)
admin.site.register(models.Pairs, PairView)
admin.site.register(models.Advice, AdviceView)
admin.site.register(models.Mood)
admin.site.register(models.GlobalTrainingData)

# Register FundedAccount with the enhanced admin
admin.site.register(models.FundedAccount, FundedAccountDetailedAdmin)