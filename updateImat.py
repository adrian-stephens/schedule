# imat.py
# 2015-03-31 Adrian Stephens
# Functions to get an imat session data

from datetime import datetime, timedelta
from lxml import html, etree
import keyring
from events import ImatEvent, SlottedEvent, compareEventLists


# Mapping tables from human readable field name to the names used for input tags
editMeetingMapping = {
               'Meeting Name': 'f4',
               'Group ID': 'f3',
               'Session Day': 'f8',
               'Timeslot Start': 'f16',
               'Override Start Time': 'f14',
               'Timeslot End': 'f15',  
               'Override End Time': 'f9', 
               'Location/Room': 'f2',
               'Credit': ['f6', {'Normal': 1, 'Extra': 2, 'Zero': 3, 'Other': 4}],
               'Override Credit Numerator': 'f1',
               'Override Credit Denominator': 'f0',
               'Facilitator Username or Email': 'f10',
               'Submit': ['f12','OK/Done']                          
               }

addNewMeetingMapping = {
               'Meeting Name': 'f2',
               'Group ID': 'f1',
               'Session Day': 'f6',
               'Timeslot Start': 'f12',
               'Override Start Time': 'f10',
               'Timeslot End': 'f11',  
               'Override End Time': 'f7', 
               'Location/Room': 'f0',
               'Credit': ['f4', {'Normal': 1, 'Extra': 2, 'Zero': 3, 'Other': 4}],
               'Facilitator Username or Email': 'f8',
               'Submit': ['f9','OK/Done']                          
               }

meetingDetailMapping = {'Delete': ['f2', 'Delete']}


def getSessionURL(settings, meetings, sessionDateTime):
    """
    Search a list of meetings and return an URL to the session page
    """
    for m in meetings:
        if m['start'] == sessionDateTime:
            return settings.imatBaseURL + m['view']
    return None    

def imatLogin(settings):
    """
    Log in to IMAT
    Returns a session object
    """
    inputs = {}
    if 'proxyIP' in settings.__dict__:
        proxies = {'http':'http://{0}:{1}'.format(settings.proxyIP, str(settings.proxyPort)), 'https':'http://{0}:{1}'.format(settings.proxyIP, str(settings.proxyPort))}
    else:
        proxies = {}
    
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
    
    s=requests.Session()
    s.proxies = proxies
    s.verify = False        # Don't verify SSL certificates,  as imat uses a self-signed cert.
    
    r = s.get(settings.loginURL)

    loginTree = html.fromstring(r.text)
    form = loginTree.forms[0]
    for element in form.inputs:
        inputs[element.get('name')] = element.get('value')
            
    
    imatPassword = keyring.get_password("imat", settings.imatUser)
    assert (imatPassword),"Cannot retrieve IMAT password"

    
    data = {'v': inputs['v'], 'c': inputs['c'], 'x1': settings.imatUser, 'x2': imatPassword, 'f0': '1', 'ok_button': 'Sign+In'}

    r = s.post(settings.loginURL, data=data, allow_redirects=False)
    assert (r.status_code==302), "Cannot Log in"
    return s

def getSessions(settings, s, imatSessionsURL):
    """
    Return the list of sessions known to imat
    The parameter is the requests session
    """
    
    r = s.get(imatSessionsURL)
    assert (r.status_code==200), "Cannot read sessions page"
    
    sessionsTree = html.fromstring(r.text)
 
    rows = sessionsTree.xpath('//tr')
    
    sessions = []
    for row in rows:
        c = row.get('class')
        if (c != None) and (c.startswith('b_data_row')) == True:

            cols = []
            for col in row.xpath('td'):
                cols.append(col.text)
        
            links = []
            for link in row.xpath('td/a'):
                links.append(link.get('href'))
            
            startDate = datetime.strptime(cols[0],"%d-%b-%Y")
            endDate = datetime.strptime(cols[1],"%d-%b-%Y")
            sessions.append({'start': startDate, 'end': endDate, 'sponsor': cols[2], 'type': cols[3], 'name': cols[4], 'timezone': cols[5], 'view': links[0]})

    return sessions


