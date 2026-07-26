# trade/services.py

from django.core.exceptions import ValidationError
from .models import Trades

TRADE_TYPE_MAP = {
    "Scalping (1M)": "scalping_1m",
    "Day trading (5M)": "day_trading_5m",
    "Intraday trading (15M)": "intraday_15m",
    "Swing (H1)": "swing_h1",
}

STYLE_BLOCK_RULES = {
    "swing_h1": {"swing_h1", "intraday_15m"},
    "intraday_15m": {"swing_h1", "intraday_15m"},
    "day_trading_5m": {"day_trading_5m", "intraday_15m"},
    "scalping_1m": set(),
}


def restrict_trade(request, pair, new_trade_type, exclude_draft_id=None) -> None:
    """
    Restrict opening a new trade if there are unjournaled trades
    with conflicting styles on ANY pair sharing the same quote currency.
    
    IMPORTANT: This ignores:
    - Draft trades (is_draft=True)
    - Completed trades (target is not None)
    - The draft being edited (if exclude_draft_id is provided)
    """
    
    # Resolve new trade style
    new_style = TRADE_TYPE_MAP.get(new_trade_type)
    if not new_style:
        return

    # Extract quote currency - handle both string and object
    if isinstance(pair, str):
        pair_name = pair
    else:
        # Assume it's a Pair object or has a name attribute
        pair_name = getattr(pair, "name", str(pair))
    
    if "/" not in pair_name:
        return

    _, quote = pair_name.split("/", 1)

    # Build the query
    # Get unjournaled trades for current user on ALL pairs with same quote
    # Exclude drafts and completed trades
    query = Trades.objects.filter(
        user=request.user,
        pair__name__endswith=f"/{quote}",
        target__isnull=True,  # Only unjournaled trades
        is_draft=False,       # Exclude drafts
    )
    
    # Exclude the draft being edited (if any)
    if exclude_draft_id:
        try:
            query = query.exclude(id=exclude_draft_id)
        except (ValueError, TypeError):
            # If exclude_draft_id is not a valid ID, ignore it
            pass
    
    existing_trade_types = query.values_list("trade_type", flat=True).distinct()
    
    # Debug logging
    print(f"🔍 Restrict trade check - Quote: {quote}, New type: {new_trade_type}")
    print(f"   Found existing types: {list(existing_trade_types)}")
    print(f"   Excluding draft ID: {exclude_draft_id}")

    # Apply blocking rules
    for existing_type in existing_trade_types:
        existing_style = TRADE_TYPE_MAP.get(existing_type)
        if not existing_style:
            continue

        blocked_styles = STYLE_BLOCK_RULES.get(existing_style, set())

        if new_style in blocked_styles:
            print(f"❌ BLOCKED: {new_trade_type} conflicts with {existing_type} on {quote} pair")
            raise ValidationError(
                (
                    f"Trade blocked: '{new_trade_type}' is not allowed while "
                    f"'{existing_type}' is still open or not journaled "
                    f"on another {quote}-based pair."
                )
            )
    
    print(f"✅ No conflicts found for {new_trade_type}")