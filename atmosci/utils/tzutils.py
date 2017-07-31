""" methods for managing time zones in datetime.datetime objects
"""
import datetime
import pytz
import tzlocal

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ARG_TYPE_ERROR = '"%s" is an invalid type for "%s" argument.'

HOUR_STRING_FORMAT = '%Y-%m-%d:%H'
VALID_TIME_STRING = datetime.datetime(1970,1,1,0).strftime(HOUR_STRING_FORMAT)
VALID_DATE_STRING, VALID_HOUR_STRING = VALID_TIME_STRING.split(':')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# FUNCTIONS THA OPERATE ON TIME ZONES (not times)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def asTimezoneObj(timezone):
    if isinstance(timezone, pytz.tzinfo.BaseTzInfo): return timezone
    elif type(timezone) == type(pytz.UTC): return timezone
    else: return pytz.timezone(timezone)

def hasValidTimezone(hour):
    return isValidTimezoneObj(hour.tzinfo)

def isInTimezone(date_time, timezone):
    if isinstance(date_time, datetime.datetime):
        return date_time.tzinfo == asTimezoneObj(timezone)
    else: return False

def isValidTimezone(timezone):
    if isinstance(timezone, pytz.tzinfo.BaseTzInfo): return True
    elif type(timezone) == type(pytz.UTC): return True
    try:
        tz = pytz.timezone(timezone)
    except:
        return False
    return True

def isValidTimezoneObj(timezone):
    if isinstance(timezone, pytz.tzinfo.BaseTzInfo): return True
    elif type(timezone) == type(pytz.UTC): return True
    else: return False

def timezoneAsString(timezone):
    return str(timezone)

def timezoneForDatetime(date_time):
    if isValidTimezoneObj(date_time.tzinfo): return date_time.tzinfo
    return None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# FUNCTIONS THAT OPERATE ON HOURS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def hourFromDatetime(date_time):
    return date_time.replace(minute=0, second=0, microsecond=0)

def hourFromString(time_str):
    date, hour = time_str.split(':')
    year, month, day = [int(n) for n in date.split('-')]
    return datetime.datetime(year, month, day, int(hour))

def asHourObject(hour):
    if isinstance(hour, datetime.datetime):
        return hourFromDatetime(hour)
    elif isinstance(hour, basestring):
        return hourFromString(hour)
    elif isinstance(hour, tuple):
        return datetime.datetime(*hour[:4])
    else:
        raise TypeError, ARG_TYPE_ERROR % (str(type(hour)), 'hour')

def asHourInTimezone(hour, timezone):
    hour_obj = asHourObject(hour)
    if isValidTimezoneObj(hour_obj.tzinfo):
        if isValidTimezoneObj(timezone):
            return hour_obj.astimezone(timezone)
        elif isinstance(timezone, basestring):
            return hour_obj.astimezone(pytz.timezone(timezone))
    else:
        if isValidTimezoneObj(timezone):
            return timezone.localize(hour_obj)
        elif isinstance(timezone, basestring):
            return pytz.timezone(timezone).localize(hour_obj)

    raise TypeError, ARG_TYPE_ERROR % (str(type(timezone)),'timesone')

def hourAsString(hour, include_timezone=False):
    hour_str = hour.strftime(HOUR_STRING_FORMAT)
    if include_timezone:
        if isValidTimezoneObj(hour.tzinfo):
            hour_str = '%s|%s' % (hour_str, str(hour.tzinfo))
            hour_repr = repr(hour)
            if 'STD' in hour_repr: return '%s:STD' % hour_str
            elif 'DST' in hour_repr: return '%s:DST' % hour_str
        else:
            errmsg = '"hour" argument does not contain a valid timzone.'
            raise ValueError, errmsg
    return hour_str

