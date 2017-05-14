# sendEmail.py
# 2015-04-04 Adrian Stephens
# Send email notifying changes to recipient specified in settings.

import smtplib
from email.mime.text import MIMEText
from datetime import datetime


def sendEmail (settings,text):
    
    if 'smtpHost' not in settings.__dict__:
        return

    if not settings.defined('imatUser'):
        return

    # Construct email
    try:
        msg = MIMEText(text)
        msg['To'] = settings.notifyEmail
       
        msg['From'] = settings.imatUser
        msg['Subject'] = "Automated IMAT main, sent at " + datetime.now().strftime("%Y-%m-%d %H:%M")
        
        mySmtp= smtplib.SMTP(settings.smtpHost)
        mySmtp.sendmail(settings.imatUser,settings.notifyEmail,msg.as_string())
        mySmtp.quit()
    except:
        print "Cannot send email"
    