# getAgendaEvents
#
# Parse an agenda and return a list of Event.event objects representing the agenda graphic


agendaFileName = r'C:\Users\apstephe\Documents\sandbox\intel\802.11 submissions\WG\may 2015\11-15-0482-d01-0000-may-2015-wg-agenda.xlsx'
import xlrd

from xlrd.xldate import xldate_as_datetime
from datetime import datetime, timedelta
from events import Event, compareEventLists
from getf2fhttp import getf2fhttpEvents
from getf2fExcel import getf2fExcelEvents

doNotPostAgenda = ["Break", 'Dinner Break', 'Social', 'Lunch Break', 'Wireless Chairs Meeting']

def getMeetingSummary(settings, s):
    """
    Parse meeting name in agenda graphic into a value that is similar to that used in the F2F breakout
    """
    
    # Take the last line of a multi-line entry
    p = s.split('\n')      
    b = settings.getShortBreakout(p[len(p)-1])
    if b in settings.mapAgendaToSummary:
        b = settings.mapAgendaToSummary[b]
    return b


def parseTimeRange(s):
    """
    Parse a time range of the format '10:00-10:30
    """
    # Trim any leading quote
    if s[0] == "'":
        s = s[1:]

    t=s.split('-')
    t1=datetime.strptime(t[0], "%H:%M").time()
    t2=datetime.strptime(t[1], "%H:%M").time()
    
    return t1, t2
    
def getAgendaEvents(settings):
    """
    Read meeting events from the agend excel file
    """
    book = xlrd.open_workbook(settings.agendaFileName)

    assert (book),"Cannot open agenda file"
    
    sheet = book.sheet_by_name('Agenda Graphic')
    
    assert (sheet),"Cannot open agenda graphic"
    
    # Find the rowIndex for the Heading row
    foundHeader = False
    for rowIndex in range(sheet.nrows):
        v = sheet.cell(rowIndex,0).value
        if sheet.cell_type(rowIndex,0) == xlrd.XL_CELL_TEXT:          
            if v.lower() == 'time':
                foundHeader = True
                break
    
    assert (foundHeader),"Cannot find header row"
    
    headerRow = rowIndex
    
    # Unpack time ranges
    slots = [ {} for __i__ in range(sheet.nrows) ]
    for rowIndex in range(headerRow+1,sheet.nrows):
        v = sheet.cell(rowIndex,0).value
        if not v:
            break
        start, end = parseTimeRange(v)
        slotEntry = {'start': start, 'end': end}
        slots[rowIndex] = slotEntry    
    
    maxColIndex = len(sheet.row(headerRow)) - 1
    assert (maxColIndex > 1),"Silly header row contents"
          
    events = []       
    dayColIndex = 1     # Column index of start of current day
    while dayColIndex <= maxColIndex:
        
        # Process a day.  First identify the width of the column

        heading = sheet.cell(headerRow,dayColIndex).value
        headingType = sheet.cell_type(headerRow,dayColIndex)
        if headingType == xlrd.XL_CELL_DATE:
            heading = xldate_as_datetime(heading, book.datemode)

        # Look up heading in merged cells list
        dayColWidth = 1
        for mc in sheet.merged_cells:
            rowLow, rowHighp1, colLow, colHighp1 = mc
            if (headerRow == rowLow) and (dayColIndex == colLow):
                dayColWidth = colHighp1 - colLow
      
        for colIndex in range(dayColIndex, min(dayColIndex + dayColWidth, maxColIndex + 1)):
            for rowIndex in range (headerRow + 1, sheet.nrows):
           
                itemValue = sheet.cell(rowIndex,colIndex).value
                itemType = sheet.cell_type(rowIndex, colIndex)
                if itemType == xlrd.XL_CELL_EMPTY:
                    continue        
                
                if not itemValue or (len(itemValue) == 0):
                    continue
                
                # Find any matching merged cell information
                itemHeight = 1
                for mc in sheet.merged_cells:
                    rowLow, rowHighp1, colLow, colHighp1 = mc
                    if (rowIndex == rowLow) and (colIndex == colLow):
                        itemHeight = rowHighp1 - rowLow

                         
                            
                if ('start' in slots[rowIndex]):
                    startTime = slots[rowIndex]['start']
                    endTime = slots[rowIndex + itemHeight - 1]['end']
                    startDateTime = heading + timedelta(hours=startTime.hour, minutes=startTime.minute)
                    endDateTime = heading + timedelta(hours=endTime.hour, minutes=endTime.minute)
                    summary = getMeetingSummary(settings, itemValue)

                    if summary not in settings.doNotPostAgenda:
                        newEvent = Event(startDateTime, endDateTime, summary, '')
                        events.append(newEvent)              
        
        # Process next day
        assert (dayColWidth > 0),"Silly day column width"
        dayColIndex += dayColWidth

    assert (len(events) > 0),"No events found in agenda"
    
    return events

def main():
    agendaEvents = getAgendaEvents()
    if 'scheduleURL' in globals():
        f2fEvents = getf2fhttpEvents()
    elif 'excelFile' in globals():
        f2fEvents = getf2fExcelEvents() 
    else:
        assert (False),"No source for F2F schedule" 
    
    print compareEventLists(agendaEvents, "Agenda", f2fEvents, "F2F")


if __name__ == '__main__':
    main()
    
