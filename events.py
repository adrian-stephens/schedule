# Events
# Class definitions for events

from datetime import timedelta, datetime


# Base Event type

class Event(object):
    """
    Base class for all meeting events.  Times and dates are in the meeting locale.
    """
    
    def __init__(self,settings,startDateTime,endDateTime,summary,location):
        self.sessionDateTime = settings.sessionDateTime
        self.startDateTime = startDateTime  # In the local meeting timezone
        self.endDateTime = endDateTime # In the local meeting timezone
        self.summary = summary
        self.deleted = False
        self.timeZoneOffset = settings.timeZoneOffset
        if location != None:
            self.location = location
        else:
            self.location = ''

          
    def endsBefore(self, endDateTime):
        return self.endDateTime < endDateTime
    
    def startDateTimeUTC(self):
        return self.startDateTime - timedelta(hours=self.timeZoneOffset)

    def endDateTimeUTC(self):
        return self.endDateTime - timedelta(hours=self.timeZoneOffset)
    
    def __repr__(self):
        s = "Event %s-%s '%s' " % (self.startDateTime, self.endDateTime, self.summary)
        if len(self.location) > 0:
            s += "in %s " % (self.location,)
        return s
    
    def shortStr(self):
        """
        Return a short string to identify the meeting uniquely
        """
        return "%s %s '%s'" % (self.startDateTime.strftime("%Y-%m-%d %a"), self.startDateTime.time(), self.summary)
    
    # Equality is determined by a matching start and summary
    def __eq__(self,obj):
        return (self.startDateTime == obj.startDateTime) and (self.summary == obj.summary)

    def __ne__(self,obj):
        return not self == obj
    
    
    def changed(self,obj):
        """ 
        Determine if self and obj have changed
        """
        if self.startDateTime != obj.startDateTime:
            return True

        if self.endDateTime != obj.endDateTime:
            return True

        if self.summary != obj.summary:
            return True
            
        if (len(self.location) > 0) and (len(obj.location) > 0) and (self.location != obj.location):
            return True
       
        if self.deleted and not obj.deleted:
            return True
            
#        if self.deleted != obj.deleted:
#            return True

        return False    
        
    
    def diff(self,obj):
        """ 
        Returns a string describing differences between two objects
        """
        s = ''
        if self.startDateTime != obj.startDateTime:
            s += '%s start changed: to %s from %s. ' % (self.shortStr(), self.startDateTime, obj.startDateTime)

        if self.endDateTime != obj.endDateTime:
            s += '%s end changed: to %s from %s. ' % (self.shortStr(), self.endDateTime, obj.endDateTime)

        if self.summary != obj.summary:
            s += '%s summary changed: to %s from %s. ' % (self.shortStr(), self.summary, obj.summary)
            
        if (len(self.location) > 0) and (len(obj.location) > 0) and (self.location != obj.location):
            s += '%s location changed: to %s from %s. ' % (self.shortStr(), self.location, obj.location)
            
        if self.deleted and not obj.deleted:
            s += '%s deleted changed: %s. ' % (self.shortStr(), 'now marked deleted')


#        if self.deleted != obj.deleted:
#            s += '%s deleted changed: %s. ' % (self.shortStr(), 'now marked deleted' if self.deleted else 'deletion marker removed')
        
        if len(s) > 0:
            s += '\n'
            
        return s    
            
    # Return day index of start time
    def dayIndex(self):
        td = self.startDateTime - self.sessionDateTime
        return td.days

        

class SlottedEvent(Event):
    """
    Class for events that have been assigned start and end slots
    """
    def __init__(self,settings,startDateTime,endDateTime,summary,location,startSlot,endSlot):
        super(SlottedEvent, self).__init__(settings,startDateTime,endDateTime,summary,location)
        self.startSlot = startSlot
        if endSlot != None:
            self.endSlot = endSlot
        else:
            self.endSlot = startSlot
    
    def __repr__(self):
        return super(SlottedEvent, self).__repr__() + " %s-%s" % (self.startSlot, self.endSlot)
    
    # Equality is determined by a matching start date and slot and summary
    def __eq__(self,obj):
        return (self.dayIndex() == obj.dayIndex()) and \
            (self.startSlot == obj.startSlot) and \
            (self.summary == obj.summary)
            


    
    
class ImatEvent(SlottedEvent):
    """
    Class to hold all information in an IMAT Event.  Adds IMAT accounting data to slotted event.
    """
    def __init__(self,settings,startDateTime,endDateTime,summary,location,startSlot,endSlot,group,credit,edit):
        super(ImatEvent, self).__init__(settings,startDateTime,endDateTime,summary,location,startSlot,endSlot)
        self.group = group
        self.credit = credit
        self.edit = edit
        self.numerator = '0'
        self.denominator = '0'

    def __repr__(self):
        return super(ImatEvent, self).__repr__() + " %s %s (%s/%s)" % (self.group, self.credit, self.numerator, self.denominator)
    
    
    def creditChanged(self,obj): 
        """
        Indicate if a significant change has been made to credit
        """
        if self.credit != obj.credit:
            # We generally don't enforce our automated view of credit.  It it's
            # been changed on IMAT,  that is presumably for a good reason.  However
            # The closing plenary has to be progressed automatically from "Normal" to
            # "Other" as the dialog on which the meeting was initially created doesn't
            # support "Other"
            if self.credit == 'Other' and obj.credit == 'Normal':
                return True       
            
        return False

    def changed(self,obj):
        """ 
        Determine if self and obj have changed
        """
        
        if self.creditChanged(obj):
                return True
            
        return super(ImatEvent, self).changed(obj)
    
    def diff(self,obj):
        """ 
        Returns a string describing differences between two objects
        """
        s = super(ImatEvent, self).diff(obj)
        if self.creditChanged(obj):
            s += '%s credit changed: to %s from %s.\n' % (self.shortStr(), self.credit, obj.credit)
    
        return s
    
def compareEventLists(l1,n1,l2,n2):
    """
    Compare two event lists l1 and l2 called n1 and n2,  ignoring any events that ended in the past.
    When one of the lists is on IMAT,  it is l2.
    Returns:
        a list events only in l1
        a list [l1, l2] tuples of those changed
        a list of events only in l2
        A string describing the changes that will be made to resolve any differences.  This string
        assumes that l1 is the "new" state and l2 the "old" state,  and that changes will be made
        to match the new state.
    """
    # Current time in UTC
    now = datetime.utcnow()
    onlyInL1 = []
    onlyInL2 = []
    changed = []
    
    s = ''
    
    for e1 in l1:
        
        # Ignore events that end in the past        
        if e1.endDateTimeUTC() <= now:
            continue
        
        # Ignore events marked deleted
        if e1.deleted:
            continue
        
        found = False
        for e2 in l2:
            if e1 == e2:
                if e1.changed(e2):
                    changed.append((e1, e2))
                s += e1.diff(e2)
                found = True
                break
        if not found:
            onlyInL1.append(e1)
            s += "%s: New in %s\n" % (e1.shortStr(), n1)
        
    for e2 in l2:
        
        # Ignore events that end in the past        
        if e2.endDateTimeUTC() <= now:
            continue
        
        # Ignore events marked as deleted
        if e2.deleted:
            continue
        
        found = False
        for e1 in l1:
            if e1 == e2:
                found = True
                break
        if not found:
            onlyInL2.append(e2)
            s += "%s: Deleting item only in %s\n" % (e2.shortStr(), n2)
      
    return (onlyInL1, changed, onlyInL2, s)
