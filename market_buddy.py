print('Initializing...')

try:
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

except:
	print("Installing dependencies...")
	from subprocess import Popen
	p = Popen("requirements.bat")
	stdout, stderr = p.communicate()

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

item_list = json.loads(client.get('https://api.warframe.market/v1/items').text)['payload']['items']['en']

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

-Type "orders" to see a list of your current wf.market orders.

-Type "chat" to generate a trade chat message of your most expensive WTB and WTS orders and automatically copy it to clipboard.
-Type "chat WTS" to only list items you want to sell.
-Type "chat WTB" to only list items you want to buy.

-Type "GR nekros prime, tigris prime, galatine prime handle" to plot a graph of the median wf.market prices for these items over the last 90 days.
-Type "PC nekros prime, tigris prime, galatine prime handle" to get the minimun selling and maximum buying prices for these items at this moment.
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


			stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics']['90days']
			time.sleep(0.1)
			median_price = median([x['median'] for x in stats[-5:]])

			orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
			time.sleep(0.1)

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
			time.sleep(0.1)
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

			stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics']['90days']
			time.sleep(0.1)
			median_price = median([x['median'] for x in stats[-5:]])

			orders = json.loads(client.get("https://api.warframe.market/v1/items/{0}/orders".format(best_match_item['url_name'])).text)['payload']['orders']
			time.sleep(0.1)

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
			time.sleep(0.1)
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
			time.sleep(0.1)

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
			time.sleep(0.1)

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
		print("Copied to clipboard: \"{0}\"".format(chat_message))
		pyperclip.copy(chat_message)

	elif commands[:8].upper() == "CHAT WTS":
		orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']
		sorted_by_plat = sorted(orders, key=lambda x: x['platinum'], reverse=True)

		chat_message = 'WTS'
		for order in sorted_by_plat:
			order_text = order['item']['en']['item_name'] + ' ' + str(order['platinum'])
			if len(', '.join([chat_message, order_text])) <= CHAT_LIMIT:
				chat_message = ', '.join([chat_message, order_text])
		print("Copied to clipboard: \"{0}\"".format(chat_message))
		pyperclip.copy(chat_message)

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

		
		print("Copied to clipboard: \"{0}\"".format(chat_message))
		pyperclip.copy(chat_message)

	elif commands[:6].upper() == 'ORDERS':
		sell_orders = json.loads(client.get('https://api.warframe.market/v1/profile/{0}/orders'.format(user_name)).text)['payload']['sell_orders']
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

			stats = json.loads(client.get("https://api.warframe.market/v1/items/{0}/statistics".format(best_match_item['url_name'])).text)['payload']['statistics']['90days']

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
			
			time.sleep(0.1) #Not sure why because I dont know much about python, but you had it above and I trust you.

			item_orders = [x for x in orders if x['user']['status'] == 'ingame']
			buy_plat = 0
			sell_plat = 99999
			
			for order in item_orders:
				if order['order_type'] == 'buy':
					if order['user']['status'] == 'ingame' and order['platinum'] > buy_plat:
						buy_plat = order['platinum']

				elif order['order_type'] == 'sell':
					if order['user']['status'] == 'ingame' and order['platinum'] < sell_plat:
						sell_plat = order['platinum']
			#print("\n\t{0} SELLING PRICE: {1}p - BUYING PRICE: {2}p.".format(best_match_item['item_name'], sell_plat, buy_plat))
			table.add_row([best_match_item['item_name'], sell_plat, buy_plat])
		
		
		print(table)
	
	else:
		print("Couldn't recognize the command, if you need help, you can type \"Help\" to get a list of commands.")


def median(lst):
    n = len(lst)
    if n < 1:
            return None
    if n % 2 == 1:
            return sorted(lst)[n//2]
    else:
            return sum(sorted(lst)[n//2-1:n//2+1])/2.0