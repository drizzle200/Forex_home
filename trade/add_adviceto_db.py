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
     {
        'quote': 'The market is a mirror reflecting your emotional state. Trade only when the reflection is clear.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Emotions are like waves in the ocean - you cannot stop them, but you can learn to surf.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'When anger enters your trading decisions, logic exits through the back door.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The most dangerous time to trade is when you feel invincible after a winning streak.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Your trading account is a direct reflection of your emotional stability.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Fear makes small losses big; greed makes small profits disappear.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The market doesn\'t know you exist - don\'t take its movements personally.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Impulse trading is the silent killer of trading accounts.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Your worst trade will come right after your best one if you let success go to your head.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Emotional detachment from money is the secret to making money.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The battle in trading is not against the market, but against the voice in your head.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'When you feel the urge to "get even" with the market, you\'re about to get odd with your account.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'A calm mind sees opportunities that an anxious mind completely misses.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'The market will wait for you to calm down. Don\'t rush back in.',
        'author': 'Unknown',
        'category': 'psychology',
    },
    {
        'quote': 'Your trading psychology is like a garden - weeds grow automatically, but good crops need tending.',
        'author': 'Unknown',
        'category': 'psychology',
    },

    # ===== RISK MANAGEMENT (15 quotes) =====
    {
        'quote': 'Never let a single trade define your month. Let probability work over many trades.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Risk management isn\'t about avoiding losses - it\'s about surviving them.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The size of your stop loss should be determined by market conditions, not your ego.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'A stop loss is like insurance - you hope you never need it, but you never drive without it.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'If you don\'t respect risk, risk will disrespect your account balance.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The best traders are professional risk managers who happen to trade.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Risk per trade should be so small that you forget about it 5 minutes after entering.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'A losing trade with proper risk management is a winning trade in disguise.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Your stop loss is not a suggestion - it\'s a binding contract with yourself.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The market can smell when you\'re over-leveraged. That\'s when it turns against you.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Risk what you can afford to lose, not what you hope to gain.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Position sizing is more important than entry signals.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The goal is not to be right 90% of the time, but to be profitable 100% of the time through risk control.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'When in doubt, size down. You can always size up later.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'A small loss today prevents a large loss tomorrow.',
        'author': 'Unknown',
        'category': 'risk',
    },

    # ===== TRADING PROCESS (15 quotes) =====
    {
        'quote': 'A trade without a plan is just gambling with charts.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Write down your trade plan, or it\'s just a wish.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'The best entry in the world won\'t save a trade without a proper exit strategy.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Trade what you see, not what you think.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'If you don\'t know where to exit, you have no business entering.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Your trading system should work in both bull and bear markets. If it doesn\'t, keep looking.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'The best traders have the fewest decisions to make. Simplicity beats complexity.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'A good trade setup is like a good wave - you wait for it, ride it, and get out before it crashes.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Don\'t add to a losing position. That\'s like digging a hole deeper to get out of it.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'The trend is your friend until it ends - and it always ends.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Trade with the trend until the trend bends.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'Your trading rules are like a fence - they keep you safe inside the right path.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'If you break your trading rules once, breaking them again becomes easier.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'The market rewards consistency, not heroism.',
        'author': 'Unknown',
        'category': 'discipline',
    },
    {
        'quote': 'There\'s no such thing as a "sure thing" in trading. Anyone who promises one is selling something.',
        'author': 'Unknown',
        'category': 'discipline',
    },

    # ===== MINDSET & PHILOSOPHY (15 quotes) =====
    {
        'quote': 'In trading, you don\'t get what you want, you get what you are.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market is like the ocean - you can\'t control it, but you can learn to navigate it.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Successful traders think in probabilities, not certainties.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your mindset should be: "I will be here tomorrow" rather than "I need to make it all today."',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market has no interest in your financial goals. It only moves for its own reasons.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Trading is 10% strategy and 90% staring at charts doing nothing.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The best traders are like cats - they wait patiently and pounce only when the time is right.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your trading account is a report card on your psychological state.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Don\'t wish the market would give you more. Wish you had more patience.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The market is a great teacher, but it charges expensive tuition.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'In trading, humility is not a weakness - it\'s survival instinct.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The moment you think you\'ve figured out the market, it changes just to humble you.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Trading is not about being right - it\'s about making money when you\'re right and losing little when wrong.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'The stock market is the only store where when things go on sale, everyone runs away.',
        'author': 'Unknown',
        'category': 'mindset',
    },
    {
        'quote': 'Your greatest enemy in trading is the person you see in the mirror.',
        'author': 'Unknown',
        'category': 'mindset',
    },

    # ===== PATIENCE AND TIMING (15 quotes) =====
    {
        'quote': 'The best trade is sometimes the one you don\'t take.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Patience in trading means waiting for the ball to come into your sweet spot, not swinging at everything.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The market gives endless opportunities. You don\'t need to catch them all.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Time in the market beats timing the market.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The money is made while sitting, not while trading.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'If you\'re bored while waiting for setups, you\'re doing it right.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The urge to trade every day is the urge to lose money every day.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Markets move in cycles. Patience allows you to ride the full cycle.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Good things come to those who wait. Great things come to those who wait for the right setup.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The difference between a trade and a gamble is patience.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'When you force a trade, the market forces you out with a loss.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Trees don\'t grow to the sky, and markets don\'t move in straight lines. Be patient for the pullback.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The market will eventually come to your price if you\'re patient. If you\'re not, you\'ll chase it higher.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'Patience is not waiting for the market to give you something. It\'s waiting for yourself to be ready.',
        'author': 'Unknown',
        'category': 'patience',
    },
    {
        'quote': 'The biggest profits come to those who can wait for them to mature.',
        'author': 'Unknown',
        'category': 'patience',
    },

    # ===== MONEY MANAGEMENT (10 quotes) =====
    {
        'quote': 'Your first job as a trader is to protect what you have, not to make what you don\'t have.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Money management is the art of staying in the game long enough to win.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Never add to a losing position. Only add to winners.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The size of your position should be inversely proportional to the difficulty of the setup.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Preserve your capital like it\'s the last money you\'ll ever have.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Don\'t let a winning trade turn into a losing one by moving your stop loss.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The goal is to have small losses and big wins, not the other way around.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Take profits to someone else\'s greed, not your own.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'Never turn a scalp into a swing trade just because you\'re greedy.',
        'author': 'Unknown',
        'category': 'risk',
    },
    {
        'quote': 'The best traders know when to hold and when to fold, but more importantly, they know the difference.',
        'author': 'Unknown',
        'category': 'risk',
    },

    # ===== FINAL WISDOM (15 quotes) =====
    {
        'quote': 'Trading is simple: cut losses, let winners run, and do it consistently for years.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The market has a way of finding your weakest psychological point and attacking it.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Every trader gets what they deserve in the long run. The market is perfectly fair that way.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'If you can\'t take a small loss, you\'ll be forced to take a big one.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The market is never wrong. Opinions are.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Don\'t confuse a bull market with brains.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'In trading, survival is winning. Everything else is just details.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The market will teach you lessons whether you want to learn them or not. The tuition is non-refundable.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Good trades can feel bad at entry. Bad trades can feel good at entry. Feelings are not facts.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The goal is not to predict the future, but to react properly to the present.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Trading is a marathon, not a sprint. Pace yourself.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The market rewards those who respect it and punishes those who don\'t.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'Your trading journal is the mirror to your trading soul. Look into it often.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'The best traders are not the ones who never lose, but the ones who lose well.',
        'author': 'Unknown',
        'category': 'trading',
    },
    {
        'quote': 'In the end, trading is not about beating the market. It\'s about beating yourself.',
        'author': 'Unknown',
        'category': 'trading',
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