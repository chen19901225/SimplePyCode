import datetime
import json

__author__ = 'Administrator'
import simplejson

def safe_new_datetime(d):
    kw=[d.year,d.month,d.day]
    if isinstance(d,datetime.datetime):
        kw.extend([d.hour,d.minute,d.second,d.microsecond])
    return datetime.datetime(*kw)
def safe_new_date(d):
    return datetime.date(d.year,d.month,d.day)


class DatetimeJsonEncoder(json.JSONEncoder):
    DATE_FORMAT="%Y-%m-%d"
    TIME_FORMAT="%H:%M:%S"

    def default(self,o):
        if isinstance(o,datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o,datetime.date):
            return o.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self,o)