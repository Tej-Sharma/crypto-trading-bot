from pycoingecko import CoinGeckoAPI
import datetime
import smtplib, ssl
import requests
from time import time, sleep

# Exchanges to look at
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
# enter the emails where you want the list of coins to be sent to
# this list contains the coins that can be arbitraged for profit
RECEIVER_EMAILS = ["aaa@gmail.com", "aaa@gmail.com"]

# Init the API
cg = CoinGeckoAPI()

def get_trackable_coins_from_coins_list(pages=30, coins_per_page=250):
    '''
    Given the pages and the number of coins per page,
    call the cg API and retrieve the coins on that page.
    Then filter coins based on our desired filters.
    '''
    trackable_coins = []
    # Call the API for the # of pages we want
    for i in range(1, pages):
        data = cg.get_ex(vs_currency='usd', page=i, price_change_percentage='1h')
        for coin in data:
            # Filter out coisn by market cap, total volume, and if price went up
            if coin['market_cap'] == 0 or coin['total_volume'] == 0 or not coin['price_change_percentage_1h_in_currency']:
                continue
            volume_to_market_cap_ratio = coin['total_volume'] / coin['market_cap']
            # print(coin['id'] + " | " + str(volume_to_market_cap_ratio) + " | " + str(coin['total_volume']) + " | " + str(coin['market_cap']))
            if volume_to_market_cap_ratio >= 0.01 and volume_to_market_cap_ratio <= 0.1 and coin['total_volume'] >= MIN_TOTAL_VOLUME and coin['total_volume'] <= MAX_TOTAL_VOLUME and coin['market_cap'] <= MAX_MARKET_CAP\
                    and abs(coin['price_change_percentage_1h_in_currency']) > HOURLY_PERCENTAGE_CHANGE:
                trackable_coins.append(coin)
    return trackable_coins

def check_ticker_is_valid(ticker_data):
    '''
    Given the ticker data for an exchange in a coin
    Check if the ticker is valid and meets the criteria
    '''
    if ticker_data['converted_volume']['usd'] <= 1000: return False
    ACCEPTABLE_PAIRS = ['USDT', 'USDC', 'ETH']
    target = ticker_data['target']
    base = ticker_data['base']
    if target in ACCEPTABLE_PAIRS or base in ACCEPTABLE_PAIRS:
        return True
    else:
        return False

def filter_coins_for_arbitrage(coins):
    '''
    
    '''
    TIME_TO_WAIT_PER_COINS_PER_BATCH = 80
    MAX_COINS_PER_BATCH = 40
    result = []
    # TODO: clean up looping code to use the step function in range
    # Loop from 0 to # of batches of coins avilable
    for i in range(-(-len(coins) // MAX_COINS_PER_BATCH)):
        # For each batch, loop for the number of coins we need
        for y in range(min(MAX_COINS_PER_BATCH, abs(len(coins) - i*MAX_COINS_PER_BATCH))):
            # The current i*MAX_COINS_PER_BATCH + y would exceed the end of the array
            if (i*MAX_COINS_PER_BATCH + y > len(coins)): 
                break
            # Get the coin data and init variables
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
            # A coin can have multiple tickers (for each exchange)
            # Go through each ticker and update the above values
            for ticker_data in coin_data['tickers']:
                if not check_ticker_is_valid(ticker_data): continue
                # Update binance-related variables if found
                if 'binance' == ticker_data['market']['name'].lower():
                    binance_price = ticker_data['converted_last']['usd']
                    binance_identifier = ticker_data['market']['identifier']
                    binance_trade_pair = ticker_data['target'] + ' ' + ticker_data['base']
                # This ticker is a dex, update the dex-related variables
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
            # If a binance and a dex pair wasn't found, continue
            if binance_price == -1 or lowest_dex_price == float('inf') or lowest_dex_price == 0: continue
            # If the difference between binance and a dex is greater than the difference, we found a valid coin!
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
            # If the difference the other way is also high, still a valid coin
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
        # There is an API limit so sleep
        sleep(TIME_TO_WAIT_PER_COINS_PER_BATCH)
    return result


def get_binance_coins(numb_pages=15):
    '''
    Get the coins on the binance exchange
    '''
    all_coins = []
    for i in range(numb_pages):
        coins = cg.get_exchanges_tickers_by_id(id='binance', page=i)['tickers']
        for coin in coins:
            all_coins.append(coin['coin_id'])

    return all_coins

# TODO: why does this produce duplicate coins (uma 2x for example)
def filter_coins_from_binance(coins):
    '''
    Given the coins on binance, filter to only the ones we are
    interested in
    '''
    TIME_TO_WAIT_PER_COINS_PER_BATCH = 80
    MAX_COINS_PER_BATCH = 40
    result = []
    # Use a batching algorithm to find coins in batches
    # This is done so we can make MAX_COINS_PER_BATCH API calls
    # And then sleep to reset the API limit of 50 calls per minute
    for i in range(-(-len(coins) // MAX_COINS_PER_BATCH)):
        for y in range(min(MAX_COINS_PER_BATCH, abs(len(coins) - i*MAX_COINS_PER_BATCH))):
            if (i*50 + y > len(coins)): # Exceeds max length
                continue
            coin_id = coins[i*MAX_COINS_PER_BATCH + y]
            coin_data = cg.get_coin_by_id(id=coin_id)
            coin_market_cap = float(coin_data['market_data']['market_cap']['usd'])
            # Apply filter
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
    # Convert coins to formatted string
    for coin in coins:
        message = message + 'COIN_ID: ' + str(coin['coin_id']) + ' | Binance Price: ' + str(coin['binance_price']) \
                  + ' | Dex Price: ' + str(coin['dex_price']) + ' | Dex Identifier: ' \
                  + str(coin['dex_identifier']) + ' | Binance Identifier: ' + str(coin['binance_identifier']) + '\n'
    send_email(message)

SLEEP_TIME_BETWEEN_BINANCE_AND_ANALYSIS = 70

def execute_algorithm(coins):
    # Get possible arbitrage coins
    arbitraged_coins = filter_coins_for_arbitrage(coins)
    print(arbitraged_coins)
    # Send email of potential arbitrageable coins
    if len(arbitraged_coins) > 0:
        sendEmailWithCoinData(arbitraged_coins)

if __name__ == '__main__':
    # Read in initial coins from file
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
