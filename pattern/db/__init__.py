#### PATTERN | DB ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int, chr
from builtins import map, zip, filter
from builtins import object, range, next

import os
import sys
import inspect
import warnings
import re
import urllib
import base64
import json

if sys.version > "3":
    import csv as csvlib
else:
    from backports import csv as csvlib

from codecs import BOM_UTF8
from itertools import islice
from datetime import datetime, timedelta
from calendar import monthrange
from time import mktime, strftime
from math import sqrt
from types import GeneratorType

from functools import cmp_to_key

from io import open, StringIO, BytesIO

BOM_UTF8 = BOM_UTF8.decode("utf-8")

from html.entities import name2codepoint

from email.utils import parsedate_tz, mktime_tz

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

from pattern.helpers import encode_string, decode_string

decode_utf8 = decode_string
encode_utf8 = encode_string

MYSQL = "mysql"
SQLITE = "sqlite"


def _import_db(engine=SQLITE):
    """ Lazy import called from Database() or Database.new().
        Depending on the type of database we either import MySQLdb or SQLite.
        Note: 64-bit Python needs 64-bit MySQL, 32-bit the 32-bit version.
    """
    global MySQLdb
    global sqlite
    if engine == MYSQL:
        import MySQLdb
        warnings.simplefilter("ignore", MySQLdb.Warning)
    if engine == SQLITE:
        import sqlite3.dbapi2 as sqlite


def pd(*args):
    """ Returns the path to the parent directory of the script that calls pd() + given relative path.
        For example, in this script: pd("..") => /usr/local/lib/python2.x/site-packages/pattern/db/..
    """
    f = inspect.currentframe()
    f = inspect.getouterframes(f)[1][1]
    f = f != "<stdin>" and f or os.getcwd()
    return os.path.join(os.path.dirname(os.path.realpath(f)), *args)

_sum = sum # pattern.db.sum() is also a column aggregate function.

#### DATE FUNCTIONS ################################################################################

NOW, YEAR = "now", datetime.now().year

# Date formats can be found in the Python documentation:
# http://docs.python.org/library/time.html#time.strftime
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_formats = [
    DEFAULT_DATE_FORMAT,           # 2010-09-21 09:27:01  => SQLite + MySQL
    "%Y-%m-%dT%H:%M:%SZ",          # 2010-09-20T09:27:01Z => Bing
    "%a, %d %b %Y %H:%M:%S +0000", # Fri, 21 Sep 2010 09:27:01 +000 => Twitter
    "%a %b %d %H:%M:%S +0000 %Y",  # Fri Sep 21 09:21:01 +0000 2010 => Twitter
    "%Y-%m-%dT%H:%M:%S+0000",      # 2010-09-20T09:27:01+0000 => Facebook
    "%Y-%m-%d %H:%M",              # 2010-09-21 09:27
    "%Y-%m-%d",                    # 2010-09-21
    "%d/%m/%Y",                    # 21/09/2010
    "%d %B %Y",                    # 21 September 2010
    "%d %b %Y",                    # 21 Sep 2010
    "%B %d %Y",                    # September 21 2010
    "%B %d, %Y",                   # September 21, 2010
]


def _yyyywwd2yyyymmdd(year, week, weekday):
    """ Returns (year, month, day) for given (year, week, weekday).
    """
    d = datetime(year, month=1, day=4) # 1st week contains January 4th.
    d = d - timedelta(d.isoweekday() - 1) + timedelta(days=weekday - 1, weeks=week - 1)
    return (d.year, d.month, d.day)


def _strftime1900(d, format):
    """ Returns the given date formatted as a string.
    """
    if d.year < 1900: # Python's strftime() doesn't handle year < 1900.
        return strftime(format, (1900,) + d.timetuple()[1:]).replace("1900", str(d.year), 1)
    return datetime.strftime(d, format)


class DateError(Exception):
    pass


class Date(datetime):
    """ A convenience wrapper for datetime.datetime with a default string format.
    """
    format = DEFAULT_DATE_FORMAT
    # Date.year
    # Date.month
    # Date.day
    # Date.minute
    # Date.second

    @property
    def minutes(self):
        return self.minute

    @property
    def seconds(self):
        return self.second

    @property
    def microseconds(self):
        return self.microsecond

    @property
    def week(self):
        return self.isocalendar()[1]

    @property
    def weekday(self):
        return self.isocalendar()[2]

    @property
    def timestamp(self):

        # In Python 3, years before 1900 are accepted whilee mktime() raises ValueError in Python 2. Let's stick to this.
        if self.timetuple().tm_year < 1900:
            raise ValueError("year out of range")

        return int(mktime(self.timetuple())) # Seconds elapsed since 1/1/1970.

    def strftime(self, format):
        return _strftime1900(self, format)

    def copy(self):
        return date(self.timestamp)

    def __str__(self):
        return self.strftime(self.format)

    def __repr__(self):
        return "Date(%s)" % repr(self.__str__())

    def __iadd__(self, t):
        return self.__add__(t)

    def __isub__(self, t):
        return self.__sub__(t)

    def __add__(self, t):
        d = self
        if getattr(t, "years", 0) \
        or getattr(t, "months", 0):
            # January 31 + 1 month = February 28.
            y = (d.month + t.months - 1) // 12 + d.year + t.years
            m = (d.month + t.months + 0) % 12 or 12
            r = monthrange(y, m)
            d = date(y, m, min(d.day, r[1]), d.hour, d.minute, d.second, d.microsecond)
        d = datetime.__add__(d, t)
        return date(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, self.format)

    def __sub__(self, t):
        if isinstance(t, (Date, datetime)):
            # Subtracting two dates returns a Time.
            t = datetime.__sub__(self, t)
            return Time(+t.days, +t.seconds,
                microseconds = +t.microseconds)
        if isinstance(t, (Time, timedelta)):
            return self + Time(-t.days, -t.seconds,
                microseconds = -t.microseconds,
                      months = -getattr(t, "months", 0),
                       years = -getattr(t, "years", 0))


def date(*args, **kwargs):
    """ Returns a Date from the given parameters:
        - date(format=Date.format) => now
        - date(int)
        - date(string)
        - date(string, format=Date.format)
        - date(string, inputformat, format=Date.format)
        - date(year, month, day, format=Date.format)
        - date(year, month, day, hours, minutes, seconds, format=Date.format)
        If a string is given without an explicit input format, all known formats will be tried.
    """
    d = None
    f = None
    if len(args) == 0 \
    and kwargs.get("year") is not None \
    and kwargs.get("month") \
    and kwargs.get("day"):
        # Year, month, day.
        d = Date(**kwargs)
    elif kwargs.get("week"):
        # Year, week, weekday.
        f = kwargs.pop("format", None)
        d = Date(*_yyyywwd2yyyymmdd(
            kwargs.pop("year", args and args[0] or Date.now().year),
            kwargs.pop("week"),
            kwargs.pop("weekday", kwargs.pop("day", 1))), **kwargs)
    elif len(args) == 0 or args[0] == NOW:
        # No parameters or one parameter NOW.
        d = Date.now()
    elif len(args) == 1 \
     and isinstance(args[0], (Date, datetime)):
        # One parameter, a Date or datetime object.
        d = Date.fromtimestamp(int(mktime(args[0].timetuple())))
        d += time(microseconds=args[0].microsecond)
    elif len(args) == 1 \
     and (isinstance(args[0], int) \
      or isinstance(args[0], (str, bytes)) and args[0].isdigit()):
        # One parameter, an int or string timestamp.
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"),)
        d = Date.fromtimestamp(int(args[0]))
    elif len(args) == 1 \
     and isinstance(args[0], (str, bytes)):
        # One parameter, a date string for which we guess the input format (RFC2822 or known formats).
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"),)
        try:
            d = Date.fromtimestamp(mktime_tz(parsedate_tz(args[0])))
        except:
            for format in ("format" in kwargs and [kwargs["format"]] or []) + date_formats:
                try:
                    d = Date.strptime(args[0], format)
                    break
                except:
                    pass
        if d is None:
            raise DateError("unknown date format for %s" % repr(args[0]))
    elif len(args) == 2 \
     and isinstance(args[0], (str, bytes)):
        # Two parameters, a date string and an explicit input format.
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"), args[1].decode("utf-8"))
        d = Date.strptime(args[0], args[1])
    elif len(args) >= 3:
        # 3-6 parameters: year, month, day, hours, minutes, seconds.
        f = kwargs.pop("format", None)
        d = Date(*args[:7], **kwargs)
    else:
        raise DateError("unknown date format")
    d.format = kwargs.get("format") or len(args) > 7 and args[7] or f or Date.format
    return d


class Time(timedelta):

    def __new__(cls, *args, **kwargs):
        """ A convenience wrapper for datetime.timedelta that handles months and years.
        """
        # Time.years
        # Time.months
        # Time.days
        # Time.seconds
        # Time.microseconds
        y = kwargs.pop("years", 0)
        m = kwargs.pop("months", 0)
        t = timedelta.__new__(cls, *args, **kwargs)
        setattr(t, "years", y)
        setattr(t, "months", m)
        return t


def time(days=0, seconds=0, minutes=0, hours=0, **kwargs):
    """ Returns a Time that can be added to a Date object.
        Other parameters: microseconds, milliseconds, weeks, months, years.
    """
    return Time(days=days, seconds=seconds, minutes=minutes, hours=hours, **kwargs)


def string(value, default=""):
    """ Returns the value cast to unicode, or default if it is None/empty.
    """
    # Useful for HTML interfaces.
    if value is None or value == "": # Don't do value != None because this includes 0.
        return default
    return decode_utf8(value)


class EncryptionError(Exception):
    pass


class DecryptionError(Exception):
    pass


def encrypt_string(s, key=""):
    """ Returns the given string as an encrypted bytestring.
    """
    key += " "
    a = []
    for i in range(len(s)):
        try:
            a.append(chr(ord(s[i]) + ord(key[i % len(key)]) % 256).encode("latin-1"))
        except:
            raise EncryptionError()
    s = b"".join(a)
    s = base64.urlsafe_b64encode(s)
    return s


def decrypt_string(s, key=""):
    """ Returns the given string as a decrypted Unicode string.
    """
    key += " "
    s = base64.urlsafe_b64decode(s)
    s = s.decode("latin-1")
    a = []
    for i in range(len(s)):
        try:
            a.append(chr(ord(s[i]) - ord(key[i % len(key)]) % 256))
        except:
            raise DecryptionError()
    s = "".join(a)
    s = decode_utf8(s)
    return s

RE_AMPERSAND = re.compile("\&(?!\#)")           # & not followed by #
RE_UNICODE = re.compile(r'&(#?)(x|X?)(\w+);') # &#201;


def encode_entities(string):
    """ Encodes HTML entities in the given string ("<" => "&lt;").
        For example, to display "<em>hello</em>" in a browser,
        we need to pass "&lt;em&gt;hello&lt;/em&gt;" (otherwise "hello" in italic is displayed).
    """
    if isinstance(string, str):
        string = RE_AMPERSAND.sub("&amp;", string)
        string = string.replace("<", "&lt;")
        string = string.replace(">", "&gt;")
        string = string.replace('"', "&quot;")
        string = string.replace("'", "&#39;")
    return string


