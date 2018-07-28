import json
import urllib.request
import time
import numpy as np

# with open('wfm_item_list.json') as wfm_item_list_str:
# 	wfm_item_list_data = json.loads(wfm_item_list_str.read())

# print(wfm_item_list_data)

# Items which have below this many transactions per 90 day interval on wfm aren't assigned a median price (price unstable).
LOW_VOLUME_THRESHOLD = 1250
# Items which came out fewer than this many days ago aren't assigned a median price (price unstable).
MIN_DAYS_AVAILABLE = 50
# Store the average median daily price from the last AVERAGE_OVER days.
AVERAGE_OVER = 10


item_list = json.loads(urllib.request.urlopen("https://api.warframe.market/v1/items").read())['payload']['items']['en']
print(item_list)

wf_item_list_high_vol = []

for item in item_list:
	try:
		stats = json.loads(urllib.request.urlopen("https://api.warframe.market/v1/items/{0}/statistics".format(item['url_name'])).read())['payload']['statistics']['90days']
		time.sleep(0.4)
		volume = np.sum([x['volume'] for x in stats])
		wf_item_list_high_vol.append(item)
		if volume > LOW_VOLUME_THRESHOLD and len(stats) > MIN_DAYS_AVAILABLE:
			median_price = np.median([x['median'] for x in stats[-AVERAGE_OVER:]])
			wf_item_list_high_vol[-1]['median_price'] = median_price
		else:
			wf_item_list_high_vol[-1]['median_price'] = None
	except:
		pass


with open('data/wf_item_list_high_vol.json', 'w') as fout:
	fout.write(json.dumps(wf_item_list_high_vol))