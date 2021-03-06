#!/usr/bin/python
# -*- coding: utf-8 -*-
import common
import connection
import re
import simplejson
import sys
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup

addon = xbmcaddon.Addon()
pluginHandle = int(sys.argv[1])

SITE = "food"
NAME = "Food Network"
DESCRIPTION = "FOOD NETWORK (www.foodnetwork.com) is a unique lifestyle network and Web site that strives to be way more than cooking.  The network is committed to exploring new and different ways to approach food - through pop culture, competition, adventure, and travel - while also expanding its repertoire of technique-based information. Food Network is distributed to more than 96 million U.S. households and averages more than seven million Web site users monthly. With headquarters in New York City and offices in Atlanta, Los Angeles, Chicago, Detroit and Knoxville, Food Network can be seen internationally in Canada, Australia, Korea, Thailand, Singapore, the Philippines, Monaco, Andorra, Africa, France, and the French-speaking territories in the Caribbean and Polynesia. Scripps Networks Interactive (NYSE: SNI), which also owns and operates HGTV (www.hgtv.com), DIY Network (www.diynetwork.com), Great American Country (www.gactv.com) and FINE LIVING (www.fineliving.com), is the manager and general partner."
SHOWS = "http://www.foodnetwork.com/shows/a-z.html"
BASE  = "http://foodnetwork.com"
BITRATES = [600, 800, 1500, 2000, 2500, 3000]

def masterlist():
	master_db = []
	master_dict = {}
	dupes = []
	master_data = connection.getURL(SHOWS)
	master_tree =  BeautifulSoup(master_data, 'html.parser')
	master_menu = master_tree.find('div', class_ = 'shows-a-z').find_all('span', class_ = "arrow")
	for master_item in master_menu:
		try:
			master_name = master_item.a.string
			master_url = master_item.a['href']
			master_db.append((master_name, SITE, 'seasons', master_url))
		except Exception, e:
			print "Exception: ", e
	return master_db

def seasons(season_urls = common.args.url):
	seasons = []
	root_url = season_urls
	season_urls = BASE + season_urls
	season_data = connection.getURL(season_urls)
	try:
		season_tree = BeautifulSoup(season_data)
		video_link = BASE + season_tree.find('a', text = re.compile('Videos? \(\d+\)'))['href']
		season_data = connection.getURL(video_link)
		video_tree = BeautifulSoup(season_data)
		season_menu = video_tree.find_all('option')
		if season_menu:
			for season_item in season_menu:
				season_name = season_item.string
				season_url = BASE + season_item['value']
				seasons.append((season_name,  SITE, 'episodes', season_url, -1, -1))
		else:
			seasons.append(('Clips',  SITE, 'episodes', video_link, -1, -1))
	except:
		try:
			season_title = re.compile('"channels": \[\{\s+"title": "(.*?)",\s+"start": \d+,\s+"end": \d+,\s+"total": \d+,\s+"videos":', re.DOTALL).findall(season_data)[0]
			seasons.append((season_title,  SITE, 'episodes', season_urls, -1, -1))
		except:
			season_tree = BeautifulSoup(season_data)
			try:
				dropdown = season_tree.find('nav', class_ ='hub').find('span', text = 'Videos').find_next(class_ = 'dropdown-menu')
				season_menu = dropdown.find_all('a')
				for season_item in season_menu:
					seasons.append((season_item['title'],  SITE, 'episodes', BASE + season_item['href'], -1, -1))
			except:
				pass
			season_menu = season_tree.find_all(class_ = 'ss-play')
			for season_item in season_menu:
				season_grandparent = season_item.parent.parent.parent
				try:
					try:
						season_name = season_grandparent.img['title']
					except:
						season_name = season_grandparent.h6.string
					try:
						season_url = BASE + season_grandparent['href']
					except:
						season_url = BASE + season_grandparent.a['href']
					if 'shows' in season_url or 'packages' in season_url or 'chef' in season_url:
						seasons.append((season_name,  SITE, 'episodes', season_url, -1, -1))
				except:
					pass
	return seasons

