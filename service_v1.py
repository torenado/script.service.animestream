import urllib,urllib2,re,sys,httplib
import gzip, io, time
import xbmc,xbmcplugin,xbmcgui,xbmcaddon,urlresolver
import cookielib,os,string,cookielib,StringIO
import os,time,base64,logging
from datetime import datetime
from datetime import timedelta
try:
	import json
except ImportError:
	import simplejson as json
import sqlite3 as sqlite

base_txt = 'animestream: '
plugin_name = "animestream"
dc=xbmcaddon.Addon(id='plugin.video.animestream')
addonPath=os.getcwd()
sys.path = [dc.getAddonInfo('path') + "/resources/lib"] + sys.path
sys.path = [dc.getAddonInfo('path') + "/resources/lib/streamSites"] + sys.path

from utils import *
import anidbQuick

streamSiteList_general = ['anilinkz',
				'anime44',
				'animecrazy',
				'animeflavor',
				'animefreak',
				'animefushigi',
				'animereboot',
				'animesubbed',
				'animetip',
				'lovemyanime',
				'myanimelinks',
				'tubeplus']
streamSiteList_adult = ['hentaiseries',
				'hentaistream']
streamSiteList = streamSiteList_general + streamSiteList_adult

for module in streamSiteList:
	vars()[module]=__import__(module)

# try:
	# import StorageServer
# except:
	# import storageserverdummy as StorageServer
	
# cache = StorageServer.StorageServer(plugin_name, 24) # (Your plugin name, Cache time in hours)
# cache7 = StorageServer.StorageServer(plugin_name, 24*7) # (Your plugin name, Cache time in hours)
	
#animestream
# modded from --> <addon id="plugin.video.animecrazy" name="Anime Crazy" version="1.0.9" provider-name="AJ">

#SQLite querey to refresh data

#sql = 'delete from %s where data like "%mylist%";' % plugin_name
#sql = 'delete from %s where data like "%<anime-list>%";' % plugin_name
#sql = 'delete from %s where data like "%<error>%";' % plugin_name
#sql = 'delete from %s where name not like "%grab%";' % plugin_name


mozilla_user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
base_txt = 'animestream: '

plug_path = xbmc.translatePath(dc.getAddonInfo("profile")).decode("utf-8")
user_path = os.path.join(plug_path, plugin_name+'.db')
# cache_path= os.path.join(plug_path, '../script.common.plugin.cache/commoncache.db')
cache_path= os.path.join(plug_path, '../../../temp/commoncache.db')
con_us = sqlite.connect(user_path)
con_cache = sqlite.connect(cache_path)

# aniDB Login
uname = dc.getSetting('username')
passwd = dc.getSetting('pass')

# aniDB Public Wishlist
unid = dc.getSetting('uid')
pubpass = dc.getSetting('pubpass')

# Library Location
path_anime = dc.getSetting('path_anime')
path_cartoon = dc.getSetting('path_cartoon')

#aniDB Access
aniDB_access = dc.getSetting('aniDB_access')

# Cartoon List URLs
cartoonUrls = ['http://www.animeflavor.com/index.php?q=cartoons',
				'http://anilinkz.com/cartoons-list']
				

