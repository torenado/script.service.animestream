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
plugin_name = 'animestream'
dc=xbmcaddon.Addon(id='script.service.animestream')
addonPath=os.getcwd()
sys.path = [dc.getAddonInfo('path') + '/resources/lib'] + sys.path
sys.path = [dc.getAddonInfo('path') + '/resources/lib/streamSites'] + sys.path

from utils_run import *
import anidbQuick

base_txt = 'animestream_strm: '
# Library Location
path_anime = dc.getSetting('path_anime')
path_cartoon = dc.getSetting('path_cartoon')


if __name__ == '__main__':
	monitor = xbmc.Monitor()
	end_time = datetime.now()
	dc.setSetting('updateStreams','true')
	
	
	
	while True:
	
		if monitor.abortRequested():
			# Abort was requested while waiting. We should exit
			raise IOError('exit Kodi')
			
		updateNow = dc.getSetting('updateStreams')
		time_now = datetime.now()
		lapse_time = time_now - end_time
		
		if(lapse_time.seconds > (60*60*24) or updateNow=='true'): #runs every 24 hours
			# Initialize SQL Tables
			initializeTables()
			
			# update streaming list from websites every day
			streamSiteSeriesList_aniUrl()
			list_watchlisttotal()
			cache.cacheFunction(get_ani_aid_list)
			cache.cacheFunction(allAnimeList)
			print base_txt + 'Number of seconds since last completed streaming site run: ' + str(lapse_time.seconds)
			end_time = datetime.now()
			dc.setSetting('updateStreams','false')
	
	while False:
		# Sleep/wait for abort for 10 seconds
		if monitor.waitForAbort(5):
			# Abort was requested while waiting. We should exit
			print base_txt + 'Kodi is shutting down....'
			break			
		
		
		print base_txt + 'service is looping'
		
		if(lapse_time.seconds > 60*60*24 or updateNow=='true'): #runs every 24 hours
			#grab list of series urls			
			print base_txt + 'Grab list of series URLs from streaming sites'
			streamSeriesList = streamSiteSeriesList()
			streamSeriesList.sort(key=lambda name: name[1], reverse=True) 
				
			#get wishlist and mylist from anidb and cache for 1 day
			watchWishlist = list_wishlist()[0:2]
			print watchWishlist
			for aidDB, name, url in watchWishlist:
				
				if monitor.abortRequested():
					# Abort was requested while waiting. We should exit
					raise IOError('exit Kodi')		
				
				#get thetvdb id from andb id
				tvdbid = get_tvdb_id(aidDB)[0]
				
				#get all names associated with thetvdb id
				aidGroup = get_anidb_id(tvdbid)
				# if len(aidGroup)<1:
					# aidGroup.append([aidDB, name, '0', '1'])
				# print aidGroup
				
				#match the dirName + alternate names
				seriesURL = []
				aidGroup.sort(key=lambda name: name[1], reverse=True) 
				for aid, name, tvdbid, season in aidGroup:
					seriesName = getAltNames(name)
					
					for item in list(streamSeriesList):
						streamName = cleanSearchText(item[1])
						if streamName in seriesName:
							streamLink = item[0]
							seriesURL.append([aid, name, tvdbid, season, streamName, streamLink])
							streamSeriesList.remove(item)
				
				seriesURL.sort(key=lambda a:(a[0],a[1],a[2])) 
				seriesURL = f2(seriesURL)
				# print seriesURL
				
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
				
				dirLength = len(seriesURLConsolidated)
				print base_txt + '# of series: ' + str(dirLength)
				print seriesURLConsolidated
				
				#grab episode list from urls 
				seriesEpisodeList = []
				for aid, seriesName, tvdbid, season, streamLinkGroup in seriesURLConsolidated:
					if monitor.abortRequested():
						# Abort was requested while waiting. We should exit
						raise IOError('exit Kodi')	
					seriesEpisodeList = seriesEpisodeList + getSeriesEpisodeList(streamLinkGroup, aid, tvdbid, seriesName)
				
				seriesEpisodeList.sort(key=lambda a:(a[7],a[6],a[0])) 
				seriesEpisodeList = f2(seriesEpisodeList)
				dirLength = len(seriesEpisodeList)
				print base_txt + '# of episodes: ' + str(dirLength)
				# print seriesEpisodeList
				
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
					if aidTest == aid and epNumTest == epNum and epSeasonTest == epSeason:
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
				dirLength = len(seriesEpisodeListConsolidated)
				print base_txt + '# of unique episodes: ' + str(dirLength)	
				# print seriesEpisodeListConsolidated
				
				#grab media url from episode pages
				seriesEpisodeMediaList = []
				for episodeLinkInfo in seriesEpisodeListConsolidated:
					if monitor.abortRequested():
						# Abort was requested while waiting. We should exit
						raise IOError('exit Kodi')	
					seriesEpisodeMediaList = seriesEpisodeMediaList + getEpisodeMediaURL(episodeLinkInfo)
				
				seriesEpisodeMediaList = f2(seriesEpisodeMediaList)
				dirLength = len(seriesEpisodeMediaList)
				print base_txt + '# of episode mediaURLs: ' + str(dirLength)	
				# print seriesEpisodeMediaList		
				
				#resolve media url into direct link to video
				resolveMediaList = []
				ii = 0
				for mediaInfo in seriesEpisodeMediaList:
					ii += 1
					# print base_txt + 'episode mediaURLs: ' + str(ii) + ' of ' + str(dirLength)
					if monitor.abortRequested():
						# Abort was requested while waiting. We should exit
						raise IOError('exit Kodi')
					temp1 = resolveMediaURL(mediaInfo)
					if len(temp1)>0:
						resolveMediaList.append(temp1)
					
				# print len(resolveMediaList[20])
				print resolveMediaList
				resolveMediaList.sort(key=lambda a:(a[12],a[14],a[11],a[0],a[2],a[5],a[4])) 
				resolveMediaList = f2(resolveMediaList)
				dirLength = len(resolveMediaList)
				print base_txt + '# of valid mediaURLs: ' + str(dirLength)
				
				#populate directory with STRM files of episodes using urlresolver (skip if episode file already exists)
				ii = 0
				for aid, tvdbid, seriesName, episodePageName, epNum, epSeason, siteNname, url, mirror, part, totParts, subdub, hostName, media_url, mediaOrder in resolveMediaList:
					ii += 1
					print base_txt + 'valid mediaURLs: ' + str(ii) + ' of ' + str(dirLength)
					if monitor.abortRequested():
						# Abort was requested while waiting. We should exit
						raise IOError('exit Kodi')	
					
					#create directory names based on wishlist (skip directories if already exist based on thetvdb)
					dirName = cleanSearchText(seriesName)
					path_lib = path_anime + dirName
					# if not os.path.exists(path_lib):
						# os.makedirs(path_lib)
						
					filename = "%s - S%02dE%03d" % (seriesName, epSeason, epNum)
					fullpath = path_lib + '/' + filename
					print base_txt + fullpath + ': ' + media_url
					# with open(fullpath, 'a') as myfile:
						# myfile.write(media_url)
				
					
				end_time = datetime.now()
				dc.setSetting('updateStreams','false')