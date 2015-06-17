# getf2f.py
# 2015-04-02 Adrian Stephens
#
# Get the events for the date specified in settings into a list


from utils import f2fMergeRooms
from events import Event

import requests
import lxml.html



def parseHTTP(settings, http):
    """ Parse the specified HTTP string in a format unique to F2F into a list of Event objects """
    from datetime import timedelta, datetime
    
    dayToOffset = dict(sunday=0, monday=1, tuesday=2, wednesday=3, thursday=4, friday=5, saturday=6)

    f2fTree = lxml.html.fromstring(http).getroottree()
    schedule = f2fTree.findall('//div[@id="schedule"]')
       
    assert (schedule),"Cannot find id schedule in F2F html"

    days = schedule[0].findall('div')
    
    events = []
    
    for dayElement in days:
        dayName = dayElement.get('id')
        dayNumber = dayToOffset[dayName]
        rows = dayElement.findall('table/tr')
        for row in rows:
            trackID = row.get('class')
            if trackID.find('tr-track-') >= 0:
                track = trackID[9:]
            else:
                track = None
                
            if (track in settings.matchGroups):
                cols=[]
                colElements = row.findall('td')
                for colElement in colElements:
                    for t in colElement.itertext():
                        cols.append(t)
    
                    
        
                slotTime = cols[0]
                times = slotTime.split("-")
                startTime = datetime.strptime(times[0], "%H:%M").time()
                endTime = datetime.strptime(times[1], "%H:%M").time()  

                # These dateTimes are in the meeting timezone                           
                startDateTime = settings.sessionDateTimes[dayNumber] + \
                    timedelta(hours=startTime.hour, minutes=startTime.minute)
                    
                endDateTime = settings.sessionDateTimes[dayNumber] + \
                    timedelta(hours=endTime.hour, minutes=endTime.minute)
                
                
                breakout = cols[1]
                shortBreakout = settings.getShortBreakout(breakout)
                
                # Apply optional mapping to f2f description
                if shortBreakout in settings.f2fToBreakout:
                    shortBreakout = settings.f2fToBreakout[shortBreakout]
                
                if shortBreakout in settings.doNotPost:
                    continue
                
                room = cols[2]
                
                event = Event(settings,startDateTime,endDateTime,shortBreakout,room)
                events.append(event)

    return events

def getf2fhttpEvents(settings):
    """
    Return a list of f2f events from the current f2f attendee page
    """
    if 'proxyIP' in settings.__dict__:
        proxies = {'http':'http://{0}:{1}'.format(settings.proxyIP, str(settings.proxyPort)), 'https':'http://{0}:{1}'.format(settings.proxyIP, str(settings.proxyPort))}
    else:
        proxies = None

    # Get f2f schedule
    r = requests.get(settings.f2fScheduleURL, proxies=proxies)
    assert (r.status_code == 200),"Cannot read f2f page: {0}".format(settings.scheduleURL)
    scheduleHTTP = r.text
        
    
    # parse the http into f2f events
    f2fEvents = parseHTTP(settings, scheduleHTTP)

    return f2fMergeRooms(f2fEvents)