def decode_entities(string):
    """ Decodes HTML entities in the given string ("&lt;" => "<").
    """
    # http://snippets.dzone.com/posts/show/4569
    def replace_entity(match):
        hash, hex, name = match.group(1), match.group(2), match.group(3)
        if hash == "#" or name.isdigit():
            if hex == '':
                return chr(int(name))              # "&#38;" => "&"
            if hex in ("x", "X"):
                return chr(int('0x' + name, 16))   # "&#x0026;" = > "&"
        else:
            cp = name2codepoint.get(name)          # "&amp;" => "&"
            return cp and chr(cp) or match.group() # "&foo;" => "&foo;"
    if isinstance(string, str):
        return RE_UNICODE.subn(replace_entity, string)[0]
    return string


class _Binary(object):
    """ A wrapper for BLOB data with engine-specific encoding.
        See also: Database.binary().
    """

    def __init__(self, data, type=SQLITE):
        self.data, self.type = str(hasattr(data, "read") and data.read() or data), type

    def escape(self):
        if self.type == SQLITE:
            return str(self.data.encode("string-escape")).replace("'", "''")
        if self.type == MYSQL:
            return MySQLdb.escape_string(self.data)


def _escape(value, quote=lambda string: "'%s'" % string.replace("'", "\\'")):
    """ Returns the quoted, escaped string (e.g., "'a bird\'s feathers'") for database entry.
        Anything that is not a string (e.g., an integer) is converted to string.
        Booleans are converted to "0" and "1", None is converted to "null".
        See also: Database.escape()
    """
    # Note: use Database.escape() for MySQL/SQLITE-specific escape.
    if value in ("current_timestamp",):
        # Don't quote constants such as current_timestamp.
        return value
    if isinstance(value, str):
        # Strings are quoted, single quotes are escaped according to the database engine.
        return quote(value)
    if isinstance(value, bool):
        # Booleans are converted to "0" or "1".
        return str(int(value))
    if isinstance(value, (int, float)):
        # Numbers are converted to string.
        return str(value)
    if isinstance(value, datetime):
        # Dates are formatted as string.
        return quote(value.strftime(DEFAULT_DATE_FORMAT))
    if isinstance(value, type(None)):
        # None is converted to NULL.
        return "null"
    if isinstance(value, Query):
        # A Query is converted to "("+Query.SQL()+")" (=subquery).
        return "(%s)" % value.SQL().rstrip(";")
    if isinstance(value, _Binary):
        # Binary data is escaped with attention to null bytes.
        return "'%s'" % value.escape()
    return value


def cast(x, f, default=None):
    """ Returns f(x) or default.
    """
    if f is str and isinstance(x, str):
        return decode_utf8(x)
    if f is bool and x in ("1", "True", "true"):
        return True
    if f is bool and x in ("0", "False", "false"):
        return False
    if f is int:
        f = lambda x: int(round(float(x)))
    try:
        return f(x)
    except:
        return default

#### LIST FUNCTIONS ################################################################################


def find(match=lambda item: False, list=[]):
    """ Returns the first item in the list for which match(item) is True.
    """
    for item in list:
        if match(item) is True:
            return item


def order(list, cmp=None, key=None, reverse=False):
    """ Returns a list of indices in the order as when the given list is sorted.
        For example: ["c","a","b"] => [1, 2, 0]
        This means that in the sorted list, "a" (index 1) comes first and "c" (index 0) last.
    """
    if cmp and key:
        f = lambda i, j: cmp(key(list[i]), key(list[j]))
    elif cmp:
        f = lambda i, j: cmp(list[i], list[j])
    elif key:
        f = lambda i, j: int(key(list[i]) >= key(list[j])) * 2 - 1
    else:
        f = lambda i, j: int(list[i] >= list[j]) * 2 - 1
    return sorted(range(len(list)), key=cmp_to_key(f), reverse=reverse)

_order = order


def avg(list):
    """ Returns the arithmetic mean of the given list of values.
        For example: mean([1,2,3,4]) = 10/4 = 2.5.
    """
    return float(_sum(list)) / (len(list) or 1)


def variance(list):
    """ Returns the variance of the given list of values.
        The variance is the average of squared deviations from the mean.
    """
    a = avg(list)
    return _sum([(x - a)**2 for x in list]) / (len(list) - 1 or 1)


def stdev(list):
    """ Returns the standard deviation of the given list of values.
        Low standard deviation => values are close to the mean.
        High standard deviation => values are spread out over a large range.
    """
    return sqrt(variance(list))

#### SQLITE FUNCTIONS ##############################################################################
# Convenient MySQL functions not in in pysqlite2. These are created at each Database.connect().


class sqlite_first(list):
    def step(self, value): self.append(value)

    def finalize(self):
        return self[0]


class sqlite_last(list):
    def step(self, value): self.append(value)

    def finalize(self):
        return self[-1]


class sqlite_group_concat(list):
    def step(self, value): self.append(value)

    def finalize(self):
        return ",".join(string(v) for v in self if v is not None)

# SQLite (and MySQL) date string format:
# yyyy-mm-dd hh:mm:ss


def sqlite_year(datestring):
    return int(datestring.split(" ")[0].split("-")[0])


def sqlite_month(datestring):
    return int(datestring.split(" ")[0].split("-")[1])


def sqlite_day(datestring):
    return int(datestring.split(" ")[0].split("-")[2])


def sqlite_hour(datestring):
    return int(datestring.split(" ")[1].split(":")[0])


def sqlite_minute(datestring):
    return int(datestring.split(" ")[1].split(":")[1])


def sqlite_second(datestring):
    return int(datestring.split(" ")[1].split(":")[2])

#### DATABASE ######################################################################################


class DatabaseConnectionError(Exception):
    pass


class Database(object):

    class Tables(dict):
        # Table objects are lazily constructed when retrieved.
        # This saves time because each table executes a metadata query when constructed.
        def __init__(self, db, *args, **kwargs):
            dict.__init__(self, *args, **kwargs)
            self.db = db

        def __getitem__(self, k):
            if dict.__getitem__(self, k) is None:
                dict.__setitem__(self, k, Table(name=k, database=self.db))
            return dict.__getitem__(self, k)

    def __init__(self, name, host="localhost", port=3306, username="root", password="", type=SQLITE, unicode=True, **kwargs):
        """ A collection of tables stored in an SQLite or MySQL database.
            If the database does not exist, creates it.
            If the host, user or password is wrong, raises DatabaseConnectionError.
        """
        _import_db(type)
        self.type = type
        self.name = name
        self.host = host
        self.port = port
        self.username = kwargs.get("user", username)
        self.password = password
        self._connection = None
        self.connect(unicode)
        # Table names are available in the Database.tables dictionary,
        # table objects as attributes (e.g. Database.table_name).
        q = self.type == SQLITE and "select name from sqlite_master where type='table';" or "show tables;"
        self.tables = Database.Tables(self)
        for name, in self.execute(q):
            if not name.startswith(("sqlite_",)):
                self.tables[name] = None
        # The SQL syntax of the last query is kept in cache.
        self._query = None
        # Persistent relations between tables, stored as (table1, table2, key1, key2, join) tuples.
        self.relations = []

    def connect(self, unicode=True):
        # Connections for threaded applications work differently,
        # see http://tools.cherrypy.org/wiki/Databases
        # (have one Database object for each thread).
        if self._connection is not None:
            return
        # MySQL
        if self.type == MYSQL:
            try:
                self._connection = MySQLdb.connect(self.host, self.username, self.password, self.name, port=self.port, use_unicode=unicode)
                self._connection.autocommit(False)
            except Exception as e:
                # Create the database if it doesn't exist yet.
                if "unknown database" not in str(e).lower():
                    raise DatabaseConnectionError(e[1]) # Wrong host, username and/or password.
                connection = MySQLdb.connect(self.host, self.username, self.password)
                cursor = connection.cursor()
                cursor.execute("create database if not exists `%s`;" % self.name)
                cursor.close()
                connection.close()
                self._connection = MySQLdb.connect(self.host, self.username, self.password, self.name, port=self.port, use_unicode=unicode)
                self._connection.autocommit(False)
            if unicode:
                self._connection.set_character_set("utf8")
        # SQLite
        if self.type == SQLITE:
            self._connection = sqlite.connect(self.name, detect_types=sqlite.PARSE_DECLTYPES)
            # Create functions that are not natively supported by the engine.
            # Aggregate functions (for grouping rows) + date functions.
            self._connection.create_aggregate("first", 1, sqlite_first)
            self._connection.create_aggregate("last", 1, sqlite_last)
            self._connection.create_aggregate("group_concat", 1, sqlite_group_concat)
            self._connection.create_function("year", 1, sqlite_year)
            self._connection.create_function("month", 1, sqlite_month)
            self._connection.create_function("day", 1, sqlite_day)
            self._connection.create_function("hour", 1, sqlite_hour)
            self._connection.create_function("minute", 1, sqlite_minute)
            self._connection.create_function("second", 1, sqlite_second)
        # Map field type INTEGER to int (not long(), e.g., 1L).
        # Map field type BOOLEAN to bool.
        # Map field type DATE to str, yyyy-mm-dd hh:mm:ss.
        if self.type == MYSQL:
            type = MySQLdb.constants.FIELD_TYPE
            self._connection.converter[type.LONG]       = int
            self._connection.converter[type.LONGLONG]   = int
            self._connection.converter[type.DECIMAL]    = float
            self._connection.converter[type.NEWDECIMAL] = float
            self._connection.converter[type.TINY]       = bool
            self._connection.converter[type.TIMESTAMP]  = date
        if self.type == SQLITE:
            sqlite.converters["TINYINT(1)"] = lambda v: bool(int(v))
            sqlite.converters["BLOB"]       = lambda v: str(v).decode("string-escape")
            sqlite.converters["TIMESTAMP"]  = date

    def disconnect(self):
        if self._connection is not None:
            self._connection.commit()
            self._connection.close()
            self._connection = None

    @property
    def connection(self):
        return self._connection

    @property
    def connected(self):
        return self._connection is not None

    def __getattr__(self, k):
        """ Tables are available as attributes by name, e.g., Database.persons.
        """
        if k in self.__dict__["tables"]:
            return self.__dict__["tables"][k]
        if k in self.__dict__:
            return self.__dict__[k]
        raise AttributeError("'Database' object has no attribute '%s'" % k)

    def __len__(self):
        return len(self.tables)

    def __iter__(self):
        return iter(self.tables.keys())

    def __getitem__(self, table):
        return self.tables[table]

    def __setitem__(self, table, fields):
        self.create(table, fields)

    def __delitem__(self, table):
        self.drop(table)

    def __nonzero__(self):
        return True

    # Backwards compatibility.
    def _get_user(self):
        return self.username

    def _set_user(self, v):
        self.username = v
    user = property(_get_user, _set_user)

    @property
    def query(self):
        """ Yields the last executed SQL query as a string.
        """
        return self._query

    def execute(self, SQL, commit=False):
        """ Executes the given SQL query and return an iterator over the rows.
            With commit=True, automatically commits insert/update/delete changes.
        """
        self._query = SQL
        if not SQL:
            return # MySQL doesn't like empty queries.
        #print(SQL)
        cursor = self._connection.cursor()
        cursor.execute(SQL)
        if commit is not False:
            self._connection.commit()
        return self.RowsIterator(cursor)

    class RowsIterator(object):
        """ Iterator over the rows returned from Database.execute().
        """

        def __init__(self, cursor):
            self._cursor = cursor
            self._iter = iter(self._cursor.fetchall())

        def __next__(self):
            return next(self._iter)

        def __iter__(self):
            return self

        def __del__(self):
            self._cursor.close()

    def commit(self):
        """ Commit all pending insert/update/delete changes.
        """
        self._connection.commit()

    def rollback(self):
        """ Discard changes since the last commit.
        """
        self._connection.rollback()

    def escape(self, value):
        """ Returns the quoted, escaped string (e.g., "'a bird\'s feathers'") for database entry.
            Anything that is not a string (e.g., an integer) is converted to string.
            Booleans are converted to "0" and "1", None is converted to "null".
        """
        def quote(string):
            # How to escape strings differs between database engines.
            if self.type == MYSQL:
                #return "'%s'" % self._connection.escape_string(string) # Doesn't like Unicode.
                return "'%s'" % string.replace("'", "\\'")
            if self.type == SQLITE:
                return "'%s'" % string.replace("'", "''")
        return _escape(value, quote)

    def binary(self, data):
        """ Returns the string of binary data as a value that can be inserted in a BLOB field.
        """
        return _Binary(data, self.type)

    blob = binary

    def _field_SQL(self, table, field):
        # Returns a (field, index)-tuple with SQL strings for the given field().
        # The field string can be used in a CREATE TABLE or ALTER TABLE statement.
        # The index string is an optional CREATE INDEX statement (or None).
        auto = " auto%sincrement" % (self.type == MYSQL and "_" or "")
        field = isinstance(field, str) and [field, STRING(255)] or field
        field = list(field) + [STRING, None, False, True][len(field) - 1:]
        field = list(_field(field[0], field[1], default=field[2], index=field[3], optional=field[4]))
        if field[1] == "timestamp" and field[2] == "now":
            field[2] = "current_timestamp"
        a = b = None
        a = "`%s` %s%s%s%s" % (
            # '`id` integer not null primary key auto_increment'
            field[0],
            field[1] == STRING and field[1]() or field[1],
            field[4] is False and " not null" or " null",
            field[2] is not None and " default %s" % self.escape(field[2]) or "",
            field[3] == PRIMARY and " primary key%s" % ("", auto)[field[1] == INTEGER] or "")
        if field[3] in (UNIQUE, True):
            b = "create %sindex `%s_%s` on `%s` (`%s`);" % (
                field[3] == UNIQUE and "unique " or "", table, field[0], table, field[0])
        return a, b

    def create(self, table, fields=[], encoding="utf-8", **kwargs):
        """ Creates a new table with the given fields.
            The given list of fields must contain values returned from the field() function.
        """
        if table in self.tables:
            raise TableError("table '%s' already exists" % (self.name + "." + table))
        if table.startswith(XML_HEADER):
            # From an XML-string generated with Table.xml.
            return parse_xml(self, table,
                    table = kwargs.get("name"),
                    field = kwargs.get("field", lambda s: s.replace(".", "_")))
        encoding = self.type == MYSQL and " default charset=" + encoding.replace("utf-8", "utf8") or ""
        fields, indices = list(zip(*[self._field_SQL(table, f) for f in fields]))
        self.execute("create table `%s` (%s)%s;" % (table, ", ".join(fields), encoding))
        for index in indices:
            if index is not None:
                self.execute(index, commit=True)
        self.tables[table] = None # lazy loading
        return self.tables[table]

    def drop(self, table):
        """ Removes the table with the given name.
        """
        if isinstance(table, Table) and table.db == self:
            table = table.name
        if table in self.tables:
            self.tables[table].database = None
            self.tables.pop(table)
            self.execute("drop table `%s`;" % table, commit=True)

    remove = drop

    def link(self, table1, field1, table2, field2, join="left"):
        """ Defines a relation between two tables in the database.
            When executing a table query, fields from the linked table will also be available
            (to disambiguate between field names, use table.field_name).
        """
        if isinstance(table1, Table):
            table1 = table1.name
        if isinstance(table2, Table):
            table2 = table2.name
        self.relations.append((table1, field1, table2, field2, join))

    def __repr__(self):
        return "Database(name=%s, host=%s, tables=%s)" % (
            repr(self.name),
            repr(self.host),
            repr(self.tables.keys()))

    def _delete(self):
        # No warning is issued, seems a bad idea to document the method.
        # Anyone wanting to delete an entire database should use an editor.
        if self.type == MYSQL:
            self.execute("drop database `%s`" % self.name, commit=True)
            self.disconnect()
        if self.type == SQLITE:
            self.disconnect()
            os.unlink(self.name)

    def __delete__(self):
        try:
            self.disconnect()
        except:
            pass

