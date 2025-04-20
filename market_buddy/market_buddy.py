print('Initializing...')

import json
import time
import random
import requests
from lxml import html
from fuzzywuzzy import fuzz
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyperclip

from prettytable import PrettyTable

# Hack to make it python 2 compatible
try:
   input = raw_input
except NameError:
   pass

def median(lst):
    n = len(lst)
    if n < 1:
            return None
    if n % 2 == 1:
            return sorted(lst)[n//2]
    else:
            return sum(sorted(lst)[n//2-1:n//2+1])/2.0


# def exit_handler():
#     print('Logging out of wf.market')

# atexit.register(exit_handler)

CHAT_LIMIT = 180

try:
    # Cookie string (taken from a request in browser)
    with open('secret.txt') as secret_file:
        cookie = secret_file.read()

except:
    print('WARNING: YOU HAVE NOT SET YOUR COOKIE AND THEREFORE CANNOT PLACE ORDERS ON YOUR ACCOUNT!')
    print('See this video for instructions on finding your cookie (~2 minutes to do).')
    print('https://www.youtube.com/watch?v=OwxMjCmbx_g')
    cookie = input('Enter cookie: ')
    with open('secret.txt', 'w+') as secret_file:
        secret_file.write(cookie)
    print('Initializing...')


client = requests.session()
client.headers.update({'cookie': cookie})

HOME = 'https://warframe.market/'
r = client.get(HOME)
tree = html.fromstring(r.text)
csrf = tree.xpath('//meta[@name="csrf-token"]/attribute::content')[0]
client.headers.update({'x-csrftoken': csrf})

item_list = json.loads(client.get('https://api.warframe.market/v1/items').text)['payload']['items']

user_name = json.loads(client.get('https://api.warframe.market/v1/profile').text)['profile']['ingame_name']

# async def update_login_status(status):
#     async with websockets.connect("wss://warframe.market/socket") as websocket:
#         await websocket.send(status)

# asyncio.get_event_loop().run_until_complete(
#     update_login_status('ingame'))

# print(client.get('https://api.warframe.market/v1/profile/emernic').text)

print('Welcome to Market Buddy! Your friendly companion for Warframe trading!')
print('Market Buddy is mostly a super speedy way of interacting with wf.market.')
print('Type "help" to see a list of possible commands :)')

while True:

    print("")

    commands = input("Enter commands: ")
    
    commands = commands.replace(" bp", "blueprint") #So if you search "nekros prime bp" it understands blueprint instead of set, needs testing with more item names and commands, but should be ok.
    
    if commands.upper() == 'EXIT':
        exit()

    elif commands.upper() == 'HELP':
        print(
"""
Nothing is case sensitive, and item names will find the closest match (e.g. "embeer prime" -> "Ember Prime Set".)
Examples...
-Type "help" for a list of commands (this list!)
-Type "exit" to exit the program

-Type "buy ember prime chassis" to place a wf.market order for ember prime chassis at a "reasonable" default price.
-Type "buy ember prime chassis 40p" to place a wf.market order for ember prime chassis at 40p.
-Type "buy 2 ember prime chassis 40p, volt prime set" to place a wf.market order for 2 ember prime chassis for 40p and 1 volt prime set for the default price.
-Type "sell oberon prime" to place a wf.market order for 1 oberon prime set.
-Type "sold oberon prime" to CLOSE a wf.market order for 1 oberon prime set (once you have sold it).
-Type "bought 2 ember prime chassis" to CLOSE 2 wf.market orders for ember prime chassis (once you bought them).

-Type "reprice" to adjust all current orders to default prices.
-Type "reprice ember prime chassis" to reprice just that item.

-Type "orders" to see a list of your current wf.market orders.

-Type "chat" to generate a trade chat message of your most expensive WTB and WTS orders and automatically copy it to clipboard.
-Type "chat wts" to only list items you want to sell.
-Type "chat wtb" to only list items you want to buy.

-Type "msg buy lex prime set" to generate and copy a whisper message saying you would like to buy this item.
-Type "msg sell lex prime set" to generate and copy a whisper message saying you would like to sell this item.

-Type "GR nekros prime, tigris prime, galatine prime handle" to plot a graph of the median wf.market prices for these items over the last 90 days.
-Type "PC nekros prime, tigris prime, galatine prime handle" to get the minimun selling and maximum buying prices for these items at this moment.

-Type "RH axi a1 a2 v5" to do a price check of all items that can drop from these relics.
"""
            )

    elif commands[:4].upper() == 'BUY ':
        for name in commands[4:].split(','):
            quantity = 1
            for i in name.split(' '):
                # Check if they gave a number, which should be interpreted as buy quantity.
                try:
                    quantity = int(i)
                except:
                    pass

            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item


            stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics_closed']['90days']
            median_price = median([x['median'] for x in stats[-5:]])

            orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']

            buy_orders = [x for x in orders if x['order_type'] == 'buy' and x['user']['status'] == 'ingame']
            max_plat = 0
            for order in buy_orders:
                if order['user']['status'] == 'ingame' and order['platinum'] > max_plat:
                    max_plat = order['platinum']

            # If current prices are wack, just go with the 5 day median price.
            if max_plat > 1.5*median_price or max_plat < 0.5*median_price:
                plat = round(1.1*median_price)
            else:
                plat = max_plat

            # Check if a plat value is given by user
            for i in name.split(' '):
                if 'P' in name.upper():
                    try:
                        plat = int(i[:-1])
                    except:
                        pass

            payload = {'order_type': 'buy', 'item_id': best_match_item['id'], 'platinum': plat, 'quantity': quantity}
            additional_headers = {"language": "en", "accept-language": "en-US,en;q=0.9", "platform": "pc", "origin": "https://warframe.market", "referer": "https://warframe.market/", "accept": "application/json", "accept-encoding": "gzip, deflate, br"}
            r = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
            if not (r.status_code == 200):
                payload = {'order_type': 'buy', 'item_id': best_match_item['id'], 'platinum': plat, 'quantity': quantity, 'mod_rank': 0}
                r = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
            print("PLACED BUY ORDER FOR {0} \"{1}\" AT {2}p EACH".format(quantity, best_match_item['item_name'], plat))

    elif commands[:5].upper() == 'SELL ':
        for name in commands[5:].split(','):
            quantity = 1
            for i in name.split(' '):
                # Check if they gave a number, which should be interpreted as buy quantity.
                try:
                    quantity = int(i)
                except:
                    pass

            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item

            stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics_closed']['90days']
            median_price = median([x['median'] for x in stats[-5:]])

            orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']

            buy_orders = [x for x in orders if x['order_type'] == 'sell' and x['user']['status'] == 'ingame']
            min_plat = 999999999
            for order in buy_orders:
                if order['user']['status'] == 'ingame' and order['platinum'] < min_plat:
                    min_plat = order['platinum']

            if min_plat > 1.5*median_price or min_plat < 0.5*median_price:
                plat = round(0.9*median_price)
            else:
                plat = min_plat

            # Check if a plat value is given by user
            for i in name.split(' '):
                if 'P' in name.upper():
                    try:
                        plat = int(i[:-1])
                    except:
                        pass

            payload = {'order_type': 'sell', 'item_id': best_match_item['id'], 'platinum': plat, 'quantity': quantity}
            additional_headers = {"language": "en", "accept-language": "en-US,en;q=0.9", "platform": "pc", "origin": "https://warframe.market", "referer": "https://warframe.market/", "accept": "application/json", "accept-encoding": "gzip, deflate, br"}
            r = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
            if not (r.status_code == 200):
                payload = {'order_type': 'sell', 'item_id': best_match_item['id'], 'platinum': plat, 'quantity': quantity, 'mod_rank': 0}
                r = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
            print("PLACED SELL ORDER FOR {0} \"{1}\" AT {2}p EACH".format(quantity, best_match_item['item_name'], plat))

    elif commands[:5].upper() == 'SOLD ':
        for name in commands[4:].split(','):
            quantity = 1
            for i in name.split(' '):
                # Check if they gave a number, which should be interpreted as quantity.
                try:
                    quantity = int(i)
                except:
                    pass
            quantity_left = quantity

            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item


            orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']

            selected_orders = []
            for order in orders:
                if order['item']['id'] == best_match_item['id']:
                    selected_orders.append(order)

            for order in selected_orders:
                order_quantity = order['quantity']
                while quantity_left > 0 and order_quantity > 0:
                    client.put('https://api.warframe.market/v1/profile/orders/close/{0}'.format(order['id']))
                    order_quantity -= 1
                    quantity_left -= 1
            
            if quantity > quantity_left:
                print("CLOSED {0} SELL ORDERS FOR \"{1}\"".format((quantity - quantity_left), best_match_item['item_name']))
            if quantity_left:
                print("COULD NOT FIND {0} SELL ORDERS FOR \"{1}\"".format(quantity_left, best_match_item['item_name']))

    elif commands[:7].upper() == 'BOUGHT ':
        for name in commands[4:].split(','):
            quantity = 1
            for i in name.split(' '):
                # Check if they gave a number, which should be interpreted as quantity.
                try:
                    quantity = int(i)
                except:
                    pass
            quantity_left = quantity

            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item


            orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['buy_orders']

            selected_orders = []
            for order in orders:
                if order['item']['id'] == best_match_item['id']:
                    selected_orders.append(order)

            for order in selected_orders:
                order_quantity = order['quantity']
                while quantity_left > 0 and order_quantity > 0:
                    client.put('https://api.warframe.market/v1/profile/orders/close/{0}'.format(order['id']))
                    order_quantity -= 1
                    quantity_left -= 1
            
            if quantity > quantity_left:
                print("CLOSED {0} BUY ORDERS FOR \"{1}\"".format((quantity - quantity_left), best_match_item['item_name']))
            if quantity_left:
                print("COULD NOT FIND {0} BUY ORDERS FOR \"{1}\"".format(quantity_left, best_match_item['item_name']))

    elif commands[:8].upper() == "CHAT WTB":
        orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['buy_orders']
        sorted_by_plat = sorted(orders, key=lambda x: x['platinum'], reverse=True)

        chat_message = 'WTB'
        for order in sorted_by_plat:
            order_text = order['item']['en']['item_name'] + ' ' + str(order['platinum'])
            if len(', '.join([chat_message, order_text])) <= CHAT_LIMIT:
                chat_message = ', '.join([chat_message, order_text])
                try:
                    print("Copied to clipboard: \"{0}\"".format(chat_message))
                    pyperclip.copy(chat_message)
                except:
                    print("Automatic copy to clipboard not supported on your OS")

    elif commands[:8].upper() == "CHAT WTS":
        orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']
        sorted_by_plat = sorted(orders, key=lambda x: x['platinum'], reverse=True)

        chat_message = 'WTS'
        for order in sorted_by_plat:
            order_text = order['item']['en']['item_name'] + ' ' + str(order['platinum'])
            if len(', '.join([chat_message, order_text])) <= CHAT_LIMIT:
                chat_message = ', '.join([chat_message, order_text])
                try:
                    print("Copied to clipboard: \"{0}\"".format(chat_message))
                    pyperclip.copy(chat_message)
                except:
                    print("Automatic copy to clipboard not supported on your OS")

    elif commands[:5].upper() == "CHAT":
        # TODO: Don't say wtb/wts if you dont have anything to buy or sell, and do a better job when it's an uneven split
        buy_orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['buy_orders']

        sell_orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']

        orders = buy_orders + sell_orders
        sorted_by_plat = sorted(orders, key=lambda x: x['platinum'], reverse=True)

        # Extra space for WTB and /WTS
        chars_remaining = CHAT_LIMIT - 9
        top_buy_orders = []
        top_sell_orders = []
        for order in sorted_by_plat:
            order_str = order['item']['en']['item_name'] + "-" + str(order['platinum']) + "p"
            if chars_remaining >= len(order_str) + 2:
                if order['order_type'] == 'buy':
                    top_buy_orders.append(order_str)
                else:
                    top_sell_orders.append(order_str)
                chars_remaining -= len(order_str) + 2

        chat_message = ''
        if top_buy_orders:
            chat_message += 'WTB ' + ', '.join(top_buy_orders)
            if top_sell_orders:
                chat_message += '/'
        if top_sell_orders:
            chat_message += 'WTS ' + ', '.join(top_sell_orders)

            try:
                print("Copied to clipboard: \"{0}\"".format(chat_message))
                pyperclip.copy(chat_message)
            except:
                print("Automatic copy to clipboard not supported on your OS")

    elif commands[:6].upper() == 'ORDERS':
        sell_orders = client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).json()['payload']['sell_orders']
        sell_orders_sorted = sorted(sell_orders, key=lambda x: x['platinum'], reverse=True)

        for order in sell_orders_sorted:
            print("SELL ORDER FOR {0} \"{1}\" AT {2}p EACH".format(order['quantity'], order['item']['en']['item_name'], order['platinum']))

        buy_orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['buy_orders']
        buy_orders_sorted = sorted(buy_orders, key=lambda x: x['platinum'], reverse=True)

        for order in buy_orders_sorted:
            print("BUY ORDER FOR {0} \"{1}\" AT {2}p EACH".format(order['quantity'], order['item']['en']['item_name'], order['platinum']))

    elif commands[:3].upper() == 'GR ':
        print("GRAPHING PRICES OVER TIME, PRESS CTRL+W TO CLOSE FIGURE.")
        for name in commands.split(','):
            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item

            stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics_closed']['90days']

            median_prices = [x['median'] for x in stats]
            relative_dates = range(-len(median_prices), 0)
            line = plt.plot(relative_dates, median_prices, label=best_match_item['item_name'])

        plt.ylim(ymin=0)
        box = plt.gca().get_position()
        plt.gca().set_position([box.x0, box.y0, box.width * 0.65, box.height])
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.xlabel('Day (relative to today)')
        plt.ylabel('Median trade price (plat)')
        plt.show()
        
    elif commands [:3].upper() == 'PC ':
    
        table = PrettyTable(['ITEM NAME', 'SELLING', 'BUYING'])
    
        #table.border = False
    
        for name in commands.split(','):
            best_match_item = None
            best_match = 0
            for item in item_list:
                match = fuzz.ratio(item['item_name'], name)
                if match > best_match:
                    best_match = match
                    best_match_item = item
                    
            orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
            
            # Filter out own orders before processing
            item_orders = [x for x in orders if x['user']['status'] == 'ingame' and x['user']['ingame_name'] != user_name] 
            buy_plat = 0
            sell_plat = 99999
            
            for order in item_orders:
                if order['order_type'] == 'buy':
                    # Check only platinum, user already filtered
                    if order['platinum'] > buy_plat: 
                        buy_plat = order['platinum']

                elif order['order_type'] == 'sell':
                    # Check only platinum, user already filtered
                    if order['platinum'] < sell_plat: 
                        sell_plat = order['platinum']
            #print("\n\t{0} SELLING PRICE: {1}p - BUYING PRICE: {2}p.".format(best_match_item['item_name'], sell_plat, buy_plat))
            table.add_row([best_match_item['item_name'], sell_plat, buy_plat])
        
        
        print(table)

    elif commands [:3].upper() == 'RH ':

            commands = commands [3:]

            table2 = PrettyTable(['ITEM NAME', 'PRICE'])

            url = 'http://cristobal2dam.esy.es/WDIP/query.php?tier=';

            for term in commands.split(' '):
                url = url + term.strip() +  '&name[]='

            orders = json.loads(requests.get(url).text)

            for item in orders:
                name = orders[item]['NAME']
                pl = orders[item]['PLATINUM']
                table2.add_row([name, pl])

            print(table2)

    elif commands [:7].upper() == 'MSG BUY':
    
        terms = commands[7:].strip()
        
        best_match_item = None
        best_match = 0
        for item in item_list:
            match = fuzz.ratio(item['item_name'], terms)
            if match > best_match:
                best_match = match
                best_match_item = item
                
        orders = json.loads(requests.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
        
        time.sleep(0.1) #Not sure why because I dont know much about python, but you had it above and I trust you.
        # Filter out own orders before processing
        item_orders = [x for x in orders if x['user']['status'] == 'ingame' and x['order_type'] == 'sell' and x['visible'] == True and x['user']['ingame_name'] != user_name]
        
        sell_plat = 99999
        username = None # Initialize username
        
        for order in item_orders:
             # Check only platinum, user already filtered
            if order['platinum'] < sell_plat:
                sell_plat = order['platinum']
                username = order['user']['ingame_name']
        
        if username: # Check if a suitable seller was found
            chat_message = '/w '+ username + ' Hi! I want to buy: ' + best_match_item['item_name'] + ' for ' + str(sell_plat) + ' platinum. (warframe.market)'
                           #/w Jefferson231 Hi! I want to buy: Vauban Prime Systems for 45 platinum. (warframe.market)
            try:
                print("Copied to clipboard: \"{0}\"".format(chat_message))
                pyperclip.copy(chat_message)
            except:
                print("Automatic copy to clipboard not supported on your OS")
        else:
             print(f"Could not find any sellers (other than you) for \"{best_match_item['item_name']}\".")
        
    elif commands [:8].upper() == 'MSG SELL':    
    
        terms = commands[7:].strip()
        
        best_match_item = None
        best_match = 0
        for item in item_list:
            match = fuzz.ratio(item['item_name'], terms)
            if match > best_match:
                best_match = match
                best_match_item = item
                
        orders = json.loads(requests.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
        
        time.sleep(0.1) #Not sure why because I dont know much about python, but you had it above and I trust you.
         # Filter out own orders before processing
        item_orders = [x for x in orders if x['user']['status'] == 'ingame' and x['order_type'] == 'buy' and x['visible'] == True and x['user']['ingame_name'] != user_name]
        
        buy_plat = 0
        username = None # Initialize username
        
        for order in item_orders:
             # Check only platinum, user already filtered
            if order['platinum'] > buy_plat:
                buy_plat = order['platinum']
                username = order['user']['ingame_name']
        
        if username: # Check if a suitable buyer was found
            chat_message = '/w '+ username + ' Hi! I want to sell: ' + best_match_item['item_name'] + ' for ' + str(buy_plat) + ' platinum. (warframe.market)'
            try:
                print("Copied to clipboard: \"{0}\"".format(chat_message))
                pyperclip.copy(chat_message)
            except:
                print("Automatic copy to clipboard not supported on your OS")
        else:
            print(f"Could not find any buyers (other than you) for \"{best_match_item['item_name']}\".")

    elif commands[:7].upper() == 'REPRICE':
        orders_data = json.loads(client.get(f'https://api.warframe.market/v1/profile/{user_name}/orders').text)['payload']
        all_orders = orders_data['buy_orders'] + orders_data['sell_orders']
        time.sleep(0.1)
   
        item_names = commands[7:].strip()
        items_to_reprice_ids = set()
   
        if item_names:
            # Fuzzy-match specified items to get their IDs
            for name in item_names.split(','):
                name = name.strip()
                best_match_item = None
                best_match = 0
                for item in item_list:
                    # Use lower case for matching robustness
                    match = fuzz.ratio(item['item_name'].lower(), name.lower())
                    if match > best_match:
                        best_match = match
                        best_match_item = item
                if best_match_item:
                    items_to_reprice_ids.add(best_match_item['id'])
            # Filter orders based on matched IDs
            orders_to_process = [order for order in all_orders if order['item']['id'] in items_to_reprice_ids]
        else:
            # Reprice all if no specific items given
            orders_to_process = all_orders
   
        # Group orders by item ID and order type
        grouped_orders = {}
        for order in orders_to_process:
            key = (order['item']['id'], order['order_type'])
            if key not in grouped_orders:
                grouped_orders[key] = {'orders': [], 'total_quantity': 0, 'item_details': order['item']}
            grouped_orders[key]['orders'].append(order)
            grouped_orders[key]['total_quantity'] += order['quantity']

        # Process each group
        for (item_id, order_type), group_data in grouped_orders.items():
            original_orders = group_data['orders']
            total_quantity = group_data['total_quantity']
            item_details = group_data['item_details']
            item_url_name = item_details['url_name']
            item_name = item_details['en']['item_name']

            # Get median price
            try:
                stats_response = client.get(f"https://api.warframe.market/v1/items/{item_url_name}/statistics")
                stats_response.raise_for_status() # Check for HTTP errors
                stats = stats_response.json()['payload']['statistics_closed']['90days']
                time.sleep(0.1)
                median_price = median([x['median'] for x in stats[-5:]])
                if median_price is None:
                    print(f"WARN: Could not determine median price for \"{item_name}\". Skipping reprice for this item.") # Adjusted indentation
                    continue
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Failed to get statistics for \"{item_name}\": {e}. Skipping reprice.") # Adjusted indentation
                time.sleep(0.1)
                continue
            except KeyError:
                print(f"WARN: Unexpected statistics data format for \"{item_name}\". Skipping reprice.") # Adjusted indentation
                continue

            # Get current market orders
            try:
                market_orders_response = client.get(f"https://api.warframe.market/v1/items/{item_url_name}/orders")
                market_orders_response.raise_for_status()
                market_orders = market_orders_response.json()['payload']['orders']
                time.sleep(0.1)
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Failed to get market orders for \"{item_name}\": {e}. Skipping reprice.") # Adjusted indentation
                time.sleep(0.1)
                continue
            except KeyError:
                print(f"WARN: Unexpected market order data format for \"{item_name}\". Skipping reprice.") # Adjusted indentation
                continue

            # Calculate new price based on type
            plat = 0
            if order_type == 'buy':
                # Find max buy price among other active users
                competing_buy_prices = [o['platinum'] for o in market_orders if o['order_type'] == 'buy' and o['user']['status'] == 'ingame' and o['user']['ingame_name'] != user_name]
                max_plat = max(competing_buy_prices) if competing_buy_prices else 0
                # Use median price as a fallback/sanity check
                default_plat = round(median_price * 1.1)
                # If current prices are wack, just go with the default price.
                if not competing_buy_prices or max_plat > 1.5*median_price or max_plat < 0.5*median_price:
                    plat = default_plat
                else:
                    plat = max_plat

            else:  # sell order
                # Find min sell price among other active users
                competing_sell_prices = [o['platinum'] for o in market_orders if o['order_type'] == 'sell' and o['user']['status'] == 'ingame' and o['user']['ingame_name'] != user_name]
                min_plat = min(competing_sell_prices) if competing_sell_prices else 999999999 # High default if no sellers
                # Use median price as fallback/sanity check
                default_plat = round(median_price * 0.9)
                # If current prices are wack, just go with the default price.
                if not competing_sell_prices or min_plat > 1.5*median_price or min_plat < 0.5*median_price:
                    plat = default_plat
                else:
                    plat = min_plat

            # Check if the existing order already matches the target price and quantity
            if len(original_orders) == 1 and \\
               original_orders[0]['platinum'] == plat and \\
               original_orders[0]['quantity'] == total_quantity:
               continue # Skip to the next item group

            # Close original orders for this group
            closed_count = 0
            for order in original_orders:
                try:
                    close_response = client.put(f'https://api.warframe.market/v1/profile/orders/close/{order["id"]}')
                    time.sleep(0.1)
                    closed_count += 1
                except requests.exceptions.RequestException as e:
                    print(f"WARN: Failed to close order {order['id']}: {e}")
                    time.sleep(0.1)
            if closed_count < len(original_orders):
                 print(f"WARN: Only closed {closed_count}/{len(original_orders)} orders successfully.")

            # Create the new consolidated order
            payload = {
                'order_type': order_type,
                'item_id': item_id,
                'platinum': plat,
                'quantity': total_quantity
            }
            additional_headers = {
                "language": "en", "accept-language": "en-US,en;q=0.9", "platform": "pc",
                "origin": "https://warframe.market", "referer": "https://warframe.market/",
                "accept": "application/json", "accept-encoding": "gzip, deflate, br"
            }

            try:
                post_response = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
                time.sleep(0.1)
                if post_response.status_code != 200:
                    payload['mod_rank'] = 0
                    post_response = client.post('https://api.warframe.market/v1/profile/orders', headers=additional_headers, json=payload)
                    time.sleep(0.1)

                if post_response.status_code == 200:
                     print(f'REPRICED {order_type.upper()} ORDER FOR {total_quantity}x "{item_name}" TO {plat}p')
                else:
                    print(f'ERROR: Failed to create new order for "{item_name}" after retry. Status: {post_response.status_code}, Response: {post_response.text}')

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Failed to post new order for \"{item_name}\": {e}")
                time.sleep(0.1)

    else:
        print("Couldn't recognize the command, if you need help, you can type \"Help\" to get a list of commands.")
