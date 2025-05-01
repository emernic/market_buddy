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
import pandas as pd
import io
from PIL import ImageGrab, Image
import threading
import numpy as np
import os
import re

# Fix for missing ANTIALIAS in newer PIL versions
import PIL
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

import easyocr

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

# Load relic data
try:
    relics_raw = json.loads(requests.get('https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/Relics.json').text)
    relics_data = {}
    for relic in relics_raw:
        if "Intact" in relic['name']:
            # Extract just the tier and identifier (e.g., "Axi B12" from "Axi B12 Intact")
            name_parts = relic['name'].split()
            base_name = f"{name_parts[0]} {name_parts[1]}"
            relics_data[base_name] = relic
except:
    print('WARNING: Failed to load relic data')
    relics_data = {}

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

-Type "vaulted oldest" to see the 10 oldest vaulted items with pricing information.
-Type "vaulted newest" to see the 10 most recently vaulted items with pricing information.
-Type "unvaulted" to see a list of newly released Prime Warframes that are not yet vaulted, with pricing information.
-Type "inventory update" to enter screenshot monitoring mode for inventory tracking.
-Type "relics" to scan screenshots of your relic inventory give refinement recommendations.
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

            # Update inventory if it exists
            inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory.json')
            if os.path.exists(inventory_path):
                with open(inventory_path, 'r') as f:
                    inventory = json.load(f)
                
                if best_match_item['item_name'] in inventory:
                    inventory[best_match_item['item_name']] -= quantity
                    if inventory[best_match_item['item_name']] <= 0:
                        del inventory[best_match_item['item_name']]
                    
                    with open(inventory_path, 'w') as f:
                        json.dump(inventory, f, indent=4)

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

            # Update inventory if it exists
            inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory.json')
            if os.path.exists(inventory_path):
                with open(inventory_path, 'r') as f:
                    inventory = json.load(f)
                
                if best_match_item['item_name'] in inventory:
                    inventory[best_match_item['item_name']] += quantity
                else:
                    inventory[best_match_item['item_name']] = quantity
                
                with open(inventory_path, 'w') as f:
                    json.dump(inventory, f, indent=4)

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
            if (
                len(original_orders) == 1 and 
                original_orders[0]['platinum'] == plat and 
                original_orders[0]['quantity'] == total_quantity
            ):
                continue

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

    elif commands[:7].upper() == 'VAULTED':
        sub_command = commands[8:].strip().lower() if len(commands) > 8 else ''
        
        if not sub_command:
            print("Please specify a sub-command: 'vaulted oldest' or 'vaulted newest'")
            continue
            
        print("Fetching Prime Vault information...")
        try:
            # Get the data from Warframe wiki
            df = next(t for t in pd.read_html('https://warframe.fandom.com/wiki/Prime_Vault')
                  if 'Current Status' in t.columns and 'Permanent' not in ''.join(map(str, t.columns)))
            
            # Clean up the data
            df['Item Name'] = df['Item Name'].str.replace('\u00a0', ' ')  # Replace non-breaking spaces
            df['Current Status'] = df['Current Status'].map({'\u2611': 'Available', '\u2612': 'Vaulted'})
            
            # Convert date columns to datetime for proper sorting
            df['Initial Vaulting(YYYY-MM-DD)'] = pd.to_datetime(df['Initial Vaulting(YYYY-MM-DD)'])
            df['Last Resurgence(YYYY-MM-DD)'] = pd.to_datetime(df['Last Resurgence(YYYY-MM-DD)'], errors='coerce')
            
            # Create a new column for sorting - use Last Resurgence if available, otherwise use Initial Vaulting
            df['Sort Date'] = df['Last Resurgence(YYYY-MM-DD)'].fillna(df['Initial Vaulting(YYYY-MM-DD)'])
            
            # Sort by the new column (oldest first)
            sorted_df = df.sort_values('Sort Date')
            
            # Handle sub-commands to limit output
            if sub_command in ['oldest', 'old']:
                display_df = sorted_df.head(20)  # Show first 20 (oldest)
            elif sub_command in ['newest', 'new']:
                display_df = sorted_df.tail(20)  # Show last 20 (newest)
            else:
                print(f"Unknown sub-command: '{sub_command}'. Please use 'oldest' or 'newest'.")
                continue
            
            # Create a pretty table
            table = PrettyTable()
            table.field_names = ["Item Name", "Type", "Status", "Initial Vaulting", "Last Resurgence", "Current", "vs 90d Low", "vs 90d High"]
            
            # Add rows to the table
            for _, row in display_df.iterrows():
                item_name = row['Item Name']
                item_type = row['Item Type']
                status = row['Current Status']
                initial_vaulting = row['Initial Vaulting(YYYY-MM-DD)'].strftime('%Y-%m-%d')
                last_resurgence = row['Last Resurgence(YYYY-MM-DD)'].strftime('%Y-%m-%d') if pd.notna(row['Last Resurgence(YYYY-MM-DD)']) else "N/A"
                
                # Find the item in the item_list to get its url_name
                best_match_item = None
                best_match = 0
                for item in item_list:
                    match = fuzz.ratio(item['item_name'], item_name + " Set")
                    if match > best_match:
                        best_match = match
                        best_match_item = item
                
                # Initialize price data
                current_price = "N/A"
                vs_low_price = "N/A"
                vs_high_price = "N/A"
                
                if best_match_item and best_match > 80:  # Ensure we have a good match
                    try:
                        # Fetch statistics for the item
                        stats_response = client.get(f"https://api.warframe.market/v1/items/{best_match_item['url_name']}/statistics")
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            
                            # Extract statistics from the response
                            if 'payload' in stats_data and 'statistics_closed' in stats_data['payload'] and '90days' in stats_data['payload']['statistics_closed']:
                                stats = stats_data['payload']['statistics_closed']['90days']
                                if stats:
                                    # Get current price (median of last 5 days)
                                    current_median = median([x['median'] for x in stats[-5:] if 'median' in x and x['median'] is not None])
                                    
                                    # Get 90-day low and high
                                    all_medians = [x['median'] for x in stats if 'median' in x and x['median'] is not None]
                                    
                                    if current_median is not None and all_medians:
                                        current_price = f"{int(current_median)}p"
                                        
                                        # Calculate relative differences using 3rd lowest and 3rd highest instead of min/max
                                        sorted_medians = sorted(all_medians)
                                        
                                        # Use 3rd lowest and 3rd highest if we have enough data points
                                        if len(sorted_medians) >= 5:
                                            min_price = sorted_medians[2]  # 3rd lowest
                                            max_price = sorted_medians[-3]  # 3rd highest
                                        else:
                                            # Fall back to min/max for small datasets
                                            min_price = min(sorted_medians)
                                            max_price = max(sorted_medians)
                                        
                                        vs_low = int(current_median - min_price)
                                        vs_high = int(current_median - max_price)
                                        
                                        # Format with + or - sign
                                        vs_low_price = f"+{vs_low}p" if vs_low > 0 else f"{vs_low}p"
                                        vs_high_price = f"+{vs_high}p" if vs_high > 0 else f"{vs_high}p"
                                    else:
                                        current_price = "N/A"
                        
                        # Add a small delay to avoid hitting rate limits
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Warning: Could not fetch price data for {item_name}: {e}")
                
                table.add_row([item_name, item_type, status, initial_vaulting, last_resurgence, 
                              current_price, vs_low_price, vs_high_price])
            
            # Set table formatting
            table.align = "l"  # Left-align text
            table.max_width = 120  # Prevent overly wide tables
            
            # Print the table
            print(table)
            
        except Exception as e:
            print(f"An error occurred: {e}")

    elif commands[:9].upper() == 'UNVAULTED':
        print("Fetching Prime Warframe release information...")
        try:
            # Get the Prime Warframes table (index 2 based on inspection)
            tables = pd.read_html('https://warframe.fandom.com/wiki/Warframes_Comparison/Release_Dates')
            df = tables[2]
            
            # Convert date to datetime for sorting
            df['Release Date (yyyy-mm-dd)'] = pd.to_datetime(df['Release Date (yyyy-mm-dd)'])
            
            # Sort by release date, newest first
            sorted_df = df.sort_values('Release Date (yyyy-mm-dd)', ascending=False)
            
            # Create a pretty table
            table = PrettyTable()
            table.field_names = ["Warframe Name", "Release Date", "Current", "vs 90d Low", "vs 90d High"]
            
            # Process rows until the first "Vaulted" entry
            for _, row in sorted_df.iterrows():
                if row['Vaulted'] == 'Vaulted':
                    break
                    
                warframe_name = row['Warframe Name']
                release_date = row['Release Date (yyyy-mm-dd)'].strftime('%Y-%m-%d')
                
                # Find the item in the item_list to get its url_name
                best_match_item = None
                best_match = 0
                for item in item_list:
                    match = fuzz.ratio(item['item_name'], warframe_name + " Prime Set")
                    if match > best_match:
                        best_match = match
                        best_match_item = item
                
                # Initialize price data
                current_price = "N/A"
                vs_low_price = "N/A"
                vs_high_price = "N/A"
                
                if best_match_item and best_match > 80:  # Ensure we have a good match
                    try:
                        # Fetch statistics for the item
                        stats_response = client.get(f"https://api.warframe.market/v1/items/{best_match_item['url_name']}/statistics")
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            
                            # Extract statistics from the response
                            if 'payload' in stats_data and 'statistics_closed' in stats_data['payload'] and '90days' in stats_data['payload']['statistics_closed']:
                                stats = stats_data['payload']['statistics_closed']['90days']
                                if stats:
                                    # Get current price (median of last 5 days)
                                    current_median = median([x['median'] for x in stats[-5:] if 'median' in x and x['median'] is not None])
                                    
                                    # Get 90-day low and high
                                    all_medians = [x['median'] for x in stats if 'median' in x and x['median'] is not None]
                                    
                                    if current_median is not None and all_medians:
                                        current_price = f"{int(current_median)}p"
                                        
                                        # Calculate relative differences using 3rd lowest and 3rd highest instead of min/max
                                        sorted_medians = sorted(all_medians)
                                        
                                        # Use 3rd lowest and 3rd highest if we have enough data points
                                        if len(sorted_medians) >= 5:
                                            min_price = sorted_medians[2]  # 3rd lowest
                                            max_price = sorted_medians[-3]  # 3rd highest
                                        else:
                                            # Fall back to min/max for small datasets
                                            min_price = min(sorted_medians)
                                            max_price = max(sorted_medians)
                                        
                                        vs_low = int(current_median - min_price)
                                        vs_high = int(current_median - max_price)
                                        
                                        # Format with + or - sign
                                        vs_low_price = f"+{vs_low}p" if vs_low > 0 else f"{vs_low}p"
                                        vs_high_price = f"+{vs_high}p" if vs_high > 0 else f"{vs_high}p"
                                    else:
                                        current_price = "N/A"
                        
                        # Add a small delay to avoid hitting rate limits
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Warning: Could not fetch price data for {warframe_name}: {e}")
                
                table.add_row([warframe_name, release_date, current_price, vs_low_price, vs_high_price])
            
            # Set table formatting
            table.align = "l"  # Left-align text
            table.max_width = 120  # Prevent overly wide tables
            
            # Print the table
            print(table)
            
        except Exception as e:
            print(f"An error occurred: {e}")

    elif commands.upper() == 'INVENTORY UPDATE':
        print("Inventory update mode: Use PrtScn to take screenshots of your inventory.")
        print("Important: Wait 5 seconds between screenshots for processing!")
        print("When finished, type Y+Enter to continue (or N to cancel).")
        
        stop_monitoring = threading.Event()
        screenshots = []
        
        def monitor_clipboard():
            last_image_hash = None
            
            try:
                clipboard_image = ImageGrab.grabclipboard()
                if isinstance(clipboard_image, Image.Image):
                    last_image_hash = hash(clipboard_image.tobytes())
            except OSError:
                pass
                
            while not stop_monitoring.is_set():
                try:
                    clipboard_image = ImageGrab.grabclipboard()
                    
                    if not isinstance(clipboard_image, Image.Image):
                        continue
                    
                    # Generate hash of image data for fast comparison
                    current_hash = hash(clipboard_image.tobytes())
                    
                    # Check if the hash is different from the previous image
                    if current_hash != last_image_hash:
                        screenshots.append(clipboard_image)
                        print(f"Screenshot {len(screenshots)} detected")
                        last_image_hash = current_hash
                except OSError:
                    pass
                except Exception as e:
                    print(f"Warning: {str(e)}")
        
        monitor_thread = threading.Thread(target=monitor_clipboard)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        user_input = input().lower()
        stop_monitoring.set()
        monitor_thread.join(timeout=1.0)
        
        if user_input == 'y' and screenshots:
            print(f"\nProcessing {len(screenshots)} screenshots...")
            reader = easyocr.Reader(['en'])
            
            all_items = {}
            
            for i, screenshot in enumerate(screenshots):
                img_np = np.array(screenshot)
                height, width = img_np.shape[:2]
                results = reader.readtext(img_np)
                
                text_blocks = []
                digit_blocks = []
                
                for idx, (bbox, text, conf) in enumerate(results):
                    block = {
                        'idx': idx,
                        'text': text,
                        'center_x': sum(point[0] for point in bbox) / 4,
                        'center_y': sum(point[1] for point in bbox) / 4,
                    }
                    
                    if text.isdigit():
                        digit_blocks.append(block)
                    else:
                        text_blocks.append(block)
                
                prime_blocks = [block for block in text_blocks if 'Prime' in block['text']]
                
                items = {}
                
                for prime_block in prime_blocks:
                    associated_text = []
                    
                    for block in text_blocks:
                        if block['idx'] == prime_block['idx']:
                            continue
                        
                        x_dist = abs(block['center_x'] - prime_block['center_x'])
                        x_dist_ratio = x_dist / width
                        
                        y_dist = abs(block['center_y'] - prime_block['center_y'])
                        y_dist_ratio = y_dist / height
                        
                        is_horizontally_aligned = x_dist_ratio < 0.05
                        is_vertically_close = y_dist_ratio < 0.07
                        
                        is_above = block['center_y'] < prime_block['center_y']
                        
                        if is_horizontally_aligned and is_vertically_close:
                            position = "above" if is_above else "below"
                            associated_text.append((block, position))
                    
                    quantity = 1
                    min_dist = float('inf')
                    
                    for digit in digit_blocks:
                        is_above = digit['center_y'] < prime_block['center_y']
                        is_left = digit['center_x'] < prime_block['center_x']
                        
                        if is_above and is_left:
                            dx = abs(digit['center_x'] - prime_block['center_x'])
                            dy = abs(digit['center_y'] - prime_block['center_y'])
                            
                            # Convert to relative distances
                            dx_ratio = dx / width
                            dy_ratio = dy / height
                            
                            # Simple 2D distance using normalized coordinates
                            dist_ratio = (dx_ratio**2 + dy_ratio**2)**0.5
                            
                            if dist_ratio < 0.15 and dist_ratio < min_dist:
                                min_dist = dist_ratio
                                quantity = int(digit['text'])
                    
                    full_name = prime_block['text']
                    
                    for block, position in sorted(associated_text, key=lambda x: x[0]['center_y']):
                        if position == "above":
                            full_name = block['text'] + " " + full_name
                        else:
                            full_name += " " + block['text']
                    
                    all_items[full_name] = quantity
                
            print("\nItems detected:")
            valid_items = {}
            for name, quantity in all_items.items():
                # Try exact match first
                item_match = False
                for item in item_list:
                    if item['item_name'] == name:
                        item_match = True
                        valid_items[name] = quantity
                        print(f"{quantity} {name}")
                        break
                
                # If no exact match, try fuzzy matching with a threshold
                if not item_match:
                    best_match_item = None
                    best_match_score = 0
                    for item in item_list:
                        match_score = fuzz.ratio(item['item_name'], name)
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match_item = item
                    
                    # Only accept fuzzy matches above a reasonable threshold (85)
                    if best_match_score >= 85:
                        print(f"{best_match_item['item_name']} {quantity}")
                        valid_items[best_match_item['item_name']] = quantity
                    else:
                        print(f"WARNING: Could not find match for '{name}' in item database (best match: {best_match_item['item_name']} with score {best_match_score})")
            
            # Save inventory to JSON file
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory.json'), 'w') as f:
                json.dump(valid_items, f, indent=4)
        else:
            print("\nCancelling inventory update.")

    elif commands.upper() == 'RELICS':
        print("Relic scanning mode: Use PrtScn to take screenshots of your relic inventory.")
        print("Wait 5 seconds between screenshots for processing!")
        print("When finished, type Y+Enter to continue (or N to cancel).")
        
        stop_monitoring = threading.Event()
        screenshots = []
        
        def monitor_clipboard():
            last_image_hash = None
            
            try:
                clipboard_image = ImageGrab.grabclipboard()
                if isinstance(clipboard_image, Image.Image):
                    last_image_hash = hash(clipboard_image.tobytes())
            except OSError:
                pass
                
            while not stop_monitoring.is_set():
                try:
                    clipboard_image = ImageGrab.grabclipboard()
                    
                    if not isinstance(clipboard_image, Image.Image):
                        continue
                    
                    # Generate hash of image data for fast comparison
                    current_hash = hash(clipboard_image.tobytes())
                    
                    # Check if the hash is different from the previous image
                    if current_hash != last_image_hash:
                        screenshots.append(clipboard_image)
                        print(f"Screenshot {len(screenshots)} detected")
                        last_image_hash = current_hash
                except OSError:
                    pass
                except Exception as e:
                    print(f"Warning: {str(e)}")
        
        monitor_thread = threading.Thread(target=monitor_clipboard)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        user_input = input().lower()
        stop_monitoring.set()
        monitor_thread.join(timeout=1.0)
        
        if user_input == 'y' and screenshots:
            print(f"\nProcessing {len(screenshots)} screenshots...")
            reader = easyocr.Reader(['en'])
            
            all_relics = set()
            relic_pattern = re.compile(r'^(Lith|Neo|Meso|Axi)\s+[A-Z][0-9]+\s+Relic$')
            
            for i, screenshot in enumerate(screenshots):
                img_np = np.array(screenshot)
                results = reader.readtext(img_np)
                
                for _, text, _ in results:
                    if 'relic' in text.lower() and relic_pattern.match(text):
                        all_relics.add(text)
            
            table = PrettyTable(['Relic Name', 'Rare Drop', 'Price'])
            relic_values = []
            
            for relic_name in sorted(all_relics):
                rare_drop = "Unknown"
                rare_drop_url = None
                price = 0
                
                # Remove "Relic" from the end to match format in relics_data
                search_name = relic_name.replace(' Relic', '')
                
                # Direct dictionary lookup
                if search_name in relics_data:
                    for reward in relics_data[search_name]['rewards']:
                        if reward['rarity'] == 'Rare':
                            rare_drop = reward['item']['name']
                            if 'warframeMarket' in reward['item'] and 'urlName' in reward['item']['warframeMarket']:
                                rare_drop_url = reward['item']['warframeMarket']['urlName']
                            break
                
                # Get price for the rare item
                if rare_drop_url:
                    try:
                        orders = json.loads(client.get(f"https://api.warframe.market/v1/items/{rare_drop_url}/orders").text)['payload']['orders']
                        sell_orders = [o for o in orders if o['order_type'] == 'sell' and o['user']['status'] == 'ingame']
                        if sell_orders:
                            price = min(o['platinum'] for o in sell_orders)
                        time.sleep(0.1)
                    except:
                        pass
                
                relic_values.append((relic_name, rare_drop, price))
            
            # Sort by price (descending) and take top 10
            relic_values.sort(key=lambda x: x[2], reverse=True)
            for relic_name, rare_drop, price in relic_values[:10]:
                price_str = f"{price}p" if price > 0 else "N/A"
                table.add_row([relic_name, rare_drop, price_str])
            
            print(table)

    elif commands.upper() == 'INVENTORY SELL':
        inventory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory.json')
        if not os.path.exists(inventory_path):
            print("No inventory data found.")
            continue
            
        with open(inventory_path, 'r') as f:
            inventory = json.load(f)
            
        # Get current sell orders
        sell_orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']
        
        # Track what we're already selling
        selling_items = {}
        for order in sell_orders:
            item_name = order['item']['en']['item_name']
            selling_items[item_name] = selling_items.get(item_name, 0) + order['quantity']
        
        # Process each inventory item
        sellable_items = []
        
        for item_name, quantity in inventory.items():
            # Skip items we're already selling
            already_selling = selling_items.get(item_name, 0)
            remaining_quantity = quantity - already_selling
            
            if remaining_quantity <= 0:
                continue
                
            # Find the item in item_list by exact name
            best_match_item = None
            for item in item_list:
                if item['item_name'] == item_name:
                    best_match_item = item
                    break
                    
            if not best_match_item:
                continue
                
            # Get market data and calculate price
            try:
                stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics_closed']['90days']
                median_price = median([x['median'] for x in stats[-5:]])
                time.sleep(0.1)
                
                orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
                
                sell_orders = [x for x in orders if x['order_type'] == 'sell' and x['user']['status'] == 'ingame' and x['user']['ingame_name'] != user_name]
                min_plat = 999999999
                for order in sell_orders:
                    if order['platinum'] < min_plat:
                        min_plat = order['platinum']
                
                if min_plat > 1.5*median_price or min_plat < 0.5*median_price or min_plat == 999999999:
                    plat = round(0.9*median_price)
                else:
                    plat = min_plat
                    
                # Only include items worth at least 7 plat
                if plat >= 7:
                    sellable_items.append((item_name, remaining_quantity, plat))
                    
                time.sleep(0.1)  # Avoid hitting rate limits
            except:
                continue
        
        # Sort by price (descending)
        sellable_items.sort(key=lambda x: x[2], reverse=True)
        
        # Print sell commands
        print(f"Found {sum(x[1] for x in sellable_items)} items worth selling with no active sell orders. Worth {sum(x[2] for x in sellable_items)}p")
        print("\nSuggested sell commands (copy/paste these):")
        for item_name, quantity, price in sellable_items:
            print(f"sell {quantity} {item_name} {price}p")

    else:
        print("Couldn't recognize the command, if you need help, you can type \"Help\" to get a list of commands.")