#### FIELD #########################################################################################


class _String(str):
    # The STRING constant can be called with a length when passed to field(),
    # for example field("language", type=STRING(2), default="en", index=True).
    def __new__(self):
        return str.__new__(self, "string")

    def __call__(self, length=100):
        return "varchar(%s)" % (length > 255 and 255 or (length < 1 and 1 or length))

# Field type.
# Note: SQLite string fields do not impose a string limit.
# Unicode strings have more characters than actually displayed (e.g. "&#9829;").
# Boolean fields are stored as tinyint(1), int 0 or 1.
STRING, INTEGER, FLOAT, TEXT, BLOB, BOOLEAN, DATE = \
    _String(), "integer", "float", "text", "blob", "boolean", "date"

STR, INT, BOOL = STRING, INTEGER, BOOLEAN

# Field index.
PRIMARY = "primary"
UNIQUE = "unique"

# DATE default.
NOW = "now"

#--- FIELD- ----------------------------------------------------------------------------------------

#def field(name, type=STRING, default=None, index=False, optional=True)


def field(name, type=STRING, **kwargs):
    """ Returns a table field definition that can be passed to Database.create().
        The column can be indexed by setting index to True, PRIMARY or UNIQUE.
        Primary key number columns are always auto-incremented.
    """
    default, index, optional = (
        kwargs.get("default", type == DATE and NOW or None),
        kwargs.get("index", False),
        kwargs.get("optional", True)
    )
    if type == STRING:
        type = STRING()
    if type == FLOAT:
        type = "real"
    if type == BOOLEAN:
        type = "tinyint(1)"
    if type == DATE:
        type = "timestamp"
    if str(index) in "01":
        index = bool(int(index))
    if str(optional) in "01":
        optional = bool(int(optional))
    return (name, type, default, index, optional)

_field = field


def primary_key(name="id"):
    """ Returns an auto-incremented integer primary key field named "id".
    """
    return field(name, INTEGER, index=PRIMARY, optional=False)

pk = primary_key

#--- FIELD SCHEMA ----------------------------------------------------------------------------------


class Schema(object):

    def __init__(self, name, type, default=None, index=False, optional=True, extra=None):
        """ Field info returned from a "show columns from table"-query.
            Each table object has a Table.schema{} dictionary describing the fields' structure.
        """
        # Determine field type (NUMBER, STRING, TEXT, BLOB or DATE).
        type, length = type.lower(), None
        if type.startswith(("varchar", "char")):
            length = type.split("(")[-1].strip(")")
            length = int(length)
            type = STRING
        if type.startswith("int"):
            type = INTEGER
        if type.startswith(("real", "double")):
            type = FLOAT
        if type.startswith("time"):
            type = DATE
        if type.startswith("text"):
            type = TEXT
        if type.startswith("blob"):
            type = BLOB
        if type.startswith("tinyint(1)"):
            type = BOOLEAN
        # Determine index type (PRIMARY, UNIQUE, True or False).
        if isinstance(index, str):
            if index.lower().startswith("pri"):
                index = PRIMARY
            if index.lower().startswith("uni"):
                index = UNIQUE
            if index.lower() in ("0", "1", "", "yes", "mul"):
                index = index.lower() in ("1", "yes", "mul")
        # SQLite dumps the date string with quotes around it:
        if isinstance(default, str) and type == DATE:
            default = default.strip("'")
            default = default.replace("current_timestamp", NOW)
            default = default.replace("CURRENT_TIMESTAMP", NOW)
        if default is not None and type == INTEGER:
            default = int(default)
        if default is not None and type == FLOAT:
            default = float(default)
        if not default and default != 0:
            default = None
        self.name     = name                   # Field name.
        self.type     = type                   # Field type: INTEGER | FLOAT | STRING | TEXT | BLOB | DATE.
        self.length   = length                 # Field length for STRING.
        self.default  = default                # Default value.
        self.index    = index                  # PRIMARY | UNIQUE | True | False.
        self.optional = str(optional) in ("0", "True", "YES")
        self.extra    = extra or None

    def __repr__(self):
        return "Schema(name=%s, type=%s, default=%s, index=%s, optional=%s)" % (
            repr(self.name),
            repr(self.type),
            repr(self.default),
            repr(self.index),
            repr(self.optional))

#### TABLE #########################################################################################

ALL = "*"


class TableError(Exception):
    pass


