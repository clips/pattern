import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.db  import date, time, NOW
from pattern.web import Bing, NEWS

# It is often useful to keep a date stamp for each row in the table.
# The pattern.db module's date() function can be used for this.
# It is a simple wrapper around Python's datetime.datetime class,
# with extra functionality to make it easy to parse or print it as a string.

print(date(NOW))
print(date())
print(date("2010-11-01 16:30", "%Y-%m-%d %H:%M"))
print(date("Nov 1, 2010", "%b %d, %Y"))
print(date("Nov 1, 2010", "%b %d, %Y", format="%d/%m/%Y"))
print("")

# All possible formatting options:
# http://docs.python.org/library/time.html#time.strftime

for r in Bing(license=None, language="en").search("today", type=NEWS):
    print(r.title)
    print(repr(r.date))  # Result.date is a string (e.g. we can't > <= += with the date).
    print(date(r.date))  # date() can parse any Result.date in the web module.
    print("")

d  = date("4 november 2011")
d += time(days=2, hours=5)
print(d)
