
#GLOBAL WS LIST (todo in DB)

#ARCHIVE
archive_ws_url_page ='http://boucantrin.ovh.hw.ipol.im:9000/page'
archive_ws_url_ping = 'http://boucantrin.ovh.hw.ipol.im:9000/ping'
archive_ws_url_stats = 'http://boucantrin.ovh.hw.ipol.im:9000/stats'
#BLOBS


import requests
import logging
logger = logging.getLogger(__name__)

def get_page(experimentid , page='1'):
	result = None
	wsurl = archive_ws_url_page
	try:

		params = {'demo_id': experimentid, 'page': page}
		r = requests.get(wsurl,params)
		result = r.json()
	except Exception as e:
		msg=" get_page: error=%s"%(e)
		print(msg)
		logger.error(msg)
	return result