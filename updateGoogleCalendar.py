# Schedule.py
# Adrian Stephens 20150318
# This file maintains synchronicity between the F2F meeting calendar and a Google calendar derived from it.
# The entries in the Google Calendar are marked with "autoGen",  which appears as a "category" when viewed by
# thunderbird/sunbird. Other entries in the calendar not so marked are ignored.
#
# Dependencies:
# 1. run: "pip install --upgrade google-api-python-client"
# 2. A writable google calender,  identified by the Google calender ID.


from datetime import datetime, timedelta
from events import Event, compareEventLists
 


def insertCalEvent (settings, service, event):
    """
    Insert the specified event from the F2F file into the Google calendar
    """
    e = {'start': {'dateTime': datetime.strftime(event.startDateTimeUTC(),"%Y-%m-%dT%H:%M:00Z")}, 
         'end': {'dateTime': datetime.strftime(event.endDateTimeUTC(),"%Y-%m-%dT%H:%M:00Z")},
         'summary': event.summary, 
         'location': event.location,
         'extendedProperties': 	
            {'shared': 
                {'X-MOZ-CATEGORIES': 'autoGen'}}}
    
       
    service.events().insert(calendarId=settings.calendarID, body=e).execute()
    
    
    
def deleteCalEvent (settings, service, calEvent):
    """
    Delete the specified calendar event from the calendar
    """
    service.events().delete(calendarId=settings.calendarID, eventId=calEvent.id).execute()
    
    
    
    


def parseTime (dt, timeString ):
    """
    Input: a datetime representing a date and string of the form 20:00:00[Z|+|-][04:00] into a time in hh:mm based on UTC 
    Output: a datetime representing the date and time 
    """
  
    t1 = datetime.strptime(timeString[0:5], "%H:%M")
    adjust = timeString[8]
    
    td1 = timedelta(hours=t1.hour, minutes=t1.minute)

    if adjust == 'Z':
        return dt + td1
    else:
        dt2 = datetime.strptime(timeString[9:15], "%H:%M")
        td2 = timedelta(hours=dt2.hour, minutes=dt2.minute)
        if adjust == '-':       # Timezone is behind UTC, therefore UTC should be increased
            return dt + td1 + td2
        else:
            return dt + td1 - td2


def parseDateTime( dateTime ):
    """ Parse Strings of the forms: 
            2015-05-05T20:00:00-04:00
            and
            2015-05-05
            into a datetime.datetime object
            applying any UTC correction in the datetime
    
        Returns datetime,  utc based
    """
    if len(dateTime) < 10:
        # Too short
        return None
    
    d = datetime.strptime(dateTime[0:10], "%Y-%m-%d")
    
    if len(dateTime) > 10:
        # Includes a time
        p = dateTime.split('T')  
        return parseTime(d, p[1])
    else:
        return d

def getCalEvents(settings, service):
    """ Get list of events for our calendar.
    
    The Events are structured into a dict containing the following keys:
        date:  Date in yyyy-mm-dd format
        start: Start time in hh:mm format - adjusted to UTC
        dur: Duration in hh:mm (optional)
        summary
        description (optional)
        location
    
    """
    
    events = []
    pageToken = None
    while True: # for each page
        e = service.events().list(calendarId=settings.calendarID, pageToken=pageToken).execute()
            
        for event in e['items']: # for all events this page
            # Unpack the event
            
            if ('extendedProperties' in event) and \
                ('shared' in event['extendedProperties'] ) and \
                ('X-MOZ-CATEGORIES' in event['extendedProperties']['shared']) and \
                (event['extendedProperties']['shared']['X-MOZ-CATEGORIES'] == 'autoGen'):
            
                # Only pay attention to events that we automatically generated.  These are
                # flagged with "autoGen" as shown above.
            
                s = event['start']
                if 'date' in s:
                    start = parseDateTime(s['date'])                
                else:
                    start = parseDateTime(s['dateTime'])
                    
                # Adjust to meeting timezone
                start += timedelta(hours=settings.timeZoneOffset)
    
                s = event['end']
                if 'date' in s:
                    end = None
                else:
                    end = parseDateTime(s['dateTime'])
    
                # Adjust to meeting timezone
                end += timedelta(hours=settings.timeZoneOffset)
    
                    
                if 'summary' in event:
                    summary = event['summary']
                else:
                    summary = ''
    
                if 'location' in event:
                    location = event['location']
                else:
                    location = ''
                    
                    
                calEvent = Event(settings, start, end, summary, location)
                calEvent.id = event['id']
                events.append(calEvent)

        pageToken = e.get('nextPageToken')
        if not pageToken:
            break

    return events


def getService(settings):
    """
    Get Google service.  This code is largely copied from the Google API examples,  modified to support Proxy
    """    
    import httplib2
    import argparse
    
    from apiclient.discovery import build
    from oauth2client.file import Storage
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client import tools
    from oauth2client.tools import run_flow
    
    FLOW = OAuth2WebServerFlow(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        scope=settings.scope,
        user_agent=settings.user_agent)
    
    
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    flags = parser.parse_args()  #['--noauth_local_webserver']
    
    
    # If the Credentials don't exist or are invalid, run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.

    # Create an httplib2.Http object to handle our HTTP requests
    if 'proxyIP' in settings.__dict__:    
        proxyInfo = httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, settings.proxyIP, settings.proxyPort) 
        http = httplib2.Http(proxy_info=proxyInfo)
    else:
        http = httplib2.Http()
        
    storage = Storage('calendar.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
        credentials = run_flow(FLOW, storage, flags, http=http)
    
        


    http = credentials.authorize(http)
    
    # Build a service object for interacting with the API. 
    service = build(serviceName='calendar', version='v3', http=http, developerKey=settings.developerKey)
    
    return service

   
def updateGoogleCalendar(settings, agendaEvents):


    retries = 0
    from oauth2client.client import AccessTokenRefreshError
    
    while True:
        try:
            service = getService(settings)
        
            # Read the Calendar
            calEvents = getCalEvents(settings, service)
            
        except AccessTokenRefreshError:
            retries += 1
            if retries < 4:
                continue    # retry service login
            else:
                raise
 
        except:
            raise
        
        break
    
   
    
    onlyInAgenda, changed, onlyInCalendar, info = compareEventLists(agendaEvents,"Agenda",calEvents,"Calendar")
    
    if settings.update:
        
        # Add events only in the agenda
        for e in onlyInAgenda:
            insertCalEvent(settings, service, e)
            
        # Delete events only in the calendar
        for e in onlyInCalendar:
            deleteCalEvent(settings, service, e)
            
        # Replace events that are changed    
        for agendaEvent, calEvent in changed:
            deleteCalEvent(settings, service, calEvent)
            insertCalEvent(settings, service, agendaEvent)            
    
            
    return info