def episodes(episode_url = common.args.url):
	episodes = []
	episode_data = connection.getURL(episode_url)
	episode_tree = BeautifulSoup(episode_data)
	try:
		episode_script = episode_tree.find('section', id='player-component').script.string
	except:
		episode_script = episode_tree.find('script', text=re.compile('"videos')).string
	episode_json = re.compile('"videos".+(\[.*\])\}\]', re.DOTALL).findall(episode_script)[0]
	episode_menu = simplejson.loads(episode_json)
	for episode_item in episode_menu:
		if 'SD' not in episode_item['videoFormat']:
			HD = True
		else:
			HD = False
		url = episode_item['releaseUrl']
		episode_duration = int(episode_item['length_sss'])
		episode_name = episode_item['title']
		try:
			episode_cast = [episode_item['hostName']]
		except:
			episode_cast = []
		try:
			episode_thumb = episode_item['thumbnailUrl']
		except:
			episode_thumb = None
		episode_plot = episode_item['description']
		show_title = episode_item['showName']
		if episode_duration < 500:
			episode_type = 'Clip'
		else:
			episode_type = 'Full Episode'
		if url is not None:
			u = sys.argv[0]
			u += '?url="' + urllib.quote_plus(url) + '"'
			u += '&mode="' + SITE + '"'
			u += '&sitemode="play_video"'
			infoLabels={	'title' : episode_name,
							'durationinseconds' : episode_duration,
							'plot' : episode_plot,
							'TVShowTitle': show_title,
							'cast' : episode_cast}
			episodes.append((u, episode_name, episode_thumb, infoLabels, 'list_qualities', HD, episode_type))
	return episodes
	
def list_qualities(video_url = common.args.url):
	bitrates = []
	try:
		video_data = connection.getURL(video_url)
		video_tree = BeautifulSoup(video_data, 'html.parser')
		if  video_tree.find('param', attrs = {'name' : 'isException', 'value' : 'true'}) is None:
			video_url2 = video_tree.switch.find_all('video')
			for video in video_url2:
				bitrate = video['system-bitrate']
				display = int(bitrate) / 1024
				bitrates.append((display, bitrate))
			return bitrates
		else:
			common.show_exception(video_tree.ref['title'], video_tree.ref['abstract'])
	except:
		return [(v, k) for k, v in dict(zip(BITRATES, BITRATES)).iteritems()] 

def play_video(video_url = common.args.url):
	try:
		qbitrate = common.args.quality
	except:
		qbitrate = None
	closedcaption = None
	video_url = video_url 
	video_data = connection.getURL(video_url)
	video_tree = BeautifulSoup(video_data, 'html.parser')
	sbitrate = int(addon.getSetting('quality'))
	if  video_tree.find('param', attrs = {'name' : 'isException', 'value' : 'true'}) is None:
		try:
			video_url2 = video_tree.switch.find_all('video')
			lbitrate = -1
			hbitrate = -1
			sbitrate = int(addon.getSetting('quality')) * 1024
			for video_index in video_url2:
				bitrate = int(video_index['system-bitrate'])
				if bitrate < lbitrate or lbitrate == -1:
					lbitrate = bitrate
					lplaypath_url = video_index['src']	
				if bitrate > hbitrate and bitrate <= sbitrate:
					hbitrate = bitrate
					playpath_url = video_index['src']	
			if playpath_url is None:
				playpath_url = lplaypath_url
			finalurl = playpath_url
		except:
			playpath_url = video_tree.video['src']
			if qbitrate is None:
				hbitrate = 1
				format = video_tree.find('param', attrs = {'name' : 'format' })['value']
				if 'SD' in format:
					bitrates = BITRATES[:5]
				else:
					bitrates = BITRATES
				for i, bitrate in enumerate(bitrates):
					if int(bitrate) < sbitrate:
						hbitrate = i + 1
			else:
				hbitrate = BITRATES.index(qbitrate) + 1
			finalurl = playpath_url.split('_')[0] + '_' + str(hbitrate) + '.mp4'
		try:
			closedcaption = video_tree.find('textstream', type = 'text/srt')['src']
		except:
			pass
		item = xbmcgui.ListItem(path = finalurl)
		try:
			item.setThumbnailImage(common.args.thumb)
		except:
			pass
		try:
			item.setInfo('Video', {	'title' : common.args.name,
									'season' : common.args.season_number,
									'episode' : common.args.episode_number})
		except:
			pass
		xbmcplugin.setResolvedUrl(pluginHandle, True, item)
		if (addon.getSetting('enablesubtitles') == 'true') and (closedcaption is not None):
			while not xbmc.Player().isPlaying():
				xbmc.sleep(100)
			xbmc.Player().setSubtitles(closedcaption)
	else:
		common.show_exception(video_tree.ref['title'], video_tree.ref['abstract'])
