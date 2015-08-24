# Settings.py
# Settings common to the "schedule" project,  which updates IMAT and Google calendars, given a meeting agenda.
# Everything that embeds knowledge specific to a project is placed in this file.  Hopefully everything else
# in the other files of this application is non-specific.
#
# If you are using this project for the first time,  please review all the settings and update as necessary.
#
# 2015-03-31 Adrian Stephens
from utils import getDuration
from slot import Slot, Credit


# The settings class stores settings
class Settings(object):
    def __init__(self):
        
        
        # Comment out two if unauthenticated smtp server is not available
        self.notifyEmail = "adrian.p.stephens@intel.com"                         # Email address of person to receive notifications
        #self.smtpHost = "127.0.0.1"                                           # IP address of smtp server (no logon required)
        self.smtpHost = "192.168.0.18"                                           # IP address of smtp server (no logon required)
        
        # Imat user to log in.  Needs to be an administrator of the group's IMAT.
        # Comment out to not update IMAT
        self.imatUser = "adrian.p.stephens@intel.com"                            # IMAT user id to log in and access updateImat data
        
        # Note, the imat user password is stored in a keyring under service='imat' and self.imatUser
        # e.g.
        # >>> import keyring
        # >>> keyring.set_password("imat", settings.imatUser, '<password>')

        # If true, perform update.  If false,  just report differences,  but make no changes.
        self.update = True

        # If true, loop until ^c,  if false,  run in single shot mode
        self.loop = False


        # Session date and timezone =========================================================
        # yyyy-mm-dd Start date of the session (corresponds to Sunday, usually)
        self.sessionDate = "2015-09-13" # Bangkok

        # The meeting timezone,  represented by an integer being the meeting timing offset from UTC in hours
        # e.g. pacific is -8 in winter and -7 in summer
        self.timeZoneOffset = 7    # ict

        # Agenda source definition ===========================================================
        # Define just one of the following variables: f2fScheduleURL, f2fExcelFile, agendaExcelFile

        # Session 91 is May 2015, Vancouver BC
        #self.f2fScheduleURL = "http://802world.org/apps/session/92/attendee/schedule" # Update the session number from F2F numbering
        
        # The full path name to the schedule file sent out by F2F.
        self.f2fExcelFile = r'C:\Users\apstephe\Desktop\Work\2015-09\802-0915-ScheduleofEvents-V1.0.xlsx'
        
        # The full path name of the posted agenda file,  which includes an agenda graphic to be parsed
        #self.agendaExcelFile = r'C:\Users\apstephe\Documents\sandbox\intel\802.11 submissions\WG\may 2015\11-15-0482-d01-0000-may-2015-wg-agenda.xlsx'
        
        # ===================================================================================

                
        # List of strings indicating a group to be included from the f2f agenda
        self.matchGroups = ["11", "802 Wireless", 'Wireless', '11/15/18/19/21/22/24']    
        
        # Google Calendar ID for calendar to update.   Comment out if no calendar is to be updated.
        #self.calendarID = "802_11_calendar@ieee.org"
        self.calendarID = "280qc2oit9csf7vgve0o8u9r9k@group.calendar.google.com" # test calendar
                   
        # HTTP Proxy settings.  Comment out if http access is direct.
        self.proxyIP = "192.168.0.23"
        self.proxyPort = 80
      
        
        #self.proxyIP = "127.0.0.1"
        #self.proxyIP = 'proxy-ir.intel.com'
        #self.proxyPort = 911
      
        
        # Breakout mapping tables ============================================================
        
        # There are several levels of parsing / mapping used from the description in the agenda source.
        # The agenda is first parsed using getShortBreakout to shorten and unify the description.
        # The parsed string is then mapped using the "f2f to breakout" table.
        # This produces the string that describes the breakout, for display in IMAT and in the calendar.
        # The breakout is then mapped to a project, and the project mapped to a group description,
        # which is used to tell IMAT which project to associate affiliation with for attendances to
        # that particular breakout.

        self.f2fToBreakout = {
        '802.11 Opening Plenary': 'Opening Plenary',
        'NM': 'New Members',
        'REVmc': 'TGmc',
        'WNG SC': 'WNG',
        'Wireless NM': "New Members",
        'Wireless Social Reception': "Social Reception"
        }
        
        
        # mapAgendaToSummary is used by the getAgendaEvents module to map the
        # name used in the 802.11 agenda graphic into a breakout name.  The agenda name is
        # usually as brief as possible because space is limited,  which is why it is not
        # the same as the breakout name used by the meeting planners.
        
        # if the getAgendaEvents module is not used, this can be commented out
        self.mapAgendaToSummary = {
           'NM': 'New Members',
           'MC': 'TGmc',
           'AH': 'TGah',
           'AI': 'TGai',
           'AJ': 'TGaj',
           'AK': 'TGak',
           'AQ': 'TGaq',
           'AX': 'TGax',
           'AY': 'TGay',
           'AZ': 'TGaz',
           "Editor's Meeting": 'Editors Meeting',
           "Editors' Meeting": 'Editors Meeting',
           'REG fixed slot': 'REG',
           'Pub': 'PUB',
           'NGP': 'NGP SG',
           'LRLP': 'NGP TIG'
        }
           
        
        # List of breakouts not to post in either calendar or IMAT
        self.doNotPost = ['Executive Leadership Mtg', '802.11 Leadership', 'Leadership Meeting', '802.11 Executive Leadership Mtg']
       
      
        # List of breakouts that may go on the calendar,  but should not go in IMAT
        self.doNotPostIMAT = ['Joint Opening Plenary', 'Social Reception', 'Wireless Leadership Meeting', 
                              'Wireless Joint Opening Plenary', 'Wireless Social Reception', 'Wireless Chairs',
                              '802.11/15/18/19/21/22/24 Wireless Chairs']

        # Mapping of breakout to project.  The concept of "project" is local to this application.
        # Note, the breakout must be lower case.  Project is in mixed case.
        self.breakoutToProject = {
        'cac': '802.11',
        'closing plenary': '802.11',
        'editors meeting': '802.11',
        'mid-week plenary': '802.11',
        'midWeek plenary': '802.11',
        'opening plenary': '802.11',
        'joint 802.1 + 802.11 tgak/arc': 'TGak',
        'arc': '802.11',
        'jtc1': '802.11',
        'ngp sg': '802.11',
        'lrlp': '802.11',
        'new members': '802.11',
        'par': '802.11',
        'reg': '802.11',
        'joint 802.11/802.15 reg sc': '802.11',
        'pub': '802.11',
        'wng': '802.11',
        'tgah': 'TGah',
        'tgai': 'TGai',
        'tgaj': 'TGaj',
        'tgak': 'TGak',
        'tgaq': 'TGaq',
        'tgax': 'TGax',
        'tgay': 'TGay',
        'tgmc': 'TGmc'
        }
        
        # Mapping from projects to the IMAT project descriptors
        self.projectToDescriptor = { '802.11': "C/LM/WG802.11",
        'TGmc': "C/LM/WG802.11/802.11",
        'TGah': "C/LM/WG802.11/802.11ah",
        'TGai': "C/LM/WG802.11/802.11ai",
        'TGaj': "C/LM/WG802.11/802.11aj",
        'TGak': "C/LM/WG802.11/802.11ak",
        'TGaq': "C/LM/WG802.11/802.11aq",
        'TGax': "C/LM/WG802.11/802.11ax",
        'TGay': "C/LM/WG802.11/802.11ay" }
        
        # These projects are used to collect affiliation if not found in the mapping tables above
        # A warning to STDOUT will be generated if the default is used so that the above tables can
        # be populated.
        self.defaultProject = '802.11'
        self.defaultProjectDescriptor = 'C/LM/WG802.11'
        
                   
        # IMAT related ===============================================================


        # Grace period to apply to slot boundaries.  This allows folks to recored
        # attendance before the meeting starts or after it ends.
        # The value is in minutes and must be less than half the gap between slots
        # that are not indicated as abutted in the slots table
        self.imatGracePeriod = 10
        
        # Mapping table of slots to time.
        # The start and end times should describe the official times of the slot (inclusive), and should not overlap with adjacent slots.
        # The extended start and end dates should fully cover a 24-hour period and should not overlap with adjacent slots.
        # Slots should be ordered by increasing time
        self.slots = [                   
                      Slot(0, 'AM0', '07:00', '07:59', '00:00', '07:59', 'Extra'),
                      Slot(1, 'AM1', '08:00', '10:00', '08:00', '10:29', 'Normal'),
                      Slot(2, 'AM2', '10:30', '12:30', '10:30', '12:59', 'Normal'),
                      Slot(3, 'PM1', '13:30', '15:30', '13:00', '15:59', 'Normal'),
                      Slot(4, 'PM2', '16:00', '18:00', '16:00', '18:00', 'Normal'),
                      Slot(5, 'EVE1', '19:30', '21:30', '18:01', '23:59', 'Extra')
        ]
        
        
        # Override credit settings for specific breakouts that do not follow the credit
        # determined by the starting slot position as shown in the 'slots' dict above.
        # Format:  '<breakout name>': ['<credit>', <numerator>, <denominator>]
        # NOTE - meetings in this table are not split into slots if they would normally
        # be slotted into multiple meetings when converting from a f2f to imat event
        self.overrideCredit = {
                          #'Editors Meeting':    Credit('Extra', 0, 0), # to avoid being split into two
                          #'CAC':                Credit('Extra', 0, 0),
                          'Closing Plenary':    Credit('Other', 2, 2)
                          }
                            
        # Shouldn't need to update these:
        self.loginURL = "https://development.standards.ieee.org/pub/login"
        self.imatBaseURL = "https://imat.ieee.org"
        
        
        # Google Calendar related ==============================================================
        
        # Google calendar client application credentials.   Please do not use these credentials
        # for any other purpose.
        self.client_id='272983310920-lb8r4aiea6ajg4qnue22rsud145f1n1r.apps.googleusercontent.com'
        self.client_secret='itiDjnuiBf4YXx5oMi71c43c'
        self.scope='https://www.googleapis.com/auth/calendar'
        self.user_agent= "Adrian's Calendar App/1.0"
        self.developerKey="AIzaSyDtx2qkP2HqI7y-WHVI52nlnhJW0TmyVa0"          



        # Create derived values and check consistency of slots
        self.setupSlots()
        self.setupDays()                        


    
    def setupSlots(self):
        self.nSlots = len(self.slots)
        self.slotIndexToSlotName = []
        for slot in self.slots:
            self.slotIndexToSlotName.append(slot.name)
            
        self.slotNameToIndex = {}
        for slot in self.slots:
            self.slotNameToIndex[slot.name] = slot.index
        
        # Check for valid times and determine "abuts"
        for i in range(self.nSlots):
            assert ( self.slots[i].start < self.slots[i].end)
            assert ( self.slots[i].extendedStart < self.slots[i].extendedEnd)
            if i > 0:
                assert (self.slots[i-1].end < self.slots[i].start)
                assert (self.slots[i-1].extendedEnd < self.slots[i].extendedStart)
                gap = getDuration(self.slots[i].start, self.slots[i-1].end) - 1
                if gap < self.imatGracePeriod:
                    self.slots[i-1].endAbuts = True
                    self.slots[i].startAbuts = True
     
    def setupDays(self):
        
        from datetime import datetime, timedelta
        
        oneDay = timedelta(days=1)
        
        self.sessionDateTime = datetime.strptime(self.sessionDate, "%Y-%m-%d")       
        self.sessionDateTimes = []

        # Long and short day names indexed by meeting day offset
        self.days = []
        self.shortDays = []
        
        thisDay = self.sessionDateTime
        for i in range(7):
            self.sessionDateTimes.append(thisDay)
            self.days.append(datetime.strftime(thisDay,'%A'))
            self.shortDays.append(datetime.strftime(thisDay,'%a'))
            thisDay += oneDay
            
    
    def getShortBreakout (self, b):
        """
        Parse F2F or Agenda breakout description line to return a shorter form
        Example input: "802.11 TGah -- 900 MHz bands"
        Example output: "TGah"
        """
        import re
        
        # Change 802.Wireless to 802 Wireless
        pattern = "^802\\.(Wireless .*)$"
        if re.match(pattern, b):
            b = re.sub(pattern,"\\1", b).strip()
        
        # Remove leading 802[.group]
        pattern = "^802(.[0-9]*)? (.*)$"
        if re.match(pattern, b):
            b = re.sub(pattern,"\\2", b).strip()
        
        # Remove leading WG
        pattern = "^WG (.*)$"
        if re.match(pattern, b):
            b = re.sub(pattern,"\\1", b).strip()
        
        # If matches "- ",  only keep stuff before that
        pattern = "([^-]+)(-)+( )+.*$"
        if re.match(pattern, b):
            b = re.sub(pattern,"\\1", b).strip()
    
        # Remove any trailing asterisks. Note: non-greedy search on .*
        pattern = "^(.*?) ?\*+$"
        if re.match(pattern, b):
            b = re.sub(pattern,"\\1", b).strip()
    
        # In TGxy, ensure xy is lower case
        pattern = "^TG([A-Za-z]+)$"
        if re.match(pattern, b):
            letters = re.sub(pattern,"\\1", b).strip()
            b = "TG" + letters.lower()   
    
        return b.strip()

    def defined(self, n):
        """
        Return True if n is defined for settings
        """
        return n in self.__dict__
    