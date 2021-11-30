from pycoingecko import CoinGeckoAPI
import datetime
import smtplib, ssl
import requests
from time import time, sleep

# NOTE: All prices are in USD


# Parameters to determine whether the coin
# matches our tracking criteria
RUN_EVERY_SECONDS = 61 # 60seconds * 30mins
MIN_MARKET_CAP = 1000000
MAX_MARKET_CAP = 2000000000
HOURLY_PERCENTAGE_INCREASE_NEEDED = 7
EXCHANGE_PRICE_PERCENTAGE_DIFFERENCE = 10

# FOR SENDING EMAILS
SENDER_EMAIL = "trollmemes2003@gmail.com"
RECEIVER_EMAILS = ["tejascryptomoon@gmail.com", "tejassharma08@gmail.com"]

cg = CoinGeckoAPI()

def get_trackable_coins_from_coins_list(pages=30, coins_per_page=250):
    trackable_coins = []
    # Call the API for the # of pages we want
    for i in range(1, pages):
        data = cg.get_ex(vs_currency='usd', page=i, price_change_percentage='1h')
        for coin in data:
            print(coin)
            if coin['market_cap'] == 0 or coin['total_volume'] == 0 or not coin['price_change_percentage_1h_in_currency']:
                continue
            volume_to_market_cap_ratio = coin['total_volume'] / coin['market_cap']
            # print(coin['id'] + " | " + str(volume_to_market_cap_ratio) + " | " + str(coin['total_volume']) + " | " + str(coin['market_cap']))
            if volume_to_market_cap_ratio >= 0.01 and volume_to_market_cap_ratio <= 0.1 and coin['total_volume'] >= MIN_TOTAL_VOLUME and coin['total_volume'] <= MAX_TOTAL_VOLUME and coin['market_cap'] <= MAX_MARKET_CAP\
                    and coin['price_change_percentage_1h_in_currency'] > HOURLY_PERCENTAGE_INCREASE_NEEDED:
                trackable_coins.append(coin)
    return trackable_coins

def filter_coins_for_arbitrage(coins):
    MAX_COINS = 3
    result = []
    for coin_id in coins[0:MAX_COINS]:
        coin_data = cg.get_coin_by_id(id=coin_id)
        coin_market_cap = float(coin_data['market_data']['market_cap']['usd'])
        coin_symbol = coin_data['symbol'].lower()
        print(coin_id)
        if True:
        # if coin_market_cap >= MIN_MARKET_CAP and coin_market_cap <= MAX_MARKET_CAP:
        #         # and coin_data['market_data']['price_change_percentage_1h_in_currency']['usd'] > HOURLY_PERCENTAGE_INCREASE_NEEDED:
            binance_price = -1
            binance_identifier = ''
            lowest_dex_price = float('inf')
            lowest_dex_identifier = ''
            lowest_dex_trade_pair = ''
            highest_dex_price = float('-inf')
            highest_dex_identifier = ''
            highest_dex_trade_pair = ''
            for ticker_data in coin_data['tickers']:
                # Update binance price if found
                if 'binance' in ticker_data['market']['name'].lower() and ticker_data['target'] == 'USD':
                    binance_price = ticker_data['converted_last']['usd']
                    binance_identifier = ticker_data['market']['identifier']
                elif 'swap' in ticker_data['market']['name'].lower():
                    ticker_price = ticker_data['converted_last']['usd']
                    if ticker_price < lowest_dex_price:
                        lowest_dex_price = ticker_price
                        lowest_dex_identifier = ticker_data['market']['identifier']
                        lowest_dex_trade_pair = ticker_data['target'] if ticker_data['base'].lower() == coin_symbol else \
                            ticker_data['base']
                    if ticker_price > highest_dex_price:
                        highest_dex_price = ticker_price
                        highest_dex_identifier = ticker_data['market']['identifier']
                        highest_dex_trade_pair = ticker_data['target'] if ticker_data['base'].lower() == coin_symbol else \
                            ticker_data['base']
            if binance_price == -1 or lowest_dex_price == float('inf'): continue
            print('Lowest dex price: ' + str(lowest_dex_price))
            print('Dex identifier: ' + str(lowest_dex_identifier))
            print('Trade pair: ' + lowest_dex_trade_pair)
            print('Binance price: ' + str(binance_price))
            print('Highest dex price: ' + str(highest_dex_price))
            print('Dex identifier: ' + str(highest_dex_identifier))
            print('Trade pair: ' + highest_dex_trade_pair)
            if (abs(lowest_dex_price - binance_price) / binance_price) * 100 > EXCHANGE_PRICE_PERCENTAGE_DIFFERENCE:
                result.append({
                    'coin_id': coin_id,
                    'binance_price': binance_price,
                    'dex_price': lowest_dex_price,
                    'dex_identifier': lowest_dex_identifier,
                    'binance_identifier': binance_identifier
                })
            if (abs(highest_dex_price - binance_price) / binance_price) * 100 > EXCHANGE_PRICE_PERCENTAGE_DIFFERENCE:
                result.append({
                    'coin_id': coin_id,
                    'binance_price': binance_price,
                    'dex_price': highest_dex_price,
                    'dex_identifier': highest_dex_identifier,
                    'binance_identifier': binance_identifier
                })
    return result


