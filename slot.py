# slot.py

# The Slot class stores timing-related information related to an IMAT meeting slot
# Mapping table of slots to time. 
#    start & End: times for start and end of the slot (omitting grace period) - string
#    index: the zero-based slot index
#    defaultCredit: the default type of credit - string
#    startAbuts: True/False indicating whether the Start abuts the previous slot
#    endAbuts: True/False indicating whether the End abuts the previous slot
#    extendedStart and extendedEnd: time for start and end of the slot extending slot boundaries so they touch - string
class Slot(object):
    
    
    def __init__(self, index, name, start, end, extendedStart, extendedEnd, defaultCredit):
        from datetime import datetime
        self.index = index
        self.name = name
        self.start = datetime.strptime(start,"%H:%M").time()
        self.end = datetime.strptime(end,"%H:%M").time()
        self.extendedStart = datetime.strptime(extendedStart,"%H:%M").time()
        self.extendedEnd = datetime.strptime(extendedEnd,"%H:%M").time()
        self.defaultCredit = defaultCredit
        self.startAbuts = False
        self.endAbuts = False

# The credit class defines overridden credit
class Credit(object):
    def __init__(self, credit, numerator, denominator):
        self.credit = credit                # String
        self.numerator = numerator          # Integer
        self.denominator = denominator      # Integer
