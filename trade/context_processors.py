from .models import Trades

def draft_count(request):

    """Context processor for draft and journal counts."""
    context = {
        'draft_count': 0,
        'journal_count': 0,
    }
    
    if request.user.is_authenticated:
        # Draft count - trades marked as draft
        context['draft_count'] = Trades.objects.filter(
            user=request.user,
            is_draft=True
        ).count()
        
        # Journal count - pending trades (target is None) AND NOT drafts
        # This includes ALL trades that need journaling, regardless of trade_type
        context['journal_count'] = Trades.objects.filter(
            user=request.user,
            target__isnull=True,
            is_draft=False  # Exclude drafts
        ).count()
    
    return context