def parseTimePeriod(tp):
    """
    Parse a time period specification from the meeting detail page
    Input is a unicode string such as: PM2\xa0Thu, 12-Mar-201515:50\xa0-\xa018:10\n
    outputs:
        A datetime representing the start date and time in the meeting timezone
        A string representing the start slot name
        A datetime representing the end date and time
        A string representing the end slot name
        
    """
    a = tp.encode('ascii','replace')
    p1 = a.split(',')
    p2 = p1[0].split('?')
    
    startSlot = p2[0]
    if (len(p2) > 2) and (p2[1]=='-'):
        endSlot = p2[2]
    else:
        endSlot = startSlot

    p3 = p1[1].split('?')

    d = p3[0]
    e = p3[2]
    
    startDateTime = datetime.strptime(d.strip(),"%d-%b-%Y%H:%M")  
    endTime = datetime.strptime(e.strip(),"%H:%M")
    endDateTime = datetime(startDateTime.year, startDateTime.month, startDateTime.day, endTime.hour, endTime.minute)

    return startDateTime, startSlot, endDateTime, endSlot

def getSessionEvents(settings, s, sessionURL):
    """
    Return a list of dicts representing the breakouts or events from the specified session page
    """
    events = []

    
    r = s.get(sessionURL)
    assert (r.status_code==200), "Cannot read session page"
    
    sessionTree = html.fromstring(r.text)
 
    rows = sessionTree.xpath('//tr')
    
    for row in rows:
        c = row.get('class')
        if (c != None) and c.startswith('b_data_row'):

            cols = []
            for col in row.xpath('td'):
                cols.append(etree.tostring(col, encoding="unicode", method="text").rstrip('\n'))
        
            links = {}
            for link in row.xpath('td/a'):
                links[link.text] = link.get('href')               
 
            if (len(cols) > 8) and (len(links) > 0):  # In the main table,  not the table of timeslots
                startDateTime, startSlot, endDateTime, endSlot = parseTimePeriod(cols[0])
                credit = cols[5]
                p1 = credit.split(' ')
                
                p2 = cols[4].split('---')
                summary = p2[0].strip()
                
                # Ignore events starting with *,  they are manually entered
                if summary[0] != "*":
                                   
                    location = ''
                    if  cols[1] != None:
                        location = cols[1]  
    
                    edit = ''
                    if 'edit' in links:
                        edit = settings.imatBaseURL + links['edit']
    
                    event = ImatEvent(settings, startDateTime, endDateTime, summary, location, startSlot, endSlot,'', p1[0], edit)
                        
                    if len(p1) > 1:
                        p3 = p1[1].split(u'\xa0')
                        event.numerator = p3[0]
                        event.denominator = p3[2]
    
                    if len(p2) > 1:
                        if p2[1].strip() == 'cancelled':
                            event.deleted = True
    
    
    
                    events.append(event)
                    
    taskMenu = sessionTree.xpath('//div[@class="task_menu"]//a')
    
    addMeetingURL = None
    for task in taskMenu:
        if task.text == 'Add a new Meeting':
            addMeetingURL = task.get('href')
       
    assert (addMeetingURL),"Cannot find 'Add a new Meeting' URL"
    
    return events, settings.imatBaseURL + addMeetingURL

def getSessionSlots(s, addMeetingURL):
    """
    Given the URL to create a new meeting,  scrape the encoding of slots to slot times.
    """
    startSlots = {}
    endSlots = {}
    projectIDs = {}
    r = s.get(addMeetingURL)
    assert (r.status_code==200), "Cannot read session page"
    
    addMeetingTree = html.fromstring(r.text)
 
    cols = addMeetingTree.xpath('//td')
    for col in cols:
        if col.text == 'Timeslot Start:':
            options = col.xpath('following-sibling::td/select/option')
            for option in options:
                p=option.text.split(u'\xa0')
                startSlots[p[0]] = [option.get('value'), p[1]]

        if col.text == 'Timeslot End:':
            options = col.xpath('following-sibling::td/select/option')
            for option in options:
                p=option.text.split(u'\xa0')
                endSlots[p[0]] = [option.get('value'), p[1]]

        if col.text == 'Group ID:':
            options = col.xpath('following-sibling::td/select/option')
            for option in options:
                p=option.text.split(' ')
                projectIDs[p[0]] = option.get('value')

    return startSlots, endSlots, projectIDs


