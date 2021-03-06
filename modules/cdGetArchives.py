import re
import time
import urllib.request, urllib.error, urllib.parse
import os
import sys
import datetime
import calendar
import requests

from datetime import datetime
import logging

moduleTag="Archives"

headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}

def getMementos(uri):

    uri = uri.replace(' ', '')
    orginalExpression = re.compile( r"<http://[A-Za-z0-9.:=/%-_ ]*>; rel=\"original\"," )
    mementoExpression = re.compile( r"<http://[A-Za-z0-9.:=/&,%-_ \?]*>;rel=\"(memento|first memento|last memento|first memento last memento|first last memento)\";datetime=\"(Sat|Sun|Mon|Tue|Wed|Thu|Fri), \d{2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (19|20)\d\d \d\d:\d\d:\d\d GMT\"" )
    zeroMementoExpression = re.compile(r"Resource: http://[A-Za-z0-9.:=/&,%-_ ]*")

    #baseURI = 'http://timetravel.mementoweb.org/timemap/link/'
    #baseURI = 'http://mementoweb.org/timemap/link/'
    #OR
    baseURI = 'http://mementoproxy.cs.odu.edu/aggr/timemap/link/1/'
    memento_list = []

    try:
        search_results = urllib.request.urlopen(baseURI+uri)
        the_page = search_results.read().decode('ascii','ignore')

        timemapList = the_page.split('\n')
        mementoNames = []
        for line in timemapList:

            #reconsider this
            if(line.find("</memento")>0):
                line = line.replace("</memento", "<http://api.wayback.archive.org/memento")
    
            start = line.find('h')#find the start location of http or https
            loc = line.find('>;rel="')

            #tofind = ';datetime="'
            tofind = '; datetime="'

            loc2 = line.find(tofind)
            if(loc!=-1 and loc2!=-1):
                mementoURL = line[start:loc]
                timestamp = line[loc2+len(tofind):line.find('"',loc2+len(tofind)+3)]

                epoch = int(calendar.timegm(time.strptime(timestamp, '%a, %d %b %Y %H:%M:%S %Z')))
                day_string = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(epoch))


                memento = {}
                
                memento["time"] = day_string

                name = urllib.parse.urlparse(mementoURL.strip())

                memento["name"] = name.netloc
                memento["link"] = mementoURL

                #assumption that first memento is youngest - ON - start
                
                if( name.netloc not in mementoNames ):
                    memento_list.append(memento)
                    mementoNames.append(name.netloc)
                
                #assumption that first memento is youngest - ON - end

                #assumption that first memento is NOT youngest - ON - start
                #memento_list.append(memento)
                #assumption that first memento is NOT youngest - ON - end

    except urllib.error.URLError:
        pass


    return memento_list
  
def getRealDate(url, memDate):   
    response = requests.get(url,headers=headers)
    page = response.headers
    date = ""

    if "X-Archive-Orig-last-modified" in page:
        date=page["X-Archive-Orig-last-modified"]
    elif 'X-Archive-Orig-date' in page:
        date=page['X-Archive-Orig-date']

    if(date ==""):
        date = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(memDate))    
    else:
        epoch = int(calendar.timegm(time.strptime(date, '%a, %d %b %Y %H:%M:%S %Z')))
        date = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(epoch))
    
    return date  

def getArchives(url, outputArray, outputArrayIndex,verbose=False,**kwargs):
    
    try:
        mementos = getMementos(url)

        if(len(mementos) == 0):
            result = []
            result.append(("Earliest", ""))
            result.append(("By_Archive", dict([])))
            outputArray[outputArrayIndex] = result[0][1]
            logging.debug ("Done Archives 0")
            return dict(result)

        archives = {}

        for memento in mementos:
            epoch = int(calendar.timegm(time.strptime(memento["time"], '%Y-%m-%dT%H:%M:%S')))
            if(memento["name"] not in archives):
                archives[memento["name"]] = {"link":memento["link"], "time": epoch}
            else:
                if(epoch<archives[memento["name"]]["time"]):
                    archives[memento["name"]]["time"] = epoch
                    archives[memento["name"]]["link"] = memento["link"]



        lowest = 99999999999
        link = ""

        limitEpoch = int(calendar.timegm(time.strptime("1995-01-01T12:00:00", '%Y-%m-%dT%H:%M:%S')))


        for archive in archives:
            date = getRealDate(archives[archive]["link"],archives[archive]["time"])
            epoch = int(calendar.timegm(time.strptime(date, '%Y-%m-%dT%H:%M:%S')))
            
            if(epoch<limitEpoch):
                archives[archive]["time"] = ""
                continue

            archives[archive]["time"] = date
            if(epoch<lowest):
                lowest = epoch

        lowest = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(lowest))

        result = []
        result.append(("Earliest", lowest))

        result2 = []
        for archive in archives:
            if(archives[archive]["time"]==""):
                continue
            #result2.append((archive, str(archives[archive]["time"])))
            result2.append((archives[archive]["link"], str(archives[archive]["time"])))
        result.append(("By_Archive", dict(result2)))
        
        outputArray[outputArrayIndex] = result[0][1]
        kwargs['displayArray'][outputArrayIndex] = result
        logging.debug ("Done Archives 1")
        return dict(result)

    except:
        logging.exception (sys.exc_info())
        result = []
        result.append(("Earliest", ""))
        result.append(("By_Archive", dict([])))

        outputArray[outputArrayIndex] = result[0][1]
        kwargs['displayArray'][outputArrayIndex] = result
        logging.debug ("Done Archives 2")
        return dict(result)