class Table(object):

    class Fields(list):
        # Table.fields.append() alters the table.
        # New field() with optional=False must have a default value (can not be NOW).
        # New field() can have index=True, but not PRIMARY or UNIQUE.
        def __init__(self, table, *args, **kwargs):
            list.__init__(self, *args, **kwargs)
            self.table = table

        def append(self, field):
            name, (field, index) = field[0], self.table.db._field_SQL(self.table.name, field)
            self.table.db.execute("alter table `%s` add column %s;" % (self.table.name, field))
            self.table.db.execute(index, commit=True)
            self.table._update()

        def extend(self, fields):
            [self.append(f) for f in fields]

        def __setitem__(self, *args, **kwargs):
            raise NotImplementedError("Table.fields only supports append()")
        insert = remove = pop = __setitem__

    def __init__(self, name, database):
        """ A collection of rows consisting of one or more fields (i.e., table columns)
            of a certain type (i.e., strings, numbers).
        """
        self.database = database
        self._name = name
        self.fields = [] # List of field names (i.e., column names).
        self.schema = {} # Dictionary of (field, Schema)-items.
        self.default = {} # Default values for Table.insert().
        self.primary_key = None
        self._update()

    def _update(self):
        # Retrieve table column names.
        # Table column names are available in the Table.fields list.
        # Table column names should not contain unicode because they can also be function parameters.
        # Table column names should avoid " ", ".", "(" and ")".
        # The primary key column is stored in Table.primary_key.
        self.fields = Table.Fields(self)
        if self.name not in self.database.tables:
            raise TableError("table '%s' does not exist" % (self.database.name + "." + self.name))
        if self.db.type == MYSQL:
            q = "show columns from `%s`;" % self.name
        if self.db.type == SQLITE:
            q = "pragma table_info(`%s`);" % self.name
            i = self.db.execute("pragma index_list(`%s`)" % self.name) # look up indices
            i = dict(((v[1].replace(self.name + "_", "", 1), v[2]) for v in i))
        for f in self.db.execute(q):
            # [name, type, default, index, optional, extra]
            if self.db.type == MYSQL:
                f = [f[0], f[1], f[4], f[3], f[2], f[5]]
            if self.db.type == SQLITE:
                f = [f[1], f[2], f[4], f[5], f[3], ""]
                f[3] = f[3] == 1 and "pri" or (f[0] in i and ("1", "uni")[int(i[f[0]])] or "")
            list.append(self.fields, f[0])
            self.schema[f[0]] = Schema(*f)
            if self.schema[f[0]].index == PRIMARY:
                self.primary_key = f[0]

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        # Rename the table in the database and in any Database.relations.
        # SQLite and MySQL will automatically copy indices on the new table.
        self.db.execute("alter table `%s` rename to `%s`;" % (self._name, name))
        self.db.tables.pop(self._name)
        self.db.tables[name] = self
        for i, r in enumerate(self.db.relations):
            if r[0] == self._name:
                self.db.relations = (name, r[1], r[2], r[3])
            if r[2] == self.name:
                self.db.relations = (r[0], r[1], name, r[3])
        self._name = name

    name = property(_get_name, _set_name)

    @property
    def db(self):
        return self.database

    @property
    def pk(self):
        return self.primary_key

    def count(self):
        """ Yields the number of rows in the table.
        """
        return int(list(self.db.execute("select count(*) from `%s`;" % self.name))[0][0])

    def __len__(self):
        return self.count()

    def __iter__(self):
        return self.iterrows()

    def __getitem__(self, id):
        return self.filter(ALL, id=id)

    def __setitem__(self, id, row):
        self.delete(id)
        self.update(self.insert(row), {"id": id})

    def __delitem__(self, id):
        self.delete(id)

    def abs(self, field):
        """ Returns the absolute field name (e.g., "name" => ""persons.name").
        """
        return abs(self.name, field)

    def iterrows(self):
        """ Returns an iterator over the rows in the table.
        """
        return self.db.execute("select * from `%s`;" % self.name)

    def rows(self):
        """ Returns a list of all the rows in the table.
        """
        return list(self.iterrows())

    def record(self, row):
        """ Returns the given row as a dictionary of (field or alias, value)-items.
        """
        return dict(list(zip(self.fields, row)))

    class Rows(list):
        """ A list of results from Table.filter() with a Rows.table property.
            (i.e., like Query.table returned from Table.search()).
        """

        def __init__(self, table, data):
            list.__init__(self, data)
            self.table = table

        def record(self, row):
            return self.table.record(row) # See assoc().

    def filter(self, *args, **kwargs):
        """ Returns the rows that match the given constraints (using equals + AND):
        """
        # Table.filter(("name","age"), id=1)
        # Table.filter(ALL, type=("cat","dog")) => "cat" OR "dog"
        # Table.filter(ALL, type="cat", name="Taxi") => "cat" AND "Taxi"
        # Table.filter({"type":"cat", "name":"Taxi"})
        if len(args) == 0:
            # No parameters: default to ALL fields.
            fields = ALL
        elif len(args) == 1 and not isinstance(args[0], dict):
            # One parameter: field / list of fields + optional keyword filters.
            fields = args[0]
        elif len(args) == 1:
            # One parameter: dict of filters
            fields, kwargs = ALL, args[0]
        elif len(args) >= 2:
            # Two parameters: field(s) and dict of filters.
            fields, kwargs = args[0], args[1]
        fields = isinstance(fields, (list, tuple)) and ", ".join(fields) or fields or ALL
        q = " and ".join(cmp(k, v, "=", self.db.escape) for k, v in kwargs.items())
        q = q and " where %s" % q or ""
        q = "select %s from `%s`%s;" % (fields, self.name, q)
        return self.Rows(self, self.db.execute(q))

    def find(self, *args, **kwargs):
        return self.filter(*args, **kwargs)

    def search(self, *args, **kwargs):
        """ Returns a Query object that can be used to construct complex table queries.
        """
        return Query(self, *args, **kwargs)

    query = search

    def _insert_id(self):
        # Retrieves the primary key value of the last inserted row.
        if self.db.type == MYSQL:
            return list(self.db.execute("select last_insert_id();"))[0][0] or None
        if self.db.type == SQLITE:
            return list(self.db.execute("select last_insert_rowid();"))[0][0] or None

    def insert(self, *args, **kwargs):
        """ Inserts a new row from the given field parameters, returns id.
        """
        # Table.insert(name="Taxi", age=2, type="cat")
        # Table.insert({"name":"Fricassée", "age":2, "type":"cat"})
        commit = kwargs.pop("commit", True) # As fieldname, use abs(Table.name, "commit").
        if len(args) == 0 and len(kwargs) == 1 and isinstance(kwargs.get("values"), dict):
            kwargs = kwargs["values"]
        elif len(args) == 1 and isinstance(args[0], dict):
            kwargs = dict(args[0], **kwargs)
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            kwargs = dict(list(zip((f for f in self.fields if f != self.pk), args[0])))
        if len(self.default) > 0:
            kwargs.update(self.default)
        k = ", ".join("`%s`" % k for k in kwargs.keys())
        v = ", ".join(self.db.escape(v) for v in kwargs.values())
        q = "insert into `%s` (%s) values (%s);" % (self.name, k, v)
        self.db.execute(q, commit)
        return self._insert_id()

    def update(self, id, *args, **kwargs):
        """ Updates the row with the given id.
        """
        # Table.update(1, age=3)
        # Table.update(1, {"age":3})
        # Table.update(all(filter(field="name", value="Taxi")), age=3)
        commit = kwargs.pop("commit", True) # As fieldname, use abs(Table.name, "commit").
        if isinstance(id, (list, tuple)):
            id = FilterChain(*id)
        if len(args) == 0 and len(kwargs) == 1 and isinstance(kwargs.get("values"), dict):
            kwargs = kwargs["values"]
        if len(args) == 1 and isinstance(args[0], dict):
            a = args[0]
            a.update(kwargs)
            kwargs = a
        kv = ", ".join("`%s`=%s" % (k, self.db.escape(v)) for k, v in kwargs.items())
        q = "update `%s` set %s where %s;" % (self.name, kv,
            not isinstance(id, (Filter, FilterChain)) and cmp(self.primary_key, id, "=", self.db.escape) \
             or id.SQL(escape=self.db.escape))
        self.db.execute(q, commit)

    def delete(self, id, commit=True):
        """ Removes the row which primary key equals the given id.
        """
        # Table.delete(1)
        # Table.delete(ALL)
        # Table.delete(all(("type","cat"), ("age",15,">")))
        if isinstance(id, (list, tuple)):
            id = FilterChain(*id)
        q = "delete from `%s` where %s" % (self.name,
            not isinstance(id, (Filter, FilterChain)) and cmp(self.primary_key, id, "=", self.db.escape) \
             or id.SQL(escape=self.db.escape))
        self.db.execute(q, commit)

    append, edit, remove = insert, update, delete

    @property
    def xml(self):
        return xml(self)

    def datasheet(self):
        return Datasheet(rows=self.rows(), fields=[(f, self.schema[f].type) for f in self.fields])

    def __repr__(self):
        return "Table(name=%s, count=%s, database=%s)" % (
            repr(self.name),
            repr(self.count()),
            repr(self.db.name))

#### QUERY #########################################################################################

#--- QUERY SYNTAX ----------------------------------------------------------------------------------

BETWEEN, LIKE, IN = \
    "between", "like", "in"

sql_functions = \
    "first|last|count|min|max|sum|avg|stdev|group_concat|concatenate|" \
    "year|month|day|hour|minute|second|" \
    "length|lower|upper|substr|substring|replace|trim|round|random|rand|" \
    "strftime|date_format"


def abs(table, field):
    """ For a given <fieldname>, returns the absolute <tablename>.<fieldname>.
        This is useful when constructing queries with relations to other tables.
    """
    def _format(s):
        if "." not in s:
            # Field could be wrapped in a function: year(date) => year(table.date).
            p = s.endswith(")") and re.match(r"^(" + sql_functions + r")\(", s, re.I) or None
            i = p and len(p.group(0)) or 0
            return "%s%s.%s" % (s[:i], table, s[i:])
        return s
    if isinstance(field, (list, tuple)):
        return [_format(f) for f in field]
    return _format(field)


def cmp(field, value, comparison="=", escape=lambda v: _escape(v), table=""):
    """ Returns an SQL WHERE comparison string using =, i=, !=, >, <, >=, <= or BETWEEN.
        Strings may contain wildcards (*) at the start or at the end.
        A list or tuple of values can be given when using =, != or BETWEEN.
    """
    # Use absolute field names if table name is given:
    if table:
        field = abs(table, field)
    # cmp("name", "Mar*") => "name like 'Mar%'".
    if isinstance(value, str) and (value.startswith(("*", "%")) or value.endswith(("*", "%"))):
        if comparison in ("=", "i=", "==", LIKE):
            return "%s like %s" % (field, escape(value.replace("*", "%")))
        if comparison in ("!=", "<>"):
            return "%s not like %s" % (field, escape(value.replace("*", "%")))
    # cmp("name", "markov") => "name" like 'markov'" (case-insensitive).
    if isinstance(value, str):
        if comparison == "i=":
            return "%s like %s" % (field, escape(value))
    # cmp("type", ("cat", "dog"), "!=") => "type not in ('cat','dog')".
    # cmp("amount", (10, 100), ":") => "amount between 10 and 100".
    if isinstance(value, (list, tuple)):
        if find(lambda v: isinstance(v, str) and (v.startswith("*") or v.endswith("*")), value):
            return "(%s)" % any(*[(field, v) for v in value]).sql(escape=escape)
        if comparison in ("=", "==", IN):
            return "%s in (%s)" % (field, ",".join(escape(v) for v in value))
        if comparison in ("!=", "<>"):
            return "%s not in (%s)" % (field, ",".join(escape(v) for v in value))
        if comparison in (":", BETWEEN):
            return "%s between %s and %s" % (field, escape(value[0]), escape(value[1]))
    # cmp("type", None, "!=") => "type is not null".
    if isinstance(value, type(None)):
        if comparison in ("=", "=="):
            return "%s is null" % field
        if comparison in ("!=", "<>"):
            return "%s is not null" % field
    # Using a subquery:
    if isinstance(value, Query):
        if comparison in ("=", "==", IN):
            return "%s in %s" % (field, escape(value))
        if comparison in ("!=", "<>"):
            return "%s not in %s" % (field, escape(value))
    return "%s%s%s" % (field, comparison, escape(value))

# Functions for date fields: cmp(year("date"), 1999, ">").


def year(date):
    return "year(%s)" % date


def month(date):
    return "month(%s)" % date


def day(date):
    return "day(%s)" % date


def hour(date):
    return "hour(%s)" % date


def minute(date):
    return "minute(%s)" % date


def second(date):
    return "second(%s)" % date

# Aggregate functions.


def count(value):
    return "count(%s)" % value


def sum(value):
    return "sum(%s)" % value

#--- QUERY FILTER ----------------------------------------------------------------------------------

AND, OR = "and", "or"


class Filter(tuple):
    def __new__(cls, field, value, comparison):
        return tuple.__new__(cls, (field, value, comparison))

    def SQL(self, **kwargs):
        return cmp(*self, **kwargs)


def filter(field, value, comparison="="):
    return Filter(field, value, comparison)


def eq(field, value):
    return Filter(field, value, "=")


def eqi(field, value):
    return Filter(field, value, "i=")


def ne(field, value):
    return Filter(field, value, "!=")


def gt(field, value):
    return Filter(field, value, ">")


def lt(field, value):
    return Filter(field, value, "<")


def gte(field, value):
    return Filter(field, value, ">=")


def lte(field, value):
    return Filter(field, value, "<=")


def rng(field, value):
    return Filter(field, value, ":")


