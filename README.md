## Arbiter of Crypto

A crypto trading bot that uses the strategy of arbitrage to *attempt* to make a profit.

## The strategy

Arbitrage is a widely-used concept, and it's very simple in theory: you buy where it is cheap, and sell where it is expensive.

1) Buy from marketplace A for x amount
2) Sell on another marketplace B for y amount
3) Make the profit of y - x

So we can buy a coin from Binance for $10. We can sell it somewhere else for $15.
This gives us a $5 profit.

For the crypto-world, we will always keep one of the marketplaces to be Binance.
Binance is a centralized exchange where it is easy to buy, sell, and withrdaw coins for cash.

The second marketplace will be a decentralized exchange (DEX). This is a marketplace that's regulated by itself,
rather than a central authority like Binance.

We simply look for DEXes where the price is much lower or higher than Binance.

This strategy only works for coins that are highly volatile and have a low to medium volume.
Otherwise, for big coins like Ethereum, the price differences aren't too much to be profitable (given the transaction fees to buy / sell).

Ex:

Uniswap has coin C for $30. Binance has it for $20. Buy on Binance and sell on Uniswap.
Uniswap has coin C for $0.5. Binance has it for $0.75. Buy it on Binance and sell it on Uniswap.

This is the essence of the strategy. The code contains more implementation details as well as additional criteria:
- Coins to filter (by their market cap, volume, etc.)
- Percentage change to triger arbitrage (the difference between two marketplaces to denote it a profitable arbitrage)

When the algorithm finds a possible arbitrage opportunity, it sends an email to the provided emails with a list of coins
that are potential arbitrage opportunities.

## Code

`main.py` - contains the algorithm
`requirements.txt` - the modules required
`filtered_coins.txt` - a list of coins on Binance that are suitable for the algorithm
`Procfile` and `runtime.txt` - Files for deploying the script to Heroku so it is continuously run

## Future improvements

I don't automatically buy and sell coins, but instead the person reading the emails must analyze the coins and do the transactions.

## Disclaimer

This was built mainly for fun to demonstrate the concept of a trading bot.
While the strategy may be viable, I doubt it would due to the high transaction fees and the neglible difference in prices.
While the algorithm works and was able to find coins, they were risky coins to buy and sell (they had very low volume), so I performed
very few transactions based on the result of this bot and made neglible profits.

Use with own risk, but I hope it was interesting :D