def get_binance_filtered_coins(numb_pages=6):
    all_coins = []
    for i in range(numb_pages):
        coins = cg.get_exchanges_tickers_by_id(id='binance', page=i)['tickers']
        for coin in coins:
            all_coins.append(coin['coin_id'])
    return all_coins

# def sendEmailWithCoinData(coins):
#     message = ''
#
#     binance_coins = getBinanceCoins()
#
#     # check if any of the coins are in binance coins
#     for coin in coins:
#         if coin['id'] in binance_coins:
#             message = 'BINANCE COIN: ' + message + str(coin['id']) + ' ' + str(coin['symbol']) + ' ' \
#                       + str(coin['price_change_percentage_1h_in_currency']) + '\n'
#     # build the message
#     for coin in coins:
#         message = message + str(coin['id']) + ' ' + str(coin['symbol']) + ' ' + str(coin['name']) + ' --- ' + str(coin['price_change_percentage_1h_in_currency'])  + '\n'
#
#     send_email(message)

def send_email(message):
    send_result = requests.post(
        "https://api.mailgun.net/v3/sandbox760d004ecf7241e0bb41c7d45be670ef.mailgun.org/messages",
        auth=("api", "4dcad89c5dc39d0616b09e79c7b7c971-30b9cd6d-84bb03e0"),
        data={
            "from": "Mailgun Sandbox <postmaster@sandbox760d004ecf7241e0bb41c7d45be670ef.mailgun.org>",
            "to": RECEIVER_EMAILS,
            "subject": "Crypto Report",
            "text": message
        }
    )

def get_all_coin_ids():
    coin_list = []
    raw_data = cg.get_coins_list()
    for coin in raw_data:
        coin_list.append(coin['id'])
    return coin_list

def get_coin_historical_data(id):
    data = cg.get_coin_market_chart_by_id(id=id, vs_currency='usd', days='1', interval='hourly')
    return data
def print_historical_market_chart_data(data):
    print(
        'Time' + ' | '
        'Price' + ' | '
        'Market Cap' + ' | '
        'Volume'
    )
    for i in range(0, len(data['prices'])):
        ts = int(data['prices'][i][0])
        ts = datetime.datetime.fromtimestamp(ts / 1000)
        price_data = data['prices'][i][1]
        market_cap_data = data['market_caps'][i][1]
        volume_data = data['total_volumes'][i][1]
        print(str(ts) + " | " + str(price_data) + " | " + str(market_cap_data) + " | " + str(volume_data))

SLEEP_TIME_BETWEEN_BINANCE_AND_ANALYSIS = 61
def execute_algorithm():
    # Get binance filtered coins
    filtered_binance_coins = get_binance_filtered_coins()
    print(filtered_binance_coins)
    # sleep(SLEEP_TIME_BETWEEN_BINANCE_AND_ANALYSIS)
    arbitraged_coins = filter_coins_for_arbitrage(filtered_binance_coins)
    print(arbitraged_coins)
    # sendEmailWithCoinData(filtered_binance_coins)

if __name__ == '__main__':
    # while True:
    #     sleep(RUN_EVERY_SECONDS - time() % RUN_EVERY_SECONDS)
    execute_algorithm()
