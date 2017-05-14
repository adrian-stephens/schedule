# utils.py
# Utility functions for "updateGoogleCalendar" project
# 2015-03-31 Adrian Stephens
from __builtin__ import True

def getWanted(settings,group,shortBreakout,breakout=''):
    wanted = False
    inIMAT = False
    
    if 'caucus' in shortBreakout.lower():
        return False, False

    if 'DNP' in shortBreakout:
        return False, False
    
    if group in settings.matchGroups['imat']:
        wanted = True
        inIMAT = True
    elif group in settings.matchGroups['calendar']:
        wanted = True
    
    if shortBreakout in settings.matchBreakouts['imat']:
        wanted = True
        inIMAT = True
    elif shortBreakout in settings.matchBreakouts['calendar']:
        wanted = True

    if breakout in settings.matchBreakouts['imat']:
        wanted = True
        inIMAT = True
    elif breakout in settings.matchBreakouts['calendar']:
        wanted = True
            
    # now look for breakouts with specific groups
    if shortBreakout in settings.matchBreakoutAndGroup['imat']:
        if group in settings.matchBreakoutAndGroup['imat'][shortBreakout]:
            wanted = True
            inIMAT = True
      
    elif shortBreakout in settings.matchBreakoutAndGroup['calendar']:
        if group in settings.matchBreakoutAndGroup['calendar'][shortBreakout]:
            wanted = True
                
    if shortBreakout in settings.doNotPost['calendar']:
        wanted = False
    elif shortBreakout in settings.doNotPost['imat']:
        inIMAT = False

    if breakout in settings.doNotPost['calendar']:
        wanted = False
    elif breakout in settings.doNotPost['imat']:
        inIMAT = False

    return wanted, inIMAT


from operator import attrgetter

def sortEvents(events):
    """
    Given a list of events,  sort them by date, time, breakout and location
    """
    sortedEvents = sorted(events, key=attrgetter('startDateTime','summary', 'location'))
    return sortedEvents

def f2fMergeRooms(events):
    """
    Given a list of Events,  merge rooms for duplicate events
    """
    filteredEvents = []
    for e in events:
        if e.deleted:
            continue
        
        for t in events:
            if e is t:
                continue
            
            if t.deleted:
                continue
            
            if  e == t:
                try:
                    e.location += ", %s" % (t.location,)
                except:
                    pass
                t.deleted = True

        filteredEvents.append(e)
            
            
    return filteredEvents

    
def getDate (d):
    """
    Given a date object,  return it as a dateTime object
    """
    import datetime
    return datetime.datetime(year=d.year, month=d.month, day=d.day)

def getDuration ( end, start):
    """
    Given two datetime.datetime objects representing the end and start of a period,  determine the duration of the period in minutes
    Prerequisite:  end > start
    Return:  Duration in minutes
    """
    import datetime
    if isinstance(end, datetime.datetime) and isinstance(start, datetime.datetime):   
        delta = end - start
        mins = delta.seconds/60
    elif isinstance(end, datetime.time) and isinstance(start, datetime.time):
        mins = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
    else:
        assert (False),"Bad time classes in getDuration"
    
    return mins

def addDuration ( t1, t2):
    """ 
    Given t1 is a datetime or datetime.time and t2 is an integer number of minutes
    Returns t1 + t2 as a datetime.time 
    """
    from datetime import time

    hours = t1.hour
    mins = t1.minute    
    add = t2
    
    while add >= 60:
        add = add - 60
        hours = hours + 1
    
    mins = mins + add
    if mins > 59:
        mins = mins - 60
        hours = hours + 1
        
    t3 = time(hours, mins)
    return t3

def subtractDuration ( t1, t2):
    """ 
    Given t1 is a datetime or datetime.time and t2 is an integer number of minutes
    Returns t1 - t2 as a datetime.time 
    """
    from datetime import time

    hours = t1.hour
    mins = t1.minute    
    sub = t2
    
    while sub >= 60:
        sub = sub - 60
        hours = hours - 1
    
    mins = mins - sub
    if mins < 0:
        mins = mins + 60
        hours = hours - 1
        
    t3 = time(hours, mins)
    return t3

def subtractTime (t1, t2):
    """
    Return number of minutes corresponding to t1-t2,  where t2 and t2 are datetimes or times
    """
    from datetime import datetime,timedelta
    # The date values below are spurious,  but need to be non-zero
    t = datetime(2000,1,1) + timedelta(hours=t1.hour, minutes=t1.minute) - timedelta(hours=t2.hour, minutes=t2.minute)
    minutes = t.hour * 60 + t.minute
    return minutes
    
    