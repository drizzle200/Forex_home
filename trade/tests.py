from trade.models import Trades

trades_qs = Trades.objects.filter(target__in=[0, 1]).order_by("-timestamp")[:20]

for i in trades_qs:
	print(i.target)