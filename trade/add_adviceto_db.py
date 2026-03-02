from trade.models import Advice
from django.utils import timezone

advice_data = [
    # ===== DISCIPLINE (15 quotes) =====
    {
        'quote': 'Plan your trade and trade your plan.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline is the bridge between goals and accomplishment.',
        'author': 'Jim Rohn',
        'category': 'discipline',
    },
    {
        'quote': 'The market will test your discipline more than your intelligence.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline is doing what you said you would do, even when you don\'t feel like it.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Without discipline, no trading system will work. With discipline, any trading system can work.',
        'author': 'Mark Douglas',
        'category': 'discipline',
    },
    {
        'quote': 'The most important quality for a trader is discipline, not intelligence.',
        'author': 'Richard Dennis',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline means sticking to your rules even when you\'re losing.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Trading is 20% strategy and 80% discipline.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Your trading plan is your roadmap. Discipline is the vehicle that gets you there.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline is choosing what you want most over what you want now.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'The enemy of discipline is emotion. Master your emotions or they will master your account.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline in trading is like brakes in a car. You need both to go fast safely.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Small losses with discipline are better than large losses with hope.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Discipline is the difference between a professional and an amateur.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Trade your plan, don\'t plan your trade after you enter.',
        'author': 'Unknown',
        'category': 'discipline',
    },

    # ===== PSYCHOLOGY (20 quotes) =====
    {
        'quote': 'The secret to trading success is emotional discipline. If intelligence were the key, there would be a lot more people making money trading.',
        'author': 'Victor Sperandeo',
        'category': 'psychology',
    },
    {
        'quote': 'Fear and greed are the two strongest emotions in trading. Master them and you master the market.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The market is a psychological battlefield. The enemy is not other traders, it\'s yourself.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Your mind is your most powerful trading tool. Keep it sharp, keep it calm, keep it focused.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Fear causes you to exit winners too early. Greed causes you to hold losers too long.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The greatest obstacle to trading success is not the market, but the trader\'s own psychology.',
        'author': 'Mark Douglas',
        'category': 'psychology',
    },
    {
        'quote': 'Hope is the enemy of the losing trader. Hope keeps you in losing positions.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Trading is 80% psychology and 20% mechanics.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The market can remain irrational longer than you can remain solvent.',
        'author': 'John Maynard Keynes',
        'category': 'psychology',
    },
    {
        'quote': 'Don\'t let a losing trade turn into a losing day. Don\'t let a losing day turn into a losing week. Don\'t let a losing week turn into a losing month.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The most difficult task in trading is not finding winning trades, but managing your emotions during losing streaks.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Ego is the enemy of good trading. Pride comes before a margin call.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'When you feel euphoric after a win, you\'re most vulnerable. When you feel devastated after a loss, you\'re most vulnerable.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Trading is not about being right. It\'s about making money when you\'re right and losing as little as possible when you\'re wrong.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The market has no emotions. Don\'t project yours onto it.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Revenge trading is the fastest way to blow up your account.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'When you feel the urge to overtrade, step away. The market will be there tomorrow.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Your trading journal should record not just your trades, but your emotions during each trade.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The best trades feel uncomfortable because you\'re going against the crowd.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Confidence comes from preparation, not from winning streaks.',
        'author': 'Unknown',
        'category': 'psychology',
    },

    # ===== RISK MANAGEMENT (18 quotes) =====
    {
        'quote': 'The most important rule of trading is to play great defense, not great offense.',
        'author': 'Paul Tudor Jones',
        'category': 'risk',
    },
    {
        'quote': 'Risk comes from not knowing what you\'re doing.',
        'author': 'Warren Buffett',
        'category': 'risk',
    },
    {
        'quote': 'Never risk more than 1-2% of your account on a single trade.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The first rule of trading is to survive. The second rule is to remember the first rule.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Cut your losses short and let your winners run.',
        'author': 'Ed Seykota',
        'category': 'risk',
    },
    {
        'quote': 'It\'s not about how much you make, it\'s about how much you don\'t lose.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Risk management is not about avoiding risk, but about managing it intelligently.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The goal is not to be right, but to make money when you\'re right and lose as little as possible when you\'re wrong.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Your stop loss is your seatbelt. Don\'t drive without it.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Amateurs focus on how much they can make. Professionals focus on how much they can lose.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The market is a giant transfer mechanism that takes money from the impatient and gives it to the patient. But it also takes money from those who don\'t manage risk and gives it to those who do.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Preservation of capital is more important than return on capital.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Don\'t risk what you need to make what you want.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The best risk management is not trading when the odds are against you.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Your account size determines your risk per trade, not your confidence in the trade.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Losing trades are part of the game. The key is to keep losses small.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Risk management is knowing when to hold and when to fold.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The best traders are not the ones with the highest win rates, but the ones with the best risk management.',
        'author': 'Unknown',
        'category': 'risk',
    },

    # ===== MOTIVATION (15 quotes) =====
    {
        'quote': 'The market is a device for transferring money from the impatient to the patient.',
        'author': 'Warren Buffett',
        'category': 'motivation',
    },
    {
        'quote': 'The goal of a successful trader is to make the best trades. Money is secondary.',
        'author': 'Alexander Elder',
        'category': 'motivation',
    },
    {
        'quote': 'Success in trading is not about being a genius. It\'s about consistency, discipline, and patience.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Every master was once a beginner. Every expert was once a novice.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'The stock market is filled with individuals who know the price of everything, but the value of nothing.',
        'author': 'Philip Fisher',
        'category': 'motivation',
    },
    {
        'quote': 'The four most dangerous words in investing are: "This time it\'s different."',
        'author': 'Sir John Templeton',
        'category': 'motivation',
    },
    {
        'quote': 'In trading, you get what you deserve, not what you want.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'The market will humble you when you get too cocky and break you when you get too emotional.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Trading is simple but not easy. Simple to understand, difficult to execute.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Your next great trade could be just around the corner. Stay prepared, stay patient.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'The difference between a successful trader and a failed trader is the ability to persist through losses.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Trading is a journey, not a destination. Enjoy the process, not just the profits.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Every loss is a lesson. Every lesson makes you better.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'The market rewards patience and punishes impulsiveness.',
        'author': 'Unknown',
        'category': 'motivation',
    },
    {
        'quote': 'Successful traders are simply amateurs who never gave up.',
        'author': 'Unknown',
        'category': 'motivation',
    },

    # ===== TRADING WISDOM (22 quotes) =====
    {
        'quote': 'Markets are constantly in a state of uncertainty and flux. Money is made by discounting the obvious and betting on the unexpected.',
        'author': 'George Soros',
        'category': 'trading',
    },
    {
        'quote': 'The elements of good trading are: (1) cutting losses, (2) cutting losses, and (3) cutting losses. If you can follow these three rules, you may have a chance.',
        'author': 'Ed Seykota',
        'category': 'trading',
    },
    {
        'quote': 'Trend is your friend until the end when it bends.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Buy on rumor, sell on news.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Don\'t catch a falling knife.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The trend is your friend except at the end where it bends.',
        'author': 'Ed Seykota',
        'category': 'trading',
    },
    {
        'quote': 'Markets can remain irrational longer than you can remain solvent.',
        'author': 'John Maynard Keynes',
        'category': 'trading',
    },
    {
        'quote': 'In trading, the first loss is the best loss.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The market does not care about your opinion. It only cares about price.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Don\'t fight the tape.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The trend is your friend until it isn\'t.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Price is what you pay. Value is what you get.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },
    {
        'quote': 'The stock market is a device for transferring money from the active to the patient.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },
    {
        'quote': 'Be fearful when others are greedy, and greedy when others are fearful.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },
    {
        'quote': 'It\'s not whether you\'re right or wrong that\'s important, but how much money you make when you\'re right and how much you lose when you\'re wrong.',
        'author': 'George Soros',
        'category': 'trading',
    },
    {
        'quote': 'The big money is not in the buying and selling, but in the waiting.',
        'author': 'Charlie Munger',
        'category': 'trading',
    },
    {
        'quote': 'Successful investing is about managing risk, not avoiding it.',
        'author': 'Benjamin Graham',
        'category': 'trading',
    },
    {
        'quote': 'The individual investor should act consistently as an investor and not as a speculator.',
        'author': 'Benjamin Graham',
        'category': 'trading',
    },
    {
        'quote': 'The function of economic forecasting is to make astrology look respectable.',
        'author': 'John Kenneth Galbraith',
        'category': 'trading',
    },
    {
        'quote': 'Wide diversification is only required when investors do not understand what they are doing.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },
    {
        'quote': 'The stock market is designed to transfer money from the active to the patient.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },
    {
        'quote': 'The most important quality for an investor is temperament, not intellect.',
        'author': 'Warren Buffett',
        'category': 'trading',
    },

    # ===== MINDSET (15 quotes) =====
    {
        'quote': 'Successful trading is not about being right, it\'s about managing risk.',
        'author': 'Larry Hite',
        'category': 'mindset',
    },
    {
        'quote': 'The difference between successful and unsuccessful traders is that successful traders have developed the ability to control their emotions.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your mindset determines your success more than your strategy.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Think like a survivor. Your goal is to stay in the game long enough to win.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market will test your patience, your discipline, and your resolve. Stay strong.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Don\'t let a winning trade make you overconfident or a losing trade make you doubtful.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The best traders approach the market with humility, not ego.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your trading mindset should be: "I will survive and I will thrive."',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Detach your self-worth from your trading results.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market owes you nothing. Approach each trade with zero expectations.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'A calm mind is a profitable mind.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Don\'t trade to make money. Trade to execute your strategy well. Money follows good execution.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market is neutral. It doesn\'t know you exist. Don\'t take losses personally.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your mindset should be flexible like water, not rigid like ice.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Success in trading comes from having the right mindset, not from finding the perfect strategy.',
        'author': 'Unknown',
        'category': 'mindset',
    },

    # ===== PATIENCE (15 quotes) =====
    {
        'quote': 'The stock market is a device for transferring money from the active to the patient.',
        'author': 'Warren Buffett',
        'category': 'patience',
    },
    {
        'quote': 'Patience is a key element of success. In trading, you have to wait for the right opportunity.',
        'author': 'Bill Lipschutz',
        'category': 'patience',
    },
    {
        'quote': 'The stock market is filled with individuals who know the price of everything, but the value of nothing. Patience gives you value.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Great things never come from comfort zones. But they also never come from impatience.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The best trades are the ones you didn\'t take because you waited for the perfect setup.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Patience is not the ability to wait. It\'s the ability to keep a good attitude while waiting.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'In trading, patience is a competitive advantage.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The market will give you opportunities. Patience ensures you\'re ready when they come.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Don\'t force trades. Let the market come to you.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Patience in trading means waiting for the right pitch, not swinging at everything.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The money is made in the waiting, not in the trading.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'If you have patience, the market will eventually reward you. If you don\'t, it will eventually punish you.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The difference between a successful trader and an unsuccessful one is often just a few days of patience.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Patience is not passive waiting. It is active preparation for the right moment.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'In a world of instant gratification, patience in trading is your superpower.',
        'author': 'Unknown',
        'category': 'patience',
    },
]

# Add all advice
for data in advice_data:
    Advice.objects.create(
        quote=data['quote'],
        author=data['author'],
        category=data['category'],
        created_at=timezone.now(),
        updated_at=timezone.now()
    )

print(f"✅ Added {len(advice_data)} advice entries to database!")

# Verify
print(f"Total advice in database: {Advice.objects.count()}")
print(f"Active advice: {Advice.objects.filter(is_active=True).count()}")