def adjustEdge(tu, isStart):
    """
    Adjust tu time based on slot edge type
    """
    # Adjust start and end so they don't pick the wrong slot when the end of one slot overlaps
    # by one minute the start of the next
    if isStart:
        t = (tu + timedelta(minutes=1)).time()
    else:
        t = (tu - timedelta(minutes=1)).time()
    return t

def inSlot(settings, tu, isStart):
    t = adjustEdge(tu, isStart)
    
    for slot in settings.slots:
        if (t >= slot.start) and (t <= slot.end):
            return True
        
    return False

def getSlot(settings, tu, isStart):
    """
    Give a datetime object,  return the slot name and index containing the time
    """
    t = adjustEdge(tu, isStart)
    
    # Algorithm 1 - find time in (extended) slot hours
    for slot in settings.slots:
        if (t >= slot.extendedStart) and (t <= slot.extendedEnd):
            return slot
    
    assert (False),"Slot table extended start and end do not fully cover the 24 hour period"

def slottifyEvents(settings, events):
    """
    Slottify Events - take a list of Events from the f2f meeting calendar and split if necessary to IMAT slots
    """

    newEvents = []
    for e in events:
        
        startDateTime = e.startDateTime
        startSlot = getSlot(settings, startDateTime,True)
      
        endDateTime = e.endDateTime
        endSlot = getSlot(settings, endDateTime,False)

           
    
        slotDelta = endSlot.index - startSlot.index
        
        if not e.inIMAT:
            continue       
       
        # Determine whether the meeting should be split into slots
        # Don't split meetings on friday,  otherwise split all meetings into slots
        if (slotDelta > 0) and not(e.summary in settings.overrideCredit):
            slotIndex = startSlot.index
            while slotIndex <= endSlot.index:

                # Adjust start and end times to match slot
                slotName = settings.slots[slotIndex].name
                if slotIndex != startSlot.index: # For initial slot, take timing from f2f
                    slotStartTime = settings.slots[slotIndex].start
                    startDateTime = e.sessionDateTime + timedelta(hours=slotStartTime.hour, minutes=slotStartTime.minute)
                
                if slotIndex == endSlot.index: # For the last slot, take timing from the Event
                    endDateTime = e.endDateTime
                else:
                    slotEndTime = settings.slots[slotIndex].end
                    endDateTime = e.sessionDateTime + timedelta(hours=slotEndTime.hour, minutes=slotEndTime.minute) # for non-final slots, take end timing from slot
                
                newEvent = SlottedEvent(settings, startDateTime,endDateTime,e.summary,e.location,slotName,slotName)
                newEvents.append(newEvent)
                slotIndex += 1              
                
        else:
            newEvent = SlottedEvent(settings, startDateTime,endDateTime,e.summary,e.location,startSlot.name,endSlot.name,True,'')
            newEvents.append(newEvent)
        
    return newEvents