if __name__ == '__main__':
	monitor = xbmc.Monitor()
	end_time = datetime.now()
	dc.setSetting('updateStreams','true')
	
	while True:
		# Sleep/wait for abort for 10 seconds
		if monitor.waitForAbort(10):
			# Abort was requested while waiting. We should exit
			break
		
		updateNow = dc.getSetting('updateStreams')
		time_now = datetime.now()
		lapse_time = time_now - end_time
		
		if(lapse_time.seconds > 60*60*24 or updateNow=='true'): #runs every 24 hours
			#get wishlist and mylist from anidb and cache for 1 day
			watchWishlist = list_wishlist()[10:15]
			
			for aidDB, name, url in watchWishlist:			
				#get thetvdb id from andb id
				tvdbid = get_tvdb_id(aidDB)
				
				#get all names associated with thetvdb id
				aidGroup = get_anidb_id(tvdbid)
							
				#grab list of series urls that match the dirName + alternate names
				streamSeriesList = streamSiteSeriesList()
				seriesURL = []
				aidGroup.sort(key=lambda name: name[1], reverse=True) 
				streamSeriesList.sort(key=lambda name: name[1], reverse=True) 
				for aid, name, tvdbid, season in aidGroup:
					seriesName = getAltNames(name)
					
					for item in list(streamSeriesList):
						streamName = cleanSearchText(item[1])
						if streamName in seriesName:
							streamLink = cleanSearchText(item[0])
							seriesURL.append([aid, name, tvdbid, season, streamName, streamLink])
							streamSeriesList.remove(item)
				
				seriesURL.sort(key=lambda a:(a[0],a[1],a[2])) 
				seriesURL = f2(seriesURL)
				print seriesURL
				
				#concatenate the series urls into a single string with ' <--> ' as the delimiter per aid
				seriesURL.sort(key=lambda name: name[0])
				seriesURLConsolidated = []
				aidTest=seriesURL[0][0]
				nameTest=seriesURL[0][1]
				tvdbidTest=seriesURL[0][2]
				seasonTest=seriesURL[0][3]
				streamLinkGroup = ''
				for aid, name, tvdbid, season, streamName, streamLink in seriesURL:
					if aidTest == aid:
						streamLinkGroup = streamLink + ' <--> ' + streamLinkGroup
					else:
						seriesURLConsolidated.append([aidTest, nameTest, tvdbidTest, seasonTest, streamLinkGroup])
						aidTest = aid
						nameTest=name
						tvdbidTest=tvdbid
						seasonTest=season
				
				seriesURLConsolidated.append([aidTest, nameTest, tvdbidTest, seasonTest, streamLinkGroup])	
				seriesURLConsolidated = f2(seriesURLConsolidated)	
				print seriesURLConsolidated
				
				#grab episode list from urls 
				seriesEpisodeList = []
				for aid, seriesName, tvdbid, season, streamLinkGroup in seriesURLConsolidated:
					seriesEpisodeList = seriesEpisodeList + getSeriesEpisodeList(streamLinkGroup, aid, tvdbid, seriesName)
				
				seriesEpisodeList.sort(key=lambda a:(a[7],a[6],a[0])) 
				seriesEpisodeList = f2(seriesEpisodeList)
				print seriesEpisodeList
				
				#concatenate the episode urls into a single string with ' <--> ' as the delimiter per aid
				seriesEpisodeListConsolidated = []
				aidTest=seriesEpisodeList[0][0]
				tvdbidTest=seriesEpisodeList[0][1]
				seriesNameTest=seriesEpisodeList[0][2]
				episodePageNameTest=seriesEpisodeList[0][4]
				epNumTest=seriesEpisodeList[0][6]
				epSeasonTest=seriesEpisodeList[0][7]
				episodePageLinkGroup = ''
				for aid, tvdbid, seriesName, episodePageLink, episodePageName, garbage1, epNum, epSeason in seriesEpisodeList:
					if aidTest == aid and epNumTest == epNum and epSeasonTest == epSeason
						episodePageLinkGroup = episodePageLink + ' <--> ' + episodePageLinkGroup
					else:
						seriesEpisodeListConsolidated.append([aidTest, tvdbidTest, seriesNameTest, episodePageNameTest, epNumTest, epSeasonTest, episodePageLinkGroup])
						aidTest = aid
						tvdbidTest = tvdbid
						seriesNameTest = seriesName
						episodePageNameTest = episodePageName
						epNumTest = epNum
						epSeasonTest = epSeason
				
				seriesEpisodeListConsolidated.append([aidTest, tvdbidTest, seriesNameTest, episodePageNameTest, epNumTest, epSeasonTest, episodePageLinkGroup])	
				seriesEpisodeListConsolidated = f2(seriesEpisodeListConsolidated)	
				print seriesEpisodeListConsolidated
				
				#grab media url from episode pages
				seriesEpisodeMediaList = []
				for episodeLinkInfo in seriesEpisodeListConsolidated:
					seriesEpisodeMediaList = seriesEpisodeMediaList + getEpisodeMediaURL(episodeLinkInfo)
				
				seriesEpisodeMediaList = f2(seriesEpisodeMediaList)
				print seriesEpisodeMediaList		
				
				#resolve media url into direct link to video
				resolveMediaList = []
				for mediaInfo in seriesEpisodeMediaList:
					resolveMediaList = resolveMediaList + resolveMediaURL(mediaInfo)
				
				resolveMediaList.sort(key=lambda a:(a[12],a[14],a[11],a[0],a[2],a[5],a[4])) 
				resolveMediaList = f2(resolveMediaList)
				print resolveMediaList
				
				#populate directory with STRM files of episodes using urlresolver (skip if episode file already exists)
				for aid, tvdbid, seriesName, episodePageName, epNum, epSeason, siteNname, url, mirror, part, totParts, subdub, hostName, media_url, mediaOrder in resolveMediaList:
					
					#create directory names based on wishlist (skip directories if already exist based on thetvdb)
					dirName = cleanSearchText(seriesName)
					path_lib = path_anime + dirName
					if not os.path.exists(path_lib):
						os.makedirs(path_lib)
						
					filename = "%s - S%02dE%03d" % (seriesName, epSeason, epNum)
					fullpath = path_lib + '/' + filename
					with open(fullpath, 'a') as myfile:
						myfile.write(media_url)
				
				end_time = datetime.now()
				dc.setSetting('updateStreams','false')