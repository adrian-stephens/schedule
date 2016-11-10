# Get F2F excel
#
# Get f2f schedule from excel document
from xlrd.xldate import xldate_as_datetime
from datetime import datetime, timedelta
from events import Event


layout = {
    'Day': { 'aliases': ['day'], 'present': False, 'required': True, 'column': 0},
    'StartTime': { 'aliases': ['start', 'start time'], 'present': False, 'required': True, 'column': 0},
    'EndTime': { 'aliases': ['end', 'end time'], 'present': False, 'required': True, 'column': 0},
    'Group': { 'aliases': ['group', 'grp'], 'present': False, 'required': True, 'column': 0},
    'Meeting': { 'aliases': ['meeting', 'breakout'], 'present': False, 'required': True, 'column': 0},
    'Room': { 'aliases': ['room'], 'present': False, 'required': True, 'column': 0},
    'Location': { 'aliases': ['location'], 'present': False, 'required': False, 'column': 0}
}

import xlrd
from utils import f2fMergeRooms,getWanted,sortEvents


def getExcelTime(v,datemode):
    try:
        return xldate_as_datetime(v,datemode).time()

    # Not a valid excel time format
    except:
        v = v.replace(";",":")
        return datetime.strptime(v, "%H:%M").time()


def getf2fExcelEvents(settings):
    """ 
    Read the Face-to-Face excel spreadsheet and return parsed events
    """
    
    book = xlrd.open_workbook(settings.f2fExcelFile)
    
    
    foundSheet = False
    for s in book.sheets():
        if (s.name.lower().find('schedule') >= 0) and not (s.name.lower().find('key') >= 0):
            foundSheet = True
            break
        if (s.name.lower().find('meeting') >= 0) and not (s.name.lower().find('key') >= 0):
            foundSheet = True
            break    
        
    assert (foundSheet),"Cannot find Schedule sheet in spreadsheet"
        
    foundHeader = False
    for rowIndex in range(s.nrows):
        for colIndex in range(s.ncols):
            v = s.cell(rowIndex,colIndex).value
            if v.lower() in layout['Day']['aliases']:
                foundHeader = True
                break
        if foundHeader:
            headerIndex = rowIndex
            break
       
    assert (foundHeader),"Cannot find header row in Schedule"
    
    for key in layout.keys():
        for colIndex in range(s.ncols):
            v = s.cell(headerIndex,colIndex).value
            if v.lower() in layout[key]['aliases']:
                layout[key]['present'] = True
                layout[key]['column'] = colIndex
                break
         
        if layout[key]['required']:
            assert (layout[key]['present']),"Cannot find %s in header row" % (key,)
    
    entries = []    
    for rowIndex in range( headerIndex+1, s.nrows):
        v = s.cell(rowIndex, layout['Day']['column']).value
        d = None
        if v in settings.days:
            # It's a day name - convert to date
            for dateIndex in range(len(settings.days)):
                if v == settings.days[dateIndex]:
                    d = settings.sessionDateTimes[dateIndex]
                    break
                
        else: # Assume it's an excel date
            try:
                d = xldate_as_datetime(v,book.datemode)
            except:
                pass
        
        if not d:
            continue
        
        
        v = s.cell(rowIndex, layout['StartTime']['column']).value
        
        startTime = getExcelTime(v,book.datemode)

        # Start and end times are in the meeting timezone        
        startDateTime = d + timedelta(hours = startTime.hour, minutes = startTime.minute)
    
        v = s.cell(rowIndex, layout['EndTime']['column']).value
        endTime = getExcelTime(v,book.datemode)

        endDateTime = d + timedelta(hours = endTime.hour, minutes = endTime.minute)
    
        group = s.cell(rowIndex, layout['Group']['column']).value
        if s.cell_type(rowIndex, layout['Group']['column']) == xlrd.XL_CELL_NUMBER:
            group = "%d" % (group,)
            
        
        breakout = s.cell(rowIndex, layout['Meeting']['column']).value
        shortBreakout = settings.getShortBreakout(breakout)
        
        # Apply optional mapping to f2f description
        if shortBreakout in settings.f2fToBreakout:
            shortBreakout = settings.f2fToBreakout[shortBreakout]
        
        
        wanted, inIMAT = getWanted(settings,group,shortBreakout)
        
        if not wanted:
            continue
        
        room = s.cell(rowIndex, layout['Room']['column']).value
    
    
        if layout['Location']['present']:
            v = s.cell(rowIndex, layout['Location']['column']).value
            room += " (%s)" % (v,)
        
        entry = Event(settings, startDateTime, endDateTime, shortBreakout, room, inIMAT, group)    
        entries.append(entry)

    return f2fMergeRooms(sortEvents(entries))
    