def isValidHourString(hour_str, include_timezone=False):
    if include_timezone:
        parts = hour_str.split(':')
        if len(parts) != 3: return False
        date = parts[0]
        hour = parts[1]
        #TODO: test vor valid timezone in parts[2]
    else:
        if len(time_str) != len(VALID_TIME_STRING): return False
        parts = hour_str.split(':')
        if len(parts) != 2: return False
        date = parts[0]
        hour = parts[1]

    if len(date) != len(VALID_DATE_STRING) \
    or len(hour) != len(VALID_HOUR_STRING): return False
    try:
        year, month, day = date.split('-')
    except:
        return False
    return 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 \
           and 1 <= int(day) <= 31 and 0 <= int(hour) <= 23

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# FUNCTIONS THAT OPERATE ON TIMEZONE-AWARE datetime.datetime objects
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def tzaDateString(tza_time): return tza_time.strftime('%Y%m%d')
def tzaTimeString(tza_time): return tza_time.strftime('%Y%m%d%H')
def tzaTimeStrings(tza_time, prefix='tza'):
    return { '%s_date' % prefix : tza_time.strftime('%Y%m%d'),
             '%s_hour' % prefix : tza_time.strftime('%H'), 
             '%s_time' % prefix : tza_time.strftime('%Y%m%d%H') }
timeStrings = tzaTimeStrings

def timeDifferenceInHours(time1, time2):
    # returns time difference in hours
    if (time1 > time2):
        time_diff = time1 - time2
    else: time_diff = time2 - time1
    days = time_diff.days 
    num_hours = (time_diff.days * 24)
    seconds = time_diff.seconds
    # if seconds < 3600, then we have whole days
    if seconds < 3600: return num_hours
    # 3600 seconds / hour ... integer math ignores remainder
    return num_hours + (seconds / 3600)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# LOCAL TIME ZONE FUNCTIONS FOR
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def asLocalTime(date_time, local_timezone=None):
    if local_timezone is None: local_zone = tzlocal.get_localzone()
    else: local_zone = asTimezoneObj(local_timezone)
    if isinstance(date_time.tzinfo, pytz.tzinfo.BaseTzInfo) \
    or type(date_time.tzinfo) == type(pytz.UTC):
        return date_time.astimezone(local_zone)
    return local_zone.localize(date_time)

def asLocalHour(date_time, local_timezone=None):
    return hourFromDatetime(asLocalTime(date_time, local_timezone))

def localHour():
    return hourFromDatetime(asLocalTime(datetime.datetime.now()))

def localTime():
    return asLocalTime(datetime.datetime.now())


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# UTC TIME ZONE FUNCTIONS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def asUtcTime(date_time, local_timezone=None):
    if type(date_time.tzinfo) == type(pytz.UTC): return date_time
    utc = pytz.timezone('UTC')
    if isinstance(date_time.tzinfo, pytz.tzinfo.BaseTzInfo):
        return date_time.astimezone(utc)
    elif local_timezone is None:
        return tzlocal.get_localzone().localize(date_time).astimezone(utc)
    else: 
        local_time = asTimezoneObj(local_timezone).localize(date_time)
        return local_time.astimezone(utc)

def asUtcHour(hour, local_timezone=None):
    return hourFromDatetime(asUtcTime(hour, local_timezone))

def utcHour():
    now = datetime.datetime.now()
    utc_now = tzlocal.get_localzone().localize(now).astimezone(pytz.UTC)
    return hourFromDatetime(utc_now)

def utcTime():
    now = datetime.datetime.now()
    return tzlocal.get_localzone().localize(now).astimezone(pytz.UTC)

def utcTimeStrings(datetime_hour):
    if type(datetime_hour.tzinfo) == type(pytz.UTC):
        return { 'utc_date': datetime_hour.strftime('%Y%m%d'),
                 'utc_hour': datetime_hour.strftime('%H'), 
                 'utc_time': datetime_hour.strftime('%Y%m%d%H') }

    elif isinstance(datetime_hour.tzinfo, pytz.tzinfo.BaseTzInfo):
        utc_time = datetime_hour.astimezone(pytz.UTC)
    else:
        timezone = tzlocal.get_localzone()
        utc_time = timezone.localize(datetime_hour).astimezone(pytz.UTC)

    return { 'utc_date': utc_time.strftime('%Y%m%d'),
             'utc_hour': utc_time.strftime('%H'), 
             'utc_time': utc_time.strftime('%Y%m%d%H') }

