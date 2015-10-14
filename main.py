# update.py
# 2015-04-04 Adrian Stephens
# 
# This program performs an update of online google calendar and updateImat session details from the Face-to-Face attendee website
# This is the main program
#
# Prerequisites:
# 1. run: "pip install --upgrade google-api-python-client"
# 2. A writable google calender,  identified by the Google calender ID.
# 3. The password for the updateImat user installed in a keyring using:
# >>> keyring.set_password("updateImat", '<imatUser>', '<password>')
#
# Caveats.  The google Calendar authentication is pretty unpredictable.  It will throw up a browser window to complete
# Authentication when it determines this is required.  If it keeps doing so every run,  the local credentials.dat
# will not be holding a "refresh token".  To get one,  using your google settings,  remove "Adrians Calendar application"
# from authenticated applications and try again.  This time you should get a brower prompt with a yes / no in it,
# and a refresh token should be created.   Thereafter,  hopefully brower prompts will be a thing of the past.


from updateImat import updateIMAT
from getf2fhttp import getf2fhttpEvents
from getAgendaEvents import getAgendaEvents
import settings
from updateGoogleCalendar import updateGoogleCalendar
import time

from sendEmail import sendEmail
from getf2fExcel import getf2fExcelEvents

settings = settings.Settings()

def processOnce(settings):
    
    info = ''

    try:    
    
        if settings.defined('f2fScheduleURL'):
            events = getf2fhttpEvents(settings)
        elif settings.defined('f2fExcelFile'):
            events = getf2fExcelEvents(settings) 
        elif settings.defined('agendaExcelFile'):
            events = getAgendaEvents(settings)
        else:
            assert (False),"No source for F2F or Agenda schedule"  

        # Update IMAT
        if settings.defined('imatUser'):
            info += updateIMAT(settings, events)
        
        # Update the online Google Calendar
        if settings.defined('calendarID'):
            info += updateGoogleCalendar(settings, events)

    except KeyboardInterrupt:
        raise                   # Pass exception on to main loop
    
    except:
        if settings.loop:
            # Summarise the exception,  but keep executing
            import sys
            info = "Unexpected exception:" + str(sys.exc_info())
        else:
            raise       # Report the exception and break execution
    
    if len(info) > 0:
        if not settings.update:
            info = "WARNING: Dry run.  No changes made. \n" + info
        print info
        sendEmail(settings, info)


        

    
def processLoop(settings):
    
    
    try:    # Main program loop until keyboard interrupt
        while True:
            processOnce(settings)     

            if not settings.loop:
                print "Exiting single loop in 5s"
                time.sleep(5)
                break
            
            time.sleep(10 * 60)


    except KeyboardInterrupt:   # ^C pressed
        print ('Interrupted')
        import sys
        sys.exit()
  
    
if __name__ == '__main__':    
    processLoop(settings)