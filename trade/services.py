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


def restrict_trade(pair, new_trade_type) -> None:
    """
    Restrict opening a new trade if there are unjournaled trades
    with conflicting styles on ANY pair sharing the same quote currency.
    """

    # --- Resolve new trade style ---
    new_style = TRADE_TYPE_MAP.get(new_trade_type)
    if not new_style:
        return

    # --- Extract quote currency ---
    pair_name = getattr(pair, "name", str(pair))
    if "/" not in pair_name:
        return

    _, quote = pair_name.split("/", 1)

    # --- Fetch unjournaled trades for ALL pairs with same quote ---
    existing_trade_types = (
        Trades.objects
        .filter(
            pair__name__endswith=f"/{quote}",
            target__isnull=True
        )
        .values_list("trade_type", flat=True)
        .distinct()
    )

    # --- Apply blocking rules ---
    for existing_type in existing_trade_types:
        existing_style = TRADE_TYPE_MAP.get(existing_type)
        if not existing_style:
            continue

        blocked_styles = STYLE_BLOCK_RULES.get(existing_style, set())

        if new_style in blocked_styles:
            raise ValidationError(
                (
                    f"Trade blocked: '{new_trade_type}' is not allowed while "
                    f"'{existing_type}' is still open or not journaled "
                    f"on another {quote}-based pair."
                )
            )
            