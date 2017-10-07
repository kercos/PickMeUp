# coding=utf-8

from datetime import datetime
from datetime import timedelta
import time

def nowUTC():
    return datetime.now()

def convertUTCtoCET(dt_utc):
    from pytz_zip.gae import pytz_zip
    UTC_ZONE = pytz_zip.timezone('UTC')
    CET_ZONE = pytz_zip.timezone('Europe/Amsterdam')  # pytz.timezone('CET')
    return dt_utc.replace(tzinfo=UTC_ZONE).astimezone(CET_ZONE)

def convertCETtoUTC(dt_utc):
    from pytz_zip.gae import pytz_zip
    UTC_ZONE = pytz_zip.timezone('UTC')
    CET_ZONE = pytz_zip.timezone('Europe/Amsterdam')  # pytz.timezone('CET')
    return dt_utc.replace(tzinfo=CET_ZONE).astimezone(UTC_ZONE)

def nowCET(removeTimezone = False):
    utc = nowUTC()
    cet = convertUTCtoCET(utc)
    if removeTimezone:
        cet = cet.replace(tzinfo=None)
    return cet

#'%H:%M:%S.%f'
#'%H:%M:%S'
def datetimeStringCET(dt=None, seconds=False, format = None):
    if dt == None:
        dt = nowCET()
    dt_cet = convertUTCtoCET(dt)
    if format == None:
        format = '%d-%m-%Y %H:%M:%S' if seconds else '%d-%m-%Y %H:%M'
    return dt_cet.strftime(format)

def formatDateTime(dt, format='%d-%m-%Y %H:%M'):
    if dt:
        return dt.strftime(format)
    return None

def formatDate(dt=None, format ='%d-%m-%Y'):
    if dt == None:
        dt = nowCET()
    return dt.strftime(format)

def getCurrentYearCET():
    dt_cet = convertUTCtoCET(nowUTC())
    return int(dt_cet.strftime('%Y'))


# Return the day of the week as an integer,
# where Monday is 0 and Sunday is 6
def getWeekday(dt=None):
    if dt == None:
        dt = nowCET()
    return dt.weekday()

def get_midnight(date = None):
    if date == None:
        date = nowCET()
    return date.replace(hour=0, minute=0, second=0, microsecond=0)

def delta_min(dt1, dt2):
    diff = dt2 - dt1
    min_sec = divmod(diff.days * 86400 + diff.seconds, 60) # (min,sec)
    return min_sec[0]

def delta_days(dt1, dt2):
    diff = dt2 - dt1
    return diff.days

def ellapsed_min(dt):
    return delta_min(dt, nowCET())

def get_datetime_add_days(days, dt = None):
    if dt == None:
        dt = nowCET()
    return dt + timedelta(days=days)

def get_datetime_add_minutes(min, dt = None):
    if dt == None:
        dt = nowCET()
    return dt + timedelta(minutes=min)

def get_datetime_days_ago(days, dt = None):
    if dt == None:
        dt = nowCET()
    return dt - timedelta(days=days)

def tomorrow(dt = None):
    if dt == None:
        dt = nowCET()
    return dt + timedelta(days=1)

def get_datetime_hours_ago(hours, dt = None):
    if dt == None:
        dt = nowCET()
    return dt - timedelta(hours=hours)

def getTime(time_str, format='%H:%M'):
    try:
        return datetime.strptime(time_str, format)
    except ValueError:
        return None

def formatTime(dt, format='%H:%M'):
    return dt.strftime(format)

def convertSecondsInHourMinString(seconds):
    import time
    hh, mm, sec = [int(x) for x in time.strftime('%H:%M:%S', time.gmtime(seconds)).split(':')]
    if sec >= 30:
        mm += 1
    if hh:
        return '{} ora {} minuti'.format(hh, mm)
    else:
        return '{} minuti'.format(mm)

def getDatetime(date_string, format='%d%m%Y'):
    try:
        date = datetime.strptime(date_string, format)
    except ValueError:
        return None
    return date

def removeTimezone(dt):
    return dt.replace(tzinfo=None)

def getDateFromDateTime(dt = None):
    if dt == None:
        dt = nowCET()
    return datetime.date(dt)

def getMinutes(input):
    t1 = datetime.strptime(input, '%H:%M')
    t2 = datetime.strptime('00:00', '%H:%M')
    return int((t1-t2).total_seconds()//60)

def get_date_tomorrow(dt):
    return dt + timedelta(days=1)



'''

def now(addMinutes=0):
    return datetime.now() + timedelta(minutes=int(addMinutes))

def get_today():
    return datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)

def delta_min(date1, date2):
    diff = date2 - date1
    min_sec = divmod(diff.days * 86400 + diff.seconds, 60) # (min,sec)
    return min_sec[0]

def ellapsed_min(date):
    return delta_min(date, now())

def get_last_week():
    return datetime.now() - timedelta(days=7)

def get_date_days_ago(days):
    return datetime.now() - timedelta(days=days)

def get_date_hours_ago(days):
    return datetime.now() - timedelta(hours=days)

def get_date_CET(date):
    if date is None: return None
    newdate = date  + timedelta(hours=2)
    return newdate

def get_date_CET_from_DDMMYY(dateString):
    date = datetime.strptime(dateString,'%d%m%y')
    return get_date_CET(date)

def get_date_string(date):
    newdate = get_date_CET(date)
    time_day = str(newdate).split(" ")
    time = time_day[1].split(".")[0]
    day = time_day[0]
    return day + " " + time

def get_time_string(date):
    newdate = get_date_CET(date)
    result =  str(newdate).split(" ")[1].split(".")[0]
    return result.encode('utf-8')

def isTimeFormat(input):
    try:
        datetime.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False

def getMinutes(input):
    t1 = datetime.strptime(input, '%H:%M')
    t2 = datetime.strptime('00:00', '%H:%M')
    return int((t1-t2).total_seconds()//60)

'''