class FilterChain(list):

    def __init__(self, *args, **kwargs):
        """ A list of SQL WHERE filters combined with AND/OR logical operator.
        """
        # FilterChain(filter("type", "cat", "="), filter("age", 5, "="), operator=AND)
        # FilterChain(type="cat", age=5, operator=AND)
        # FilterChain({"type": "cat", "age": 5}, operator=AND)
        if len(args) == 1 and isinstance(args[0], dict):
            args[0].pop("operator", None)
            kwargs = dict(args[0], **kwargs)
            args = []
        else:
            args = list(args)
        self.operator = kwargs.pop("operator", AND)
        args.extend(list(filter(k, v, "=")) for k, v in kwargs.items())
        list.__init__(self, args)

    def SQL(self, **kwargs):
        """ For example, filter for small pets with tails or wings
            (which is not the same as small pets with tails or pets with wings):
            >>> FilterChain(
            >>>     filter("type", "pet"),
            >>>     filter("weight", (4,6), ":"),
            >>>     FilterChain(
            >>>         filter("tail", True),
            >>>         filter("wing", True), operator=OR))
            Yields:
            "type='pet' and weight between 4 and 6 and (tail=1 or wing=1)"
        """
        # Remember to pass the right escape() function as optional parameter.
        a = []
        for filter in self:
            # Traverse subgroups recursively.
            if isinstance(filter, FilterChain):
                a.append("(%s)" % filter.SQL(**kwargs))
                continue
            # Convert filter() to string with cmp() - see above.
            if isinstance(filter, (Filter, list, tuple)):
                a.append(cmp(*filter, **kwargs))
                continue
            raise TypeError("FilterChain can contain other FilterChain or filter(), not %s" % type(filter))
        return (" %s " % self.operator).join(a)

    sql = SQL


def all(*args, **kwargs):
    """ Returns a group of filters combined with AND.
    """
    kwargs["operator"] = AND
    return FilterChain(*args, **kwargs)


def any(*args, **kwargs):
    """ Returns a group of filters combined with OR.
    """
    kwargs["operator"] = OR
    return FilterChain(*args, **kwargs)

# From a GET-query dict:
# all(*dict.items())

# filter() value can also be a Query with comparison=IN.

#--- QUERY -----------------------------------------------------------------------------------------

# Relations:
INNER = "inner" # The rows for which there is a match in both tables (same as join=None).
LEFT = "left"  # All rows from this table, with field values from the related table when possible.
RIGHT = "right" # All rows from the related table, with field values from this table when possible.
FULL = "full"  # All rows form both tables.


class Relation(tuple):
    def __new__(cls, field1, field2, table, join):
        return tuple.__new__(cls, (field1, field2, table, join))


def relation(field1, field2, table, join=LEFT):
    return Relation(field1, field2, table, join)

rel = relation

# Sorting:
ASCENDING = "asc"
DESCENDING = "desc"

# Grouping:
FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV, CONCATENATE = \
    "first", "last", "count", "max", "min", "sum", "avg", "stdev", "group_concat"


class Query(object):

    id, cache = 0, {}

    def __init__(self, table, fields=ALL, filters=[], relations=[], sort=None, order=ASCENDING, group=None, function=FIRST, range=None):
        """ A selection of rows from the given table, filtered by any() and all() constraints.
        """
        # Table.search(ALL, filters=any(("type","cat"), ("type","dog")) => cats and dogs.
        # Table.search(("type", "name")), group="type", function=COUNT) => all types + amount per type.
        # Table.search(("name", "types.has_tail"), relations=[("types","type","id")]) => links type to types.id.
        if isinstance(filters, Filter):
            filters = [filters]
        if isinstance(relations, Relation):
            relations = [relations]
        Query.id += 1
        filters = FilterChain(*filters, **dict(operator=getattr(filters, "operator", AND)))
        self._id       = Query.id
        self._table    = table
        self.fields    = fields    # A field name, list of field names or ALL.
        self.aliases   = {}        # A dictionary of field name aliases, used with Query.xml or Query-in-Query.
        self.filters   = filters   # A group of filter() objects.
        self.relations = relations # A list of rel() objects.
        self.sort      = sort      # A field name, list of field names or field index for sorting.
        self.order     = order     # ASCENDING or DESCENDING.
        self.group     = group     # A field name, list of field names or field index for folding.
        self.function  = function  # FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV or CONCATENATE (or list).
        self.range     = range     # A (index1, index2)-tuple. The first row in the table is 0.

    @property
    def table(self):
        return self._table

    def __len__(self):
        return len(list(self.rows()))

    def __iter__(self):
        return self.execute()

    def __getitem__(self, i):
        return self.rows()[i] # poor performance

    def SQL(self):
        """ Yields the SQL syntax of the query, which can be passed to Database.execute().
            The SQL string will be cached for faster reuse.
        """
        #if self._id in Query.cache:
        #    return Query.cache[self._id]
        # Construct the SELECT clause from Query.fields.
        g = not isinstance(self.group, (list, tuple)) and [self.group] or self.group
        g = [abs(self._table.name, f) for f in g if f is not None]
        fields = not isinstance(self.fields, (list, tuple)) and [self.fields] or self.fields
        fields = [f in self.aliases and "%s as %s" % (f, self.aliases[f]) or f for f in fields]
        fields = abs(self._table.name, fields)
        # With a GROUPY BY clause, fields not used for grouping are wrapped in the given function.
        # The function can also be a list of functions for each field (FIRST by default).
        if g and isinstance(self.function, str):
            fields = [f in g and f or "%s(%s)" % (self.function, f) for f in fields]
        if g and isinstance(self.function, (list, tuple)):
            fields = [f in g and f or "%s(%s)" % (F, f) for F, f in zip(self.function + [FIRST] * len(fields), fields)]
        q = []
        q.append("select %s" % ", ".join(fields))
        # Construct the FROM clause from Query.relations.
        # Table relations defined on the database are taken into account,
        # but overridden by relations defined on the query.
        q.append("from `%s`" % self._table.name)
        relations = {}
        for key1, key2, table, join in (rel(*r) for r in self.relations):
            table = isinstance(table, Table) and table.name or table
            relations[table] = (key1, key2, join)
        for table1, key1, table2, key2, join in self._table.db.relations:
            if table1 == self._table.name:
                relations.setdefault(table2, (key1, key2, join))
            if table2 == self._table.name:
                relations.setdefault(table1, (key1, key2, join == LEFT and RIGHT or (join == RIGHT and LEFT or join)))
        # Define relations only for tables whose fields are actually selected.
        for (table, (key1, key2, join)) in relations.items():
            for f in fields:
                if table + "." in f:
                    q.append("%sjoin `%s`" % (join and join + " " or "", table))
                    q.append("on %s=%s" % (abs(self._table.name, key1), abs(self._table.db[table].name, key2)))
                    break
        # Construct the WHERE clause from Query.filters.SQL().
        # Use the database's escape function and absolute field names.
        if len(self.filters) > 0:
            q.append("where %s" % self.filters.SQL(escape=self._table.db.escape, table=self._table.name))
        # Construct the ORDER BY clause from Query.sort and Query.order.
        # Construct the GROUP BY clause from Query.group.
        for clause, value in (("order", self.sort), ("group", self.group)):
            if isinstance(value, str) and value != "":
                q.append("%s by %s" % (clause, abs(self._table.name, value)))
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                q.append("%s by %s" % (clause, ", ".join(abs(self._table.name, value))))
            elif isinstance(value, int):
                q.append("%s by %s" % (clause, abs(self._table.name, self._table.fields[value])))
            if self.sort and clause == "order":
                if self.order in (ASCENDING, DESCENDING):
                    q.append("%s" % self.order)
                elif isinstance(self.order, (list, tuple)):
                    q[-1] = ",".join(" ".join(v) for v in zip(q[-1].split(","), self.order))
        # Construct the LIMIT clause from Query.range.
        if self.range:
            q.append("limit %s, %s" % (str(self.range[0]), str(self.range[1])))
        q = " ".join(q) + ";"
        # Cache the SQL-string for faster retrieval.
        #if len(Query.cache) > 100:
        #    Query.cache.clear()
        #Query.cache[self._id] = q # XXX cache is not updated when properties change.
        return q

    sql = SQL

    def execute(self):
        """ Executes the query and returns an iterator over the matching rows in the table.
        """
        return self._table.db.execute(self.SQL())

    def iterrows(self):
        """ Executes the query and returns an iterator over the matching rows in the table.
        """
        return self.execute()

    def rows(self):
        """ Executes the query and returns the matching rows from the table.
        """
        return list(self.execute())

    def record(self, row):
        """ Returns the given row as a dictionary of (field or alias, value)-items.
        """
        return dict(list(zip((self.aliases.get(f, f) for f in self.fields), row)))

    @property
    def xml(self):
        return xml(self)

    def __repr__(self):
        return "Query(sql=%s)" % repr(self.SQL())


def associative(query):
    """ Yields query rows as dictionaries of (field, value)-items.
    """
    for row in query:
        yield query.record(row)

assoc = associative

#### VIEW ##########################################################################################
# A representation of data based on a table in the database.
# The render() method can be overridden to output data in a certain format (e.g., HTML for a web app).


class View(object):

    def __init__(self, database, table, schema=[]):
        """ A representation of data.
            View.render() should be overridden in a subclass.
        """
        self.database = database
        self._table = isinstance(table, Table) and table.name or table
        self.schema = schema # A list of table fields - see field().

    @property
    def db(self):
        return self.database

    @property
    def table(self):
        # If it doesn't exist, create the table from View.schema.
        if self._table not in self.db:
            self.setup()
        return self.db[self._table]

    def setup(self, overwrite=False):
        """ Creates the database table from View.schema, optionally overwriting the old table.
        """
        if overwrite:
            self.db.drop(self._table)
        if self._table not in self.db:
            self.db.create(self._table, self.schema)

    def render(self, *path, **query):
        """ This method should be overwritten to return formatted table output (XML, HTML, RSS, ...)
            For web apps, the given path should list all parts in the relative URL path,
            and query is a dictionary of all POST and GET variables sent from the client.
            For example: http://books.com/science/new
            => ["science", "new"]
            => render() data from db.books.filter(ALL, category="science", new=True).
        """
        pass

    # CherryPy-specific.
    def default(self, *path, **query):
        return self.render(*path, **query)
    default.exposed = True

#### XML PARSER ####################################################################################

XML_HEADER = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"


def _unpack_fields(table, fields=[]):
    """ Replaces "*" with the actual field names.
        Fields from related tables keep the "<tablename>." prefix.
    """
    u = []
    for f in fields:
        a, b = "." in f and f.split(".", 1) or (table.name, f)
        if a == table.name and b == ALL:
            # <table>.*
            u.extend(f for f in table.db.tables[a].fields)
        elif a != table.name and b == ALL:
            # <related-table>.*
            u.extend("%s.%s" % (a, f) for f in table.db.tables[a].fields)
        elif a != table.name:
            # <related-table>.<field>
            u.append("%s.%s" % (a, b))
        else:
            # <field>
            u.append(b)
    return u


def xml_format(a):
    """ Returns the given attribute (string, int, float, bool, None) as a quoted unicode string.
    """
    if isinstance(a, str):
        return "\"%s\"" % encode_entities(a)
    if isinstance(a, bool):
        return "\"%s\"" % ("no", "yes")[int(a)]
    if isinstance(a, int):
        return "\"%s\"" % a
    if isinstance(a, float):
        return "\"%s\"" % round(a, 5)
    if isinstance(a, type(None)):
        return "\"\""
    if isinstance(a, Date):
        return "\"%s\"" % str(a)
    if isinstance(a, datetime):
        return "\"%s\"" % str(date(mktime(a.timetuple())))


def xml(rows):
    """ Returns the rows in the given Table or Query as an XML-string, for example:
        <?xml version="1.0" encoding="utf-8"?>
        <table name="pets", fields="id, name, type" count="2">
            <schema>
                <field name="id", type="integer", index="primary", optional="no" />
                <field name="name", type="string", length="50" />
                <field name="type", type="string", length="50" />
            </schema>
            <rows>
                <row id="1", name="Taxi", type="cat" />
                <row id="2", name="Hofstadter", type="dog" />
            </rows>
        </table>
    """
    if isinstance(rows, Table):
        root, table, rows, fields, aliases = "table", rows, rows.rows(), rows.fields, {}
    if isinstance(rows, Query):
        root, table, rows, fields, aliases, = "query", rows.table, rows.rows(), rows.fields, rows.aliases
    fields = _unpack_fields(table, fields)
    # <table name="" fields="" count="">
    # <query table="" fields="" count="">
    xml = []
    xml.append(XML_HEADER)
    xml.append("<%s %s=%s fields=\"%s\" count=\"%s\">" % (
        root,
        root != "table" and "table" or "name",
        xml_format(table.name), # Use Query.aliases as field names.
        ", ".join(encode_entities(aliases.get(f, f)) for f in fields),
        len(rows)))
    # <schema>
    # Field information is retrieved from the (related) table schema.
    # If the XML is imported as a Table, the related fields become part of it.
    xml.append("\t<schema>")
    for f in fields:
        if f not in table.schema:
            s = f.split(".")
            s = table.db[s[0]].schema[s[-1]]
        else:
            s = table.schema[f]
        # <field name="" type="" length="" default="" index="" optional="" extra="" />
        xml.append("\t\t<field name=%s type=%s%s%s%s%s%s />" % (
            xml_format(aliases.get(f, f)),
            xml_format(s.type),
            s.length is not None and " length=%s" % xml_format(s.length) or "",
            s.default is not None and " default=%s" % xml_format(s.default) or "",
            s.index is not False and " index=%s" % xml_format(s.index) or "",
            s.optional is not True and " optional=%s" % xml_format(s.optional) or "",
            s.extra is not None and " extra=%s" % xml_format(s.extra) or ""))
    xml.append("\t</schema>")
    xml.append("\t<rows>")
    # <rows>
    for r in rows:
        # <row field="value" />
        xml.append("\t\t<row %s />" % " ".join("%s=%s" % (aliases.get(k, k), xml_format(v)) for k, v in zip(fields, r)))
    xml.append("\t</rows>")
    xml.append("</%s>" % root)
    xml = "\n".join(xml)
    return xml


def parse_xml(database, xml, table=None, field=lambda s: s.replace(".", "-")):
    """ Creates a new table in the given database from the given XML-string.
        The XML must be in the format generated by Table.xml.
        If the table already exists, raises a TableError.
        The given table parameter can be used to rename the table.
        The given field function can be used to rename field names.
    """
    def _attr(node, attribute, default=""):
        return node.getAttribute(attribute) or default
    # parseString() will decode entities, no need for decode_entities().
    from xml.dom.minidom import parseString
    dom = parseString(encode_utf8(xml))
    a = dom.getElementsByTagName("table")
    b = dom.getElementsByTagName("query")
    if len(a) > 0:
        table = table or _attr(a[0], "name", "")
    if len(b) > 0:
        table = table or _attr(b[0], "table", "")
    # Parse field information (i.e., field name, field type, etc.)
    fields, schema, rows = [], [], []
    for f in dom.getElementsByTagName("field"):
        fields.append(_attr(f, "name"))
        schema.append(_field(
            name = field(_attr(f, "name")),
            type = _attr(f, "type") == STRING and STRING(int(_attr(f, "length", 255))) or _attr(f, "type"),
         default = _attr(f, "default", None),
           index = _attr(f, "index", False),
        optional = _attr(f, "optional", True) != "no"
        ))
        # Integer primary key is always auto-increment.
        # The id's in the new table will differ from those in the XML.
        if _attr(f, "index") == PRIMARY and _attr(f, "type") == INTEGER:
            fields.pop()
    # Parse row data.
    for r in dom.getElementsByTagName("row"):
        rows.append({})
        for i, f in enumerate(fields):
            v = _attr(r, f, None)
            if schema[i][1] == BOOLEAN:
                rows[-1][f] = (0, 1)[v != "no"]
            else:
                rows[-1][f] = v
    # Create table if not exists and insert rows.
    if database.connected is False:
        database.connect()
    if table in database:
        raise TableError("table '%s' already exists" % table)
    database.create(table, fields=schema)
    for r in rows:
        database[table].insert(r, commit=False)
    database.commit()
    return database[table]

#db = Database("test")
#db.create("persons", (pk(), field("data", TEXT)))
#db.persons.append((json.dumps({"name": u"Schrödinger", "type": "cat"}),))
#
#for id, data in db.persons:
#    print(id, json.loads(data))

#### DATASHEET #####################################################################################

#--- CSV -------------------------------------------------------------------------------------------

# Raise the default field size limit:
csvlib.field_size_limit(sys.maxsize)


def csv_header_encode(field, type=STRING):
    # csv_header_encode("age", INTEGER) => "age (INTEGER)".
    t = re.sub(r"^varchar\(.*?\)", "string", (type or ""))
    t = t and " (%s)" % t or ""
    s = "%s%s" % (field or "", t.upper())
    return s


def csv_header_decode(s):
    # csv_header_decode("age (INTEGER)") => ("age", INTEGER).
    p = r"STRING|INTEGER|FLOAT|TEXT|BLOB|BOOLEAN|DATE|"
    p = re.match(r"(.*?) \((" + p + ")\)", s)
    s = s.endswith(" ()") and s[:-3] or s
    return p and (string(p.group(1), default=None), p.group(2).lower()) or (string(s) or None, None)


class CSV(list):

    def __new__(cls, rows=[], fields=None, **kwargs):
        """ A list of lists that can be imported and exported as a comma-separated text file (CSV).
        """
        if isinstance(rows, str) and os.path.exists(rows):
            csv = cls.load(rows, **kwargs)
        else:
            csv = list.__new__(cls)
        return csv

    def __init__(self, rows=[], fields=None, **kwargs):
        # List of (name, type)-tuples (STRING, INTEGER, FLOAT, DATE, BOOLEAN).
        fields = fields or kwargs.pop("headers", None)
        fields = fields and [tuple(f) if isinstance(f, (tuple, list)) else (f, None) for f in fields] or None
        self.__dict__["fields"] = fields
        if hasattr(rows, "__iter__"):
            self.extend(rows, **kwargs)

    def extend(self, rows, **kwargs):
        list.extend(self, rows)

    def _set_headers(self, v):
        self.__dict__["fields"] = v

    def _get_headers(self):
        return self.__dict__["fields"]

    headers = property(_get_headers, _set_headers)

    def save(self, path, separator=",", encoder=lambda v: v, headers=False, password=None, **kwargs):
        """ Exports the table to a unicode text file at the given path.
            Rows in the file are separated with a newline.
            Columns in a row are separated with the given separator (by default, comma).
            For data types other than string, int, float, bool or None, a custom string encoder can be given.
        """
        # Optional parameters include all arguments for csv.writer(), see:
        # http://docs.python.org/library/csv.html#csv.writer
        kwargs.setdefault("delimiter", separator)
        kwargs.setdefault("quoting", csvlib.QUOTE_ALL)
        # csv.writer will handle str, int, float and bool:
        s = StringIO()
        w = csvlib.writer(s, **kwargs)
        if headers and self.fields is not None:
            w.writerows([[csv_header_encode(name, type) for name, type in self.fields]])
        w.writerows([[encoder(v) for v in row] for row in self])
        s = s.getvalue()
        s = s.strip()
        s = re.sub("([^\"]|^)\"None\"", "\\1None", s)
        s = s if not password else encrypt_string(s, password)
        f = open(path, "w", encoding="utf-8")
        f.write(BOM_UTF8)
        f.write(s)
        f.close()

    @classmethod
    def load(cls, path, separator=",", decoder=lambda v: v, headers=False, preprocess=None, password=None, **kwargs):
        """ Returns a table from the data in the given text file.
            Rows are expected to be separated by a newline.
            Columns are expected to be separated by the given separator (by default, comma).
            Strings will be converted to int, float, bool, date or None if headers are parsed.
            For other data types, a custom string decoder can be given.
            A preprocess(str) function can be given to change the file content before parsing.
        """
        # Date objects are saved and loaded as strings, but it is easy to convert these back to dates:
        # - set a DATE field type for the column,
        # - or do Table.columns[x].map(lambda s: date(s))
        data = open(path, "rU", encoding="utf-8")
        data = data if not password else decrypt_string(data.read(), password)
        data.seek(data.readline().startswith(BOM_UTF8) and 3 or 0)
        data = data if not password else BytesIO(data.replace("\r\n", "\n").replace("\r", "\n"))
        data = data if not preprocess else BytesIO(preprocess(data.read()))
        data = csvlib.reader(data, delimiter=separator)
        i, n = kwargs.get("start"), kwargs.get("count")
        if i is not None and n is not None:
            data = list(islice(data, i, i + n))
        elif i is not None:
            data = list(islice(data, i, None))
        elif n is not None:
            data = list(islice(data, n))
        else:
            data = list(data)
        if headers:
            fields = [csv_header_decode(field) for field in data.pop(0)]
            fields += [(None, None)] * (max([0] + [len(row) for row in data]) - len(fields))
        else:
            fields = []
        if not fields:
            # Cast fields using the given decoder (by default, all strings + None).
            data = [[decoder(decode_utf8(v) if v != "None" else None) for v in row] for row in data]
        else:
            # Cast fields to their defined field type (STRING, INTEGER, ...)
            for i, row in enumerate(data):
                for j, v in enumerate(row):
                    type = fields[j][1]
                    if row[j] == "None":
                        row[j] = decoder(None)
                    elif type is None:
                        row[j] = decoder(decode_utf8(v))
                    elif type in (STRING, TEXT):
                        row[j] = decode_utf8(v)
                    elif type == INTEGER:
                        row[j] = int(row[j])
                    elif type == FLOAT:
                        row[j] = float(row[j])
                    elif type == BOOLEAN:
                        row[j] = bool(row[j])
                    elif type == DATE:
                        row[j] = date(row[j])
                    elif type == BLOB:
                        row[j] = v
                    else:
                        row[j] = decoder(decode_utf8(v))
        return cls(rows=data, fields=fields, **kwargs)

#--- DATASHEET -------------------------------------------------------------------------------------


class Datasheet(CSV):

    def __init__(self, rows=[], fields=None, **kwargs):
        """ A matrix of rows and columns, where each row and column can be retrieved as a list.
            Values can be any kind of Python object.
        """
        # NumPy array, convert to list of int/float/str/bool.
        if rows.__class__.__name__ == "ndarray":
            rows = rows.tolist()
        self.__dict__["_rows"] = DatasheetRows(self)
        self.__dict__["_columns"] = DatasheetColumns(self)
        self.__dict__["_m"] = 0 # Number of columns per row, see Datasheet.insert().
        list.__init__(self)
        CSV.__init__(self, rows, fields, **kwargs)

    def _get_rows(self):
        return self._rows

    def _set_rows(self, rows):
        # Datasheet.rows property can't be set, except in special case Datasheet.rows += row.
        if isinstance(rows, DatasheetRows) and rows._datasheet == self:
            self._rows = rows
            return
        raise AttributeError("can't set attribute")
    rows = property(_get_rows, _set_rows)

    def _get_columns(self):
        return self._columns

    def _set_columns(self, columns):
        # Datasheet.columns property can't be set, except in special case Datasheet.columns += column.
        if isinstance(columns, DatasheetColumns) and columns._datasheet == self:
            self._columns = columns
            return
        raise AttributeError("can't set attribute")
    columns = cols = property(_get_columns, _set_columns)

    def __getattr__(self, k):
        """ Columns can be retrieved by field name, e.g., Datasheet.date.
        """
        #print("Datasheet.__getattr__", k)
        if k in self.__dict__:
            return self.__dict__[k]
        for i, f in enumerate(f[0] for f in self.__dict__["fields"] or []):
            if f == k:
                return self.__dict__["_columns"][i]
        raise AttributeError("'Datasheet' object has no attribute '%s'" % k)

    def __setattr__(self, k, v):
        """ Columns can be set by field name, e.g., Datasheet.date = [...].
        """
        #print("Datasheet.__setattr__", k)
        if k in self.__dict__:
            self.__dict__[k] = v
            return
        if k == "rows":
            self._set_rows(v)
            return
        if k == "columns":
            self._set_columns(v)
            return
        if k == "headers":
            self._set_headers(v)
            return
        for i, f in enumerate(f[0] for f in self.__dict__["fields"] or []):
            if f == k:
                self.__dict__["_columns"].__setitem__(i, v)
                return
        raise AttributeError("'Datasheet' object has no attribute '%s'" % k)

    def __setitem__(self, index, value):
        """ Sets an item or row in the matrix.
            For Datasheet[i] = v, sets the row at index i to v.
            For Datasheet[i,j] = v, sets the value in row i and column j to v.
        """
        if isinstance(index, tuple):
            list.__getitem__(self, index[0])[index[1]] = value
        elif isinstance(index, int):
            self.pop(index)
            self.insert(index, value)
        else:
            raise TypeError("Datasheet indices must be int or tuple")

    def __getitem__(self, index):
        """ Returns an item, row or slice from the matrix.
            For Datasheet[i], returns the row at the given index.
            For Datasheet[i,j], returns the value in row i and column j.
        """
        if isinstance(index, int):
            # Datasheet[i] => row i.
            return list.__getitem__(self, index)
        elif isinstance(index, slice):
            return Datasheet(rows = list.__getitem__(self, index), fields = self.fields)
        elif isinstance(index, tuple):
            i, j = index
            # Datasheet[i,j] => item from column j in row i.
            # Datasheet[i,j1:j2] => columns j1-j2 from row i.
            if not isinstance(i, slice):
                return list.__getitem__(self, i)[j]
            # Datasheet[i1:i2,j] => column j from rows i1-i2.
            if not isinstance(j, slice):
                return [row[j] for row in list.__getitem__(self, i)]
            # Datasheet[i1:i2,j1:j2] => Datasheet with columns j1-j2 from rows i1-i2.
            return Datasheet(
                  rows = (row[j] for row in list.__getitem__(self, i)),
                fields = self.fields and self.fields[j] or self.fields)
        raise TypeError("Datasheet indices must be int, tuple or slice")

    # Python 2 (backward compatibility)
    __getslice__ = lambda self, i, j: self.__getitem__(slice(i, j))

    def __delitem__(self, index):
        self.pop(index)

    # datasheet1 = datasheet2 + datasheet3
    # datasheet1 = [[...],[...]] + datasheet2
    # datasheet1 += datasheet2
    def __add__(self, datasheet):
        m = self.copy()
        m.extend(datasheet)
        return m

    def __radd__(self, datasheet):
        m = Datasheet(datasheet)
        m.extend(self)
        return m

    def __iadd__(self, datasheet):
        self.extend(datasheet)
        return self

    def insert(self, i, row, default=None, **kwargs):
        """ Inserts the given row into the matrix.
            Missing columns at the end (right) will be filled with the default value.
        """
        try:
            # Copy the row (fast + safe for generators and DatasheetColumns).
            row = [v for v in row]
        except:
            raise TypeError("Datasheet.insert(x): x must be list")
        list.insert(self, i, row)
        m = max((len(self) > 1 and self._m or 0, len(row)))
        if len(row) < m:
            row.extend([default] * (m - len(row)))
        if self._m < m:
            # The given row might have more columns than the rows in the matrix.
            # Performance takes a hit when these rows have to be expanded:
            for row in self:
                if len(row) < m:
                    row.extend([default] * (m - len(row)))
        self.__dict__["_m"] = m

    def append(self, row, default=None, _m=None, **kwargs):
        self.insert(len(self), row, default)

    def extend(self, rows, default=None, **kwargs):
        for row in rows:
            self.insert(len(self), row, default)

    def group(self, j, function=FIRST, key=lambda v: v):
        """ Returns a datasheet with unique values in column j by grouping rows with the given function.
            The function takes a list of column values as input and returns a single value,
            e.g. FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV, CONCATENATE.
            The function can also be a list of functions (one for each column).
            TypeError will be raised when the function cannot handle the data in a column.
            The key argument can be used to map the values in column j, for example:
            key=lambda date: date.year to group Date objects by year.
        """
        if isinstance(function, tuple):
            function = list(function)
        if not isinstance(function, list):
            function = [function] * self._m
        if len(function) < self._m:
            function += [FIRST] * (self._m - len(function))
        for i, f in enumerate(function):
            if i == j: # Group column j is always FIRST.
                f = FIRST
            if f == FIRST:
                function[i] = lambda a: a[+0]
            if f == LAST:
                function[i] = lambda a: a[-1]
            if f == COUNT:
                function[i] = lambda a: len(a)
            if f == MAX:
                function[i] = lambda a: max(a)
            if f == MIN:
                function[i] = lambda a: min(a)
            if f == SUM:
                function[i] = lambda a: _sum([x for x in a if x is not None])
            if f == AVG:
                function[i] = lambda a: avg([x for x in a if x is not None])
            if f == STDEV:
                function[i] = lambda a: stdev([x for x in a if x is not None])
            if f == CONCATENATE:
                function[i] = lambda a: ",".join(decode_utf8(x) for x in a if x is not None)
        J = j
        # Map unique values in column j to a list of rows that contain this value.
        g = {}
        [g.setdefault(key(v), []).append(i) for i, v in enumerate(self.columns[j])]
        # Map unique values in column j to a sort index in the new, grouped list.
        o = [(g[v][0], v) for v in g]
        o = dict([(v, i) for i, (ii, v) in enumerate(sorted(o))])
        # Create a list of rows with unique values in column j,
        # applying the group function to the other columns.
        u = [None] * len(o)
        for v in g:
            # List the column values for each group row.
            u[o[v]] = [[list.__getitem__(self, i)[j] for i in g[v]] for j in range(self._m)]
            # Apply the group function to each row, except the unique value in column j.
            u[o[v]] = [function[j](column) for j, column in enumerate(u[o[v]])]
            u[o[v]][J] = v # list.__getitem__(self, i)[J]
        return Datasheet(rows=u)

    def record(self, row):
        """ Returns the given row as a dictionary of (field or alias, value)-items.
        """
        return dict(list(zip((f for f, type in self.fields), row)))

    def map(self, function=lambda item: item):
        """ Applies the given function to each item in the matrix.
        """
        for i, row in enumerate(self):
            for j, item in enumerate(row):
                row[j] = function(item)

    def slice(self, i, j, n, m):
        """ Returns a new Datasheet starting at row i and column j and spanning n rows and m columns.
        """
        return Datasheet(rows=[list.__getitem__(self, i)[j:j + m] for i in range(i, i + n)])

    def copy(self, rows=ALL, columns=ALL):
        """ Returns a new Datasheet from a selective list of row and/or column indices.
        """
        if rows == ALL and columns == ALL:
            return Datasheet(rows=self)
        if rows == ALL:
            return Datasheet(rows=list(zip(*(self.columns[j] for j in columns))))
        if columns == ALL:
            return Datasheet(rows=(self.rows[i] for i in rows))
        z = list(zip(*(self.columns[j] for j in columns)))
        return Datasheet(rows=(z[i] for i in rows))

    @property
    def array(self):
        """ Returns a NumPy array.
            Arrays must have elements of the same type, and rows of equal size.
        """
        import numpy
        return numpy.array(self)

    @property
    def json(self, **kwargs):
        """ Returns a JSON-string, as a list of dictionaries (if fields are defined) or as a list of lists.
            This is useful for sending a Datasheet to JavaScript, for example.
        """
        kwargs.setdefault("ensure_ascii", False) # Disable simplejson's Unicode encoder.
        if self.fields is not None:
            s = json.dumps([dict((f[0], row[i]) for i, f in enumerate(self.fields)) for row in self], **kwargs)
        else:
            s = json.dumps(self, **kwargs)
        return decode_utf8(s)

    @property
    def html(self):
        """ Returns a HTML-string with a <table>.
            This is useful for viewing the data, e.g., open("data.html", "wb").write(datasheet.html).
        """
        def encode(s):
            s = "%s" % s
            s = s.replace("&", "&amp;")
            s = s.replace("<", "&lt;")
            s = s.replace(">", "&gt;")
            s = s.replace("-", "&#8209;")
            s = s.replace("\n", "<br>\n")
            return s
        a = []
        a.append("<meta charset=\"utf8\">\n")
        a.append("<style>")
        a.append("table.datasheet { border-collapse: collapse; font: 11px sans-serif; } ")
        a.append("table.datasheet * { border: 1px solid #ddd; padding: 4px; } ")
        a.append("</style>\n")
        a.append("<table class=\"datasheet\">\n")
        if self.fields is not None:
            a.append("<tr>\n")
            a.append("\t<th>%s</th>\n" % "#")
            a.extend("\t<th>%s</th>\n" % encode(f[0]) for f in self.fields)
            a.append("</tr>\n")
        for i, row in enumerate(self):
            a.append("<tr>\n")
            a.append("\t<td>%s</td>\n" % (i + 1))
            a.extend("\t<td>%s</td>\n" % encode(v) for v in row)
            a.append("</tr>\n")
        a.append("</table>")
        return encode_utf8("".join(a))


def flip(datasheet):
    """ Returns a new datasheet with rows for columns and columns for rows.
    """
    return Datasheet(rows=datasheet.columns)


def csv(*args, **kwargs):
    """ Returns a Datasheet from the given CSV file path.
    """
    if len(args) == 0:
        return Datasheet(**kwargs)
    return Datasheet.load(*args, **kwargs)

#--- DATASHEET ROWS --------------------------------------------------------------------------------
# Datasheet.rows mimics the operations on Datasheet:


