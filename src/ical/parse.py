import datetime
import json
import tempfile

import dateutil.rrule as rrule
import icalendar
import pytz
import requests

from config.settings import get_cache


calendar_url = 'https://www.google.com/calendar/ical/mozilla.com_lr5jsh38i6dmr72uu4d1nv7dcc%40group.calendar.google.com/public/basic.ics'
calendar_file = get_cache('ical.ics')


def get_calendar():
    get = requests.get(calendar_url)
    with open(calendar_file, 'wb') as cal_file:
        cal_file.write(get.content)


def next_push():
    with open(calendar_file, 'rb') as cal_file:
        cal = icalendar.Calendar.from_ical(cal_file.read())
        nowish = datetime.datetime.now() - datetime.timedelta(hours=-3)
        nowish = nowish.replace(tzinfo=pytz.UTC)

        date = None
        for ev in cal.walk():
            if ev.name == 'VEVENT' and 'push' in ev.get('summary').lower():
                date = ev.get('dtstart').dt
                if ev.get('rrule'):
                    rule = rrule.rrulestr(
                        ev.get('rrule').to_ical(),
                        dtstart=ev.get('dtstart').dt
                    )
                    date = rule.after(nowish)

                if date > nowish:
                    return date