def adjustForGrace(settings, events):
    """
    Adjust list of SlottedEvents start and end times to allow grace period for logging-in.
    Firstly build a table of used slots.  Then add grace to slot boundaries that do
    not abut an occupied slot.
    """
    # Mark used slot identified by dayIndex and start slot name
    used = {}
        
    for e in events:
        dayIndex = e.dayIndex()
        startSlotIndex = settings.slotNameToIndex[e.startSlot]
        if dayIndex not in used:
            used[dayIndex] = {}
            
        used[dayIndex][startSlotIndex] = True

    def startAdjacent(dayIndex,startSlotIndex):
        # Determine whether there is an adjacent meeting
        startAbuts = settings.slots[startSlotIndex].startAbuts
        if startAbuts and (startSlotIndex - 1) in used[dayIndex]:
            return True
        return False

    def endAdjacent(dayIndex,endSlotIndex):
        # Determine whether there is an adjacent meeting
        endAbuts = settings.slots[endSlotIndex].endAbuts
        if endAbuts and (startSlotIndex + 1) in used[dayIndex]:
            return True
        return False

    
    for e in events:
        dayIndex = e.dayIndex()
        startSlotIndex = settings.slotNameToIndex[e.startSlot]
        if not startAdjacent(dayIndex,startSlotIndex):
            e.startDateTime -= timedelta(minutes=settings.imatGracePeriod)

        endSlotIndex = settings.slotNameToIndex[e.endSlot]
        if not endAdjacent(dayIndex,endSlotIndex):
            e.endDateTime += timedelta(minutes=settings.imatGracePeriod)
        else:
            e.endDateTime -= timedelta(minutes=1)   # Subtract 1 minute to ensure non-overlapping sessions

def setCredit(settings, events):
    """
    Set credit for events.  Returns a list of ImatEvents
    """
    imatEvents = []
    for e in events:
        credit = settings.slots[settings.slotNameToIndex[e.startSlot]].defaultCredit

        numerator = 1
        denominator = 1
        nSlots = settings.slotNameToIndex[e.endSlot] - settings.slotNameToIndex[e.startSlot] + 1
        if nSlots > 1:
            if credit == "Normal":
                credit = "Other"
            numerator = 2
            denominator = 2
            
        if e.summary in settings.overrideCredit:
            credit = settings.overrideCredit[e.summary].credit
            numerator = settings.overrideCredit[e.summary].numerator
            denominator = settings.overrideCredit[e.summary].denominator

        i = ImatEvent(settings, e.startDateTime, e.endDateTime, e.summary, e.location, e.startSlot, e.endSlot,'',credit,'')
        i.numerator = str(numerator)
        i.denominator = str(denominator)  
        
        imatEvents.append(i)
    return imatEvents   


def addIMATEvent(settings, s, addMeetingURL, startSlots, endSlots, projectIDs, fm, event):
    """
    Add an event to the IMAT session.  
    Parameters:
        headers - dict containing logged-on cookie
        addMeetingURL - URL to page to add meeting form
        startSlots, endSlots - mapping of slot name to slot ID
        projectIDs - mapping of project name to project ID
        fm - field name mapping for form (see addNewMeetingMapping for example)
        event - event as produced by slottify events
    """
    breakout = event.summary
    if breakout.lower() in settings.breakoutToProject:
        project = settings.breakoutToProject[breakout.lower()]
    else:
        print "Unknown breakout '{0}', defaulting to '{1}' for IMAT".format(breakout, settings.defaultProject)
        project = settings.defaultProject
    
    if project in settings.projectToDescriptor:
        descriptor = settings.projectToDescriptor[project]
    else:
        print "Unknown project '{0}', defaulting to '{1}' for IMAT".format(project, settings.defaultProjectDescriptor)
        descriptor = settings.defaultProjectDescriptor
        
    projectID = projectIDs[descriptor]
    
    # The IMAT system has a bug in that an "other" credit cannot be entered on the new meeting form
    # We resolve this by entering it as "normal" and updating it from "normal" to "other" in a subsequent cycle

    summary = event.summary
    if event.deleted:
        summary += " --- cancelled"

    location = event.location
    
    data = {
        'v': '1',                           # Unknown purpose
        fm['Meeting Name']: summary,             # Meeting name
        fm['Group ID']: projectID,                    # Group ID
        fm['Session Day']: str(event.dayIndex()),       # Day of meeting
        fm['Timeslot Start']: startSlots[event.startSlot][0], # Start Slot
        fm['Override Start Time']: event.startDateTime.strftime("%H:%M"), # Start time override
        fm['Timeslot End']: endSlots[event.endSlot][0],   # End slot
        fm['Override End Time']: event.endDateTime.strftime("%H:%M"),   # End slot override
        fm['Location/Room']: location,            # Location / Room
        fm['Facilitator Username or Email']: settings.imatUser,
        fm['Submit'][0]: fm['Submit'][1]
    }
    
    credit = event.credit
    if credit == "Other" and not (('Override Credit Numerator' in fm)):
        credit = "Normal"

    data[fm['Credit'][0]] = fm['Credit'][1][credit]                          # Map credit string to code
    
    if 'Override Credit Numerator' in fm:       # Need to provide a value for these fields
        if credit == "Other":
            data[fm['Override Credit Numerator']] = event.numerator
            data[fm['Override Credit Denominator']] = event.denominator
        else:
            data[fm['Override Credit Numerator']] = '0'
            data[fm['Override Credit Denominator']] = '0'
    

    

    
    r = s.post(addMeetingURL, data=data, allow_redirects=False)
    if r.status_code != 302:
        httpFile=open('temp.html','w')
        httpFile.write(r.text)
        httpFile.close
    
    assert (r.status_code==302), "Cannot create entry"


def updateIMATEvent(settings, s, startSlots, endSlots, projectIDs, editMeetingMapping, f, i):
    """
    Update an existing IMAT event
    Inputs:
        headers - dict containing logged-on cookie
        addMeetingURL - URL to page to add meeting form
        startSlots, endSlots - mapping of slot name to slot ID
        projectIDs - mapping of project name to project ID
        editMeetingMapping - field name mapping for form (see editMeetingMapping for example)
        f - f2f event as produced by slottify events
        i - imat event as produced by getSessionEvents
    """
    addIMATEvent(settings, s, i.edit, startSlots, endSlots, projectIDs, editMeetingMapping, f)
    

def updateIMAT(settings, agendaEvents):
    """
    updateIMAT - given the f2f events list,  main the IMAT session to match it
    input - a list of f2f events,  as produced by getf2fhttp.parseHTTP
    """

    imatSessionsURL = settings.imatBaseURL + "/" + settings.imatUser + "/meetings"

   
    # convert to IMAT slotted events
    slottedAgendaEvents = slottifyEvents (settings, agendaEvents)
    
    # Adjust timings for grace
    adjustForGrace(settings, slottedAgendaEvents)
    
    # Add credit
    imatAgendaEvents = setCredit(settings, slottedAgendaEvents)
    
    # IMAT login, returns a requests.session object used for all subsequent accesses
    s = imatLogin(settings)
    
    # Get a list of sessions known to IMAT for this user
    sessions = getSessions(settings, s, imatSessionsURL)
    
    # Find the URL of the one we are interested in
    sessionURL = getSessionURL(settings, sessions, settings.sessionDateTime)
    assert (sessionURL),"Cannot find session for date " + settings.sessionDate
    
    # Get the events for that session,  and the addMeetingURL
    imatEvents, addMeetingURL = getSessionEvents(settings, s, sessionURL)

        # From the Add meeting form, get the encoding of slots to values
    startSlots, endSlots, projectIDs = getSessionSlots(s, addMeetingURL)


    onlyInAgenda, changed, onlyInIMAT, info = compareEventLists(imatAgendaEvents,"Agenda", imatEvents,"IMAT",True)
    
    if settings.update:
        
        # Add events only in the agenda
        for e in onlyInAgenda:
            addIMATEvent(settings, s, addMeetingURL, startSlots, endSlots, projectIDs, addNewMeetingMapping, e)
            
        # Mark as deleted events only in IMAT
        for e in onlyInIMAT:
            e.deleted = True
            updateIMATEvent(settings, s, startSlots, endSlots, projectIDs, editMeetingMapping, e, e)
            
        # Replace events that are changed    
        for agendaEvent, imatEvent in changed:
            updateIMATEvent(settings, s, startSlots, endSlots, projectIDs, editMeetingMapping, agendaEvent, imatEvent)  

    return info