class DatasheetRows(list):

    def __init__(self, datasheet):
        self._datasheet = datasheet

    def __setitem__(self, i, row):
        self._datasheet.pop(i)
        self._datasheet.insert(i, row)

    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)

    def __getslice__(self, i, j):
        return self._datasheet[i:j]

    def __delitem__(self, i):
        self.pop(i)

    def __len__(self):
        return len(self._datasheet)

    def __iter__(self):
        for i in range(len(self)):
            yield list.__getitem__(self._datasheet, i)

    def __repr__(self):
        return repr(self._datasheet)

    def __add__(self, row):
        raise TypeError("unsupported operand type(s) for +: 'Datasheet.rows' and '%s'" % row.__class__.__name__)

    def __iadd__(self, row):
        self.append(row)
        return self

    def __eq__(self, rows):
        return self._datasheet.__eq__(rows)

    def __ne__(self, rows):
        return self._datasheet.__ne__(rows)

    def insert(self, i, row, default=None):
        self._datasheet.insert(i, row, default)

    def append(self, row, default=None):
        self._datasheet.append(row, default)

    def extend(self, rows, default=None):
        self._datasheet.extend(rows, default)

    def remove(self, row):
        self._datasheet.remove(row)

    def pop(self, i):
        return self._datasheet.pop(i)

    def count(self, row):
        return self._datasheet.count(row)

    def index(self, row):
        return self._datasheet.index(row)

    def sort(self, cmp=None, key=None, reverse=False):
        self._datasheet.sort(cmp, key, reverse)

    def reverse(self):
        self._datasheet.reverse()

    def swap(self, i1, i2):
        self[i1], self[i2] = self[i2], self[i1]

#--- DATASHEET COLUMNS -----------------------------------------------------------------------------


class DatasheetColumns(list):

    def __init__(self, datasheet):
        self._datasheet = datasheet
        self._cache = {} # Keep a reference to DatasheetColumn objects generated with Datasheet.columns[j].
                          # This way we can unlink them when they are deleted.

    def __setitem__(self, j, column):
        if self._datasheet.fields is not None and j < len(self._datasheet.fields):
            # Preserve the column header if it exists.
            f = self._datasheet.fields[j]
        else:
            f = None
        self.pop(j)
        self.insert(j, column, field=f)

    def __getitem__(self, j):
        if j < 0:
            j = j % len(self) # DatasheetColumns[-1]
        if j >= len(self):
            raise IndexError("list index out of range")
        return self._cache.setdefault(j, DatasheetColumn(self._datasheet, j))

    def __getslice__(self, i, j):
        return self._datasheet[:, i:j]

    def __delitem__(self, j):
        self.pop(j)

    def __len__(self):
        return len(self._datasheet) > 0 and len(self._datasheet[0]) or 0

    def __iter__(self):
        for i in range(len(self)):
            yield self.__getitem__(i)

    def __repr__(self):
        return repr(list(iter(self)))

    def __add__(self, column):
        raise TypeError("unsupported operand type(s) for +: 'Datasheet.columns' and '%s'" % column.__class__.__name__)

    def __iadd__(self, column):
        self.append(column)
        return self

    def __eq__(self, columns):
        return list(self) == columns

    def __ne__(self, columns):
        return not self.__eq__(self, columns)

    def insert(self, j, column, default=None, field=None):
        """ Inserts the given column into the matrix.
            Missing rows at the end (bottom) will be filled with the default value.
        """
        try:
            column = [v for v in column]
        except:
            raise TypeError("Datasheet.columns.insert(x): x must be list")
        column = column + [default] * (len(self._datasheet) - len(column))
        if len(column) > len(self._datasheet):
            self._datasheet.extend([[None]] * (len(column) - len(self._datasheet)))
        for i, row in enumerate(self._datasheet):
            row.insert(j, column[i])
        self._datasheet.__dict__["_m"] += 1 # Increase column count.
        # Add a new header.
        if self._datasheet.fields is not None:
            self._datasheet.fields += [(None, None)] * (len(self) - len(self._datasheet.fields) - 1)
            self._datasheet.fields.insert(j, field or (None, None))

    def append(self, column, default=None, field=None):
        self.insert(len(self), column, default, field)

    def extend(self, columns, default=None, fields=[]):
        for j, column in enumerate(columns):
            self.insert(len(self), column, default, j < len(fields) and fields[j] or None)

    def remove(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            self.pop(column._j)
            return
        raise ValueError("list.remove(x): x not in list")

    def pop(self, j):
        column = list(self[j]) # Return a list copy.
        for row in self._datasheet:
            row.pop(j)
        # At one point a DatasheetColumn object was created with Datasheet.columns[j].
        # It might still be in use somewhere, so we unlink it from the datasheet:
        self._cache[j]._datasheet = Datasheet(rows=[[v] for v in column])
        self._cache[j]._j = 0
        self._cache.pop(j)
        for k in range(j + 1, len(self) + 1):
            if k in self._cache:
                # Shift the DatasheetColumn objects on the right to the left.
                self._cache[k - 1] = self._cache.pop(k)
                self._cache[k - 1]._j = k - 1
        self._datasheet.__dict__["_m"] -= 1 # Decrease column count.
        # Remove the header.
        if self._datasheet.fields is not None:
            self._datasheet.fields.pop(j)
        return column

    def count(self, column):
        return len([True for c in self if c == column])

    def index(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            return column._j
        return list(self).index(column)

    def sort(self, cmp=None, key=None, reverse=False, order=None):
        # This makes most sense if the order in which columns should appear is supplied.
        if order and reverse is True:
            o = list(reversed(order))
        if order and reverse is False:
            o = list(order)
        if not order:
            o = _order(self, cmp, key, reverse)
        for i, row in enumerate(self._datasheet):
            # The main difficulty is modifying each row in-place,
            # since other variables might be referring to it.
            r = list(row)
            [row.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
        # Reorder the datasheet headers.
        if self._datasheet.fields is not None:
            self._datasheet.fields = [self._datasheet.fields[i] for i in o]

    def swap(self, j1, j2):
        self[j1], self[j2] = self[j2], self[j1]
        # Reorder the datasheet headers.
        if self._datasheet.fields is not None:
            self._datasheet.fields[j1], self._datasheet.fields[j2] = (
                self._datasheet.fields[j2],
                self._datasheet.fields[j1])

#--- DATASHEET COLUMN ------------------------------------------------------------------------------


class DatasheetColumn(list):

    def __init__(self, datasheet, j):
        """ A dynamic column in a Datasheet.
            If the actual column is deleted with Datasheet.columns.remove() or Datasheet.columms.pop(),
            the DatasheetColumn object will be orphaned (i.e., it is no longer part of the table).
        """
        self._datasheet = datasheet
        self._j = j

    def __getslice__(self, i, j):
        return list(list.__getitem__(self._datasheet, i)[self._j] for i in range(i, min(j, len(self._datasheet))))

    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)[self._j]

    def __setitem__(self, i, value):
        list.__getitem__(self._datasheet, i)[self._j] = value

    def __len__(self):
        return len(self._datasheet)

    def __iter__(self): # Can be put more simply but optimized for performance:
        for i in range(len(self)):
            yield list.__getitem__(self._datasheet, i)[self._j]

    def __reversed__(self):
        return reversed(list(iter(self)))

    def __repr__(self):
        return repr(list(iter(self)))

    def __gt__(self, column):
        return list(self) > list(column)

    def __lt__(self, column):
        return list(self) < list(column)

    def __ge__(self, column):
        return list(self) >= list(column)

    def __le__(self, column):
        return list(self) <= list(column)

    def __eq__(self, column):
        return list(self) == column

    def __ne__(self, column):
        return not self.__eq__(column)

    def __add__(self, column):
        return list(self) + list(column)

    def __iadd__(self, column):
        self.extend(column)

    def __contains__(self, value):
        for v in self:
            if v == value:
                return True
        return False

    def count(self, value):
        return len([True for v in self if v == value])

    def index(self, value):
        for i, v in enumerate(self):
            if v == value:
                return i
        raise ValueError("list.index(x): x not in list")

    def remove(self, value):
        """ Removes the matrix row that has the given value in this column.
        """
        for i, v in enumerate(self):
            if v == value:
                self._datasheet.pop(i)
                return
        raise ValueError("list.remove(x): x not in list")

    def pop(self, i):
        """ Removes the entire row from the matrix and returns the value at the given index.
        """
        row = self._datasheet.pop(i)
        return row[self._j]

    def sort(self, cmp=None, key=None, reverse=False):
        """ Sorts the rows in the matrix according to the values in this column,
            e.g. clicking ascending / descending on a column header in a datasheet viewer.
        """
        o = order(list(self), cmp, key, reverse)
        # Modify the table in place, more than one variable may be referencing it:
        r = list(self._datasheet)
        [self._datasheet.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]

    def insert(self, i, value, default=None):
        """ Inserts the given value in the column.
            This will create a new row in the matrix, where other columns are set to the default.
        """
        self._datasheet.insert(i, [default] * self._j + [value] + [default] * (len(self._datasheet) - self._j - 1))

    def append(self, value, default=None):
        self.insert(len(self), value, default)

    def extend(self, values, default=None):
        for value in values:
            self.insert(len(self), value, default)

    def map(self, function=lambda value: value):
        """ Applies the given function to each value in the column.
        """
        for j, value in enumerate(self):
            self[j] = function(value)

    def filter(self, function=lambda value: True):
        """ Removes the matrix rows for which function(value) in the column is not True.
        """
        i = len(self)
        for v in reversed(self):
            i -= 1
            if not function(v):
                self._datasheet.pop(i)

    def swap(self, i1, i2):
        self._datasheet.swap(i1, i2)

#---------------------------------------------------------------------------------------------------

_UID = 0


def uid():
    global _UID
    _UID += 1
    return _UID


def truncate(string, length=100):
    """ Returns a (head, tail)-tuple, where the head string length is less than the given length.
        Preferably the string is split at a space, otherwise a hyphen ("-") is injected.
    """
    if len(string) <= length:
        return string, ""
    n, words = 0, string.split(" ")
    for i, w in enumerate(words):
        if n + len(w) > length:
            break
        n += len(w) + 1
    if i == 0 and len(w) > length:
        return (w[:length - 1] + "-",
                (w[length - 1:] + " " + " ".join(words[1:])).strip())
    return (" ".join(words[:i]),
            " ".join(words[i:]))

_truncate = truncate


def pprint(datasheet, truncate=40, padding=" ", fill="."):
    """ Prints a string where the rows in the datasheet are organized in outlined columns.
    """
    # Calculate the width of each column, based on the longest field in each column.
    # Long fields can be split across different lines, so we need to check each line.
    w = [0 for column in datasheet.columns]
    R = []
    for i, row in enumerate(datasheet.rows):
        fields = []
        for j, v in enumerate(row):
            # Cast each field in the row to a string.
            # Strings that span beyond the maximum column width are wrapped.
            # Thus, each "field" in the row is a list of lines.
            lines = []
            if not isinstance(v, str):
                v = str(v)
            for v in v.splitlines():
                v = decode_utf8(v.strip())
                while v:
                    head, v = _truncate(v, truncate)
                    lines.append(head)
                    w[j] = max(w[j], len(head))
            fields.append(lines)
        R.append(fields)
    for i, fields in enumerate(R):
        # Add empty lines to each field so they are of equal height.
        n = max([len(lines) for lines in fields])
        fields = [lines + [""] * (n - len(lines)) for lines in fields]
        # Print the row line per line, justifying the fields with spaces.
        columns = []
        for k in range(n):
            for j, lines in enumerate(fields):
                s = lines[k]
                s += ((k == 0 or len(lines[k]) > 0) and fill or " ") * (w[j] - len(lines[k]))
                s += padding
                columns.append(s)
            print(" ".join(columns))
