from pycoingecko import CoinGeckoAPI
import datetime
import smtplib, ssl
import requests
from time import time, sleep

# NOTE: All prices are in USD
EXCHANGE_IDS = 'binance,pancakeswap_new,uniswap,uniswap_v2,binance_us,sushiswap'

# Parameters to determine whether the coin
# matches our tracking criteria
RUN_EVERY_SECONDS = 61 # 60seconds * 30mins
MIN_MARKET_CAP = 1000000
MAX_MARKET_CAP = 1000000000
HOURLY_PERCENTAGE_CHANGE = 7
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
                    and abs(coin['price_change_percentage_1h_in_currency']) > HOURLY_PERCENTAGE_CHANGE:
                trackable_coins.append(coin)
    return trackable_coins

def filter_coins_for_arbitrage(coins):
    TIME_TO_WAIT_PER_COINS_PER_BATCH = 80
    MAX_COINS_PER_BATCH = 40
    result = []
    print(len(coins))
    for i in range(-(-len(coins) // MAX_COINS_PER_BATCH)):
        for y in range(min(MAX_COINS_PER_BATCH, abs(len(coins) - i*MAX_COINS_PER_BATCH))):
            if (i*50 + y > len(coins)): # Exceeds max length
                continue
            coin_id = coins[i*MAX_COINS_PER_BATCH + y]
            coin_data = cg.get_coin_ticker_by_id(id=coin_id, exchange_ids=EXCHANGE_IDS)
            binance_price = -1
            binance_identifier = ''
            binance_trade_pair = ''
            lowest_dex_price = float('inf')
            lowest_dex_identifier = ''
            lowest_dex_trade_pair = ''
            highest_dex_price = float('-inf')
            highest_dex_identifier = ''
            highest_dex_trade_pair = ''
            for ticker_data in coin_data['tickers']:
                # Update binance price if found
                if 'binance' in ticker_data['market']['name'].lower():
                    binance_price = ticker_data['converted_last']['usd']
                    binance_identifier = ticker_data['market']['identifier']
                    binance_trade_pair = ticker_data['target'] + ' ' + ticker_data['base']
                elif 'swap' in ticker_data['market']['name'].lower():
                    ticker_price = ticker_data['converted_last']['usd']
                    if ticker_price < lowest_dex_price:
                        lowest_dex_price = ticker_price
                        lowest_dex_identifier = ticker_data['market']['identifier']
                        lowest_dex_trade_pair = ticker_data['target'] + ' ' + ticker_data['base']
                    if ticker_price > highest_dex_price:
                        highest_dex_price = ticker_price
                        highest_dex_identifier = ticker_data['market']['identifier']
                        highest_dex_trade_pair = ticker_data['target'] + ' ' + ticker_data['base']
            if binance_price == -1 or lowest_dex_price == float('inf') or lowest_dex_price == 0: continue
            if (abs(lowest_dex_price - binance_price) / lowest_dex_price) * 100 > EXCHANGE_PRICE_PERCENTAGE_DIFFERENCE:
                result.append({
                    'coin_id': coin_id,
                    'binance_price': binance_price,
                    'dex_price': lowest_dex_price,
                    'dex_identifier': lowest_dex_identifier,
                    'binance_identifier': binance_identifier,
                    'binance_pair': binance_trade_pair,
                    'lowest_dex_trade_pair': lowest_dex_trade_pair
                })
            elif (abs(highest_dex_price - binance_price) / binance_price) * 100 > EXCHANGE_PRICE_PERCENTAGE_DIFFERENCE\
                    and lowest_dex_identifier != highest_dex_identifier:
                result.append({
                    'coin_id': coin_id,
                    'binance_price': binance_price,
                    'dex_price': highest_dex_price,
                    'dex_identifier': highest_dex_identifier,
                    'binance_identifier': binance_identifier,
                    'binance_pair': binance_trade_pair,
                    'highest_dex_trade_pair': highest_dex_trade_pair
                })
        sleep(TIME_TO_WAIT_PER_COINS_PER_BATCH)
    return result


def get_binance_coins(numb_pages=15):
    all_coins = []
    for i in range(numb_pages):
        coins = cg.get_exchanges_tickers_by_id(id='binance', page=i)['tickers']
        for coin in coins:
            all_coins.append(coin['coin_id'])

    return all_coins

# TODO: why does this produce duplicate coins (uma 2x for example)
def filter_coins_from_binance(coins):
    TIME_TO_WAIT_PER_COINS_PER_BATCH = 80
    MAX_COINS_PER_BATCH = 40
    result = []
    for i in range(-(-len(coins) // MAX_COINS_PER_BATCH)):
        for y in range(min(MAX_COINS_PER_BATCH, abs(len(coins) - i*MAX_COINS_PER_BATCH))):
            if (i*50 + y > len(coins)): # Exceeds max length
                continue
            coin_id = coins[i*MAX_COINS_PER_BATCH + y]
            coin_data = cg.get_coin_by_id(id=coin_id)
            coin_market_cap = float(coin_data['market_data']['market_cap']['usd'])
            print(coin_id)
            print(coin_market_cap)
            print(coin_data['asset_platform_id'] == 'ethereum')
            if coin_data['asset_platform_id'] == 'ethereum' and \
                    coin_market_cap >= MIN_MARKET_CAP and coin_market_cap <= MAX_MARKET_CAP:
                result.append(coin_id)
        sleep(TIME_TO_WAIT_PER_COINS_PER_BATCH)
    return result

def read_in_filtered_coins_from_file(file_name='filtered_coins.txt'):
    with open(file_name) as f:
        coins = f.read().splitlines()
    return list(set(coins))


def send_email(message):
    send_result = requests.post(
        "https://api.mailgun.net/v3/sandbox760d004ecf7241e0bb41c7d45be670ef.mailgun.org/messages",
        auth=("api", "4dcad89c5dc39d0616b09e79c7b7c971-30b9cd6d-84bb03e0"),
        data={
            "from": "Mailgun Sandbox <postmaster@sandbox760d004ecf7241e0bb41c7d45be670ef.mailgun.org>",
            "to": RECEIVER_EMAILS,
            "subject": "Crypto ARBITRAGE Report",
            "text": message
        }
    )

def sendEmailWithCoinData(coins):
    message = ''
    coins_parsed = []
    # Convert coins to formatted string
    for coin in coins:
        message = message + 'COIN_ID: ' + str(coin['coin_id']) + ' | Binance Price: ' + str(coin['binance_price']) \
                  + ' | Dex Price: ' + str(coin['dex_price']) + ' | Dex Identifier: ' \
                  + str(coin['dex_identifier']) + ' | Binance Identifier: ' + str(coin['binance_identifier']) + '\n'
    send_email(message)

SLEEP_TIME_BETWEEN_BINANCE_AND_ANALYSIS = 70
def execute_algorithm(coins):
    arbitraged_coins = filter_coins_for_arbitrage(coins)
    print(arbitraged_coins)
    if len(arbitraged_coins) > 0:
        sendEmailWithCoinData(arbitraged_coins)

if __name__ == '__main__':
    coins = read_in_filtered_coins_from_file()
    # Loop to control algorithm with pause to reset API limit
    while True:
        execute_algorithm(coins)
        sleep(RUN_EVERY_SECONDS - time() % RUN_EVERY_SECONDS)


def generate_trackable_coins():
    '''
    Creates trackable coins and outputs to filtered_coins.txt
    '''
    binance_coins = get_binance_coins()

    print(len(binance_coins))
    sleep(SLEEP_TIME_BETWEEN_BINANCE_AND_ANALYSIS)
    filter_binance_coins = filter_coins_from_binance(binance_coins)
    filter_binance_coins = list(set(filter_binance_coins)) # remove duplicates
    print(len(filter_binance_coins))
    with open('filtered_coins.txt', 'w') as f:
        for item in filter_binance_coins:
            f.write("%s\n" % item)