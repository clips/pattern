#### PATTERN | DB ####################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################

import warnings
import re
import htmlentitydefs
import urllib
import csv

from cStringIO import StringIO
from codecs    import BOM_UTF8
from datetime  import datetime, timedelta
from time      import mktime
from math      import sqrt

try:
    from email.utils import parsedate_tz, mktime_tz
except:
    from email.Utils import parsedate_tz, mktime_tz

MYSQL  = "mysql"
SQLITE = "sqlite"

# Lazy import called from Database() or Database.new().
# Depending on the type of database we either import MySQLdb or SQLite.
# Note: 64-bit Python needs 64-bit MySQL, 32-bit the 32-bit version.
def _import_db(engine=SQLITE):
    global MySQLdb
    global sqlite
    if engine == MYSQL:
        import MySQLdb
        warnings.simplefilter("ignore", MySQLdb.Warning)
    if engine == SQLITE:
        try:
            # Python 2.5+
            import sqlite3 as sqlite
        except: 
            # Python 2.4 with pysqlite2
            import pysqlite2.dbapi2 as sqlite

#### DATE FUNCTIONS ##################################################################################

NOW, YEAR = "now", datetime.now().year

# Date formats can be found in the Python documentation:
# http://docs.python.org/library/time.html#time.strftime
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_formats = [
    DEFAULT_DATE_FORMAT,  # 2010-09-21 09:27:01  => SQLite + MySQL
    "%Y-%m-%dT%H:%M:%SZ", # 2010-09-20T09:27:01Z => Bing
    "%Y-%m-%d %H:%M",     # 2010-09-21 09:27
    "%Y-%m-%d",           # 2010-09-21
    "%d/%m/%Y",           # 2010/09/21
    "%d %B %Y",           # 21 September 2010
    "%B %d %Y",           # September 21 2010
    "%B %d, %Y",          # September 21, 2010
]

class DateError(Exception):
    pass

class Date(datetime):
    """ A convenience wrapper for datetime.datetime with a default string format.
    """
    format = DEFAULT_DATE_FORMAT
    def __str__(self):
        return self.strftime(self.format)
    def __repr__(self):
        return "Date(%s)" % repr(self.__str__())
    def __add__(self, time):
        d = datetime.__add__(self, time)
        return date(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, self.format)
    @property
    def timestamp(self):
        return mktime(self.timetuple()) # Seconds elapsed since 1/1/1970.

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
    if len(args) == 0 or args[0] == NOW:
        # No parameters or one parameter NOW.
        d = Date.now()
    elif len(args) == 1 \
     and (isinstance(args[0], int) \
      or  isinstance(args[0], basestring) and args[0].isdigit()):
        # One parameter, an int or string timestamp.
        d = Date.fromtimestamp(int(args[0]))
    elif len(args) == 1 and isinstance(args[0], basestring):
        # One parameter, a date string for which we guess the input format (RFC2822 or known formats).
        try: d = Date.fromtimestamp(mktime_tz(parsedate_tz(args[0])))
        except:
            for f in ("format" in kwargs and [kwargs["format"]] or []) + date_formats:
                try: d = Date.strptime(args[0], f); break
                except:
                    pass
        if d is None:
            raise DateError, "unknown date format for %s" % repr(args[0])
    elif len(args) == 2 and isinstance(args[0], basestring):
        # Two parameters, a date string and an explicit input format.
        d = Date.strptime(args[0], args[1])
    elif len(args) >= 3:
        # 3-6 parameters: year, month, day, hours, minutes, seconds.
        d = Date(*args[:7], **kwargs)
    else:
        raise DateError, "unknown date format"
    d.format = kwargs.get("format") or len(args)>7 and args[7] or Date.format
    return d

def time(days=0, seconds=0, minutes=0, hours=0, **kwargs):
    """ Returns a value that can be added to a Date object.
    """
    # Other parameters: microseconds, milliseconds, weeks.
    # There is no months-parameter since months have a variable amount of days (28-31).
    # To increase the month of a Date:
    # Date(date.year, date.month+1, date.day, format=date.format)
    return timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours, **kwargs)

#### STRING FUNCTIONS ################################################################################

def string(value, default=""):
    """ Returns the value cast to unicode, or default if it is None/empty.
    """
    # Useful for HTML interfaces.
    if value is None or value == "": # Don't do value != None because this includes 0.
        return default
    return decode_utf8(value)

def encode_utf8(string):
    """ Returns the given string as a Python byte string (if possible).
    """
    if isinstance(string, unicode):
        try: return string.encode("utf-8")
        except:
             return string
    return str(string)

def decode_utf8(string):
    """ Returns the given string as a unicode string (if possible).
    """
    if isinstance(string, str):
        try: return string.decode("utf-8")
        except:
             return string
    return unicode(string)

RE_AMPERSAND = re.compile("\&(?!\#)")           # & not followed by #
RE_UNICODE   = re.compile(r'&(#?)(x|X?)(\w+);') # &#201;

def encode_entities(string):
    """ Encodes HTML entities in the given string ("<" => "&lt;").
        For example, to display "<em>hello</em>" in a browser,
        we need to pass "&lt;em&gt;hello&lt;/em&gt;" (otherwise "hello" in italic is displayed).
    """
    if isinstance(string, (str, unicode)):
        string = RE_AMPERSAND.sub("&amp;", string)
        string = string.replace("<", "&lt;")
        string = string.replace(">", "&gt;")
        string = string.replace('"', "&quot;")
        string = string.replace("'", "&#39;")
    return string

def decode_entities(string):
    # http://snippets.dzone.com/posts/show/4569
    def replace_entity(match):
        hash, hex, name = match.group(1), match.group(2), match.group(3)
        if hash == "#":
            if hex == '' : 
                return unichr(int(name))                 # "&#38;" => "&"
            if hex in ("x","X"):
                return unichr(int('0x'+name, 16))        # "&#x0026;" = > "&"
        else:
            cp = htmlentitydefs.name2codepoint.get(name) # "&amp;" => "&"
            return cp and unichr(cp) or match.group()    # "&foo;" => "&foo;"
    if isinstance(string, (str, unicode)):
        return RE_UNICODE.subn(replace_entity, string)[0]
    return string

def _escape(value, quote=lambda string: "'%s'" % string.replace("'", "\\'")):
    """ Returns the quoted, escaped string (e.g., "'a bird\'s feathers'") for database entry.
        Anything that is not a string (e.g., an integer) is converted to string.
        Booleans are converted to "0" and "1", None is converted to "null".
    """
    # Note: use Database.escape() for MySQL/SQLITE-specific escape.
    if isinstance(value, str):
        # Strings are encoded as UTF-8.
        try: value = value.encode("utf-8")
        except:
            pass
    if isinstance(value, basestring):
        # Strings are quoted, single quotes are escaped according to the database engine.
        return quote(value)
    if isinstance(value, bool):
        # Booleans are converted to "0" or "1".
        return str(int(value))
    if isinstance(value, (int, long, float)):
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
    return value

#### LIST FUNCTIONS ##################################################################################

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
    return sorted(range(len(list)), cmp=f, reverse=reverse)
    
_order = order

def avg(list):
    return float(sum(list)) / (len(list) or 1)
    
def variance(list):
    a = avg(list)
    return sum([(x-a)**2 for x in list]) / (len(list)-1)
    
def stdev(self):
    return sqrt(variance(list))

#### SQLITE FUNCTIONS ################################################################################
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
        return ", ".join(v for v in self if isinstance(v, basestring))

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
        
#### DATABASE ########################################################################################

class DatabaseConnectionError(Exception): 
    pass

class Database:
    
    class Tables(dict):
        # Table objects are lazily constructed when retrieved.
        # This saves time because each table executes a metadata query when constructed.
        def __init__(self, db, *args, **kwargs):
            dict.__init__(self, *args, **kwargs); self.db=db
        def __getitem__(self, k):
            if dict.__getitem__(self, k) is None:
                dict.__setitem__(self, k, Table(name=k, database=self.db))
            return dict.__getitem__(self, k)

    def __init__(self, name, host="localhost", user="root", password="", type=SQLITE, unicode=True):
        """ A collection of tables stored in an SQLite or MySQL database.
            If the database, host, user or password does not exist, raises DatabaseConnectionError.
        """
        _import_db(type)
        self.type = type
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self._connection = None
        self.connect(unicode)
        # Table names are available in the Database.tables dictionary,
        # table objects as attributes (e.g. Database.table_name).
        q = self.type==SQLITE and "select name from sqlite_master where type='table';" or "show tables;"
        self.tables = Database.Tables(self)
        for name, in self.execute(q):
            if not name.startswith(("sqlite_",)):
                self.tables[name] = None
        # The SQL syntax of the last query is kept in cache.
        self._query = None
        # Persistent relations between tables, stored as (table1, table2, key1, key2, join) tuples.
        self.relations = []

    @classmethod
    def new(self, name, host="localhost", user="root", password="", type=SQLITE, unicode=True):
        """ Creates and returns a new database with the given name.
            If the database already exists, simply returns it.
        """
        _import_db(type)
        if type == MYSQL:
            connection = MySQLdb.connect(host, user, password)
            cursor = connection.cursor()
            cursor.execute("create database if not exists `%s`;" % name)
            cursor.close()
            connection.close()
        if type == SQLITE:
            connection = sqlite.connect(name)
            connection.close()
        return self(name, host, user, password, type, unicode)
        
    def connect(self, unicode=True):
        # Connections for threaded applications work differently,
        # see http://tools.cherrypy.org/wiki/Databases 
        # (have one Database object for each thread).
        if self._connection: 
            return
        try: 
            if self.type == SQLITE:
                self._connection = sqlite.connect(self.name)
                # Aggregate functions (for grouping rows):
                self._connection.create_aggregate("first", 1, sqlite_first)
                self._connection.create_aggregate("last", 1, sqlite_last)
                self._connection.create_aggregate("group_concat", 1, sqlite_group_concat)
                # Date functions:
                self._connection.create_function("year", 1, sqlite_year)
                self._connection.create_function("month", 1, sqlite_month)
                self._connection.create_function("day", 1, sqlite_day)
                self._connection.create_function("hour", 1, sqlite_hour)
                self._connection.create_function("minute", 1, sqlite_minute)
                self._connection.create_function("second", 1, sqlite_second)
            if self.type == MYSQL:
                # Map field type INTEGER to int (not long(), e.g., 1L).
                # You can't use UNSIGNED in this case, however.
                format = MySQLdb.converters.conversions.copy()
                format[MySQLdb.constants.FIELD_TYPE.TIMESTAMP] = str # DATE => str, yyyy-mm-dd hh:mm:ss
                format[MySQLdb.constants.FIELD_TYPE.LONG]      = int # INTEGER => int
                format[MySQLdb.constants.FIELD_TYPE.LONGLONG]  = int
                self._connection = MySQLdb.connect(self.host, self.user, self.password, self.name, use_unicode=unicode, conv=format)
                self._connection.autocommit(False)
                if unicode: 
                    self._connection.set_character_set("utf8")
        except Exception, e:
            raise DatabaseConnectionError, e
            
    def disconnect(self):
        self.tables.clear()
        self._query = None
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
        if k in self.tables: 
            return self.tables[k]
        if k in self.__dict__: 
            return self.__dict__[k]
        raise AttributeError, "'Database' object has no attribute '%s'" % k

    def __len__(self):
        return len(self.tables)
    def __iter__(self):
        return iter(self.tables)
    def __getitem__(self, k):
        return self.tables[k]
    
    @property
    def query(self):
        return self._query
    
    def execute(self, SQL, commit=False):
        """ Executes the given SQL query and return a list of rows.
            With commit=True, automatically commits insert/update/delete changes.
        """
        self._query = SQL
        if not SQL:
            return # MySQL doesn't like empty queries.
        #print SQL
        cursor = self._connection.cursor()   
        cursor.execute(SQL)
        rows = list(cursor.fetchall())
        cursor.close()
        if commit is not False:
            self._connection.commit()
        return rows
        
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
        
    def create(self, table, fields, encoding="utf-8"):
        """ Creates a new table with the given fields.
            The given list of fields must contain values returned from the field() command.
        """
        encoding = self.type == MYSQL and " default charset=" + encoding.replace("utf-8", "utf8") or ""
        autoincr = self.type == MYSQL and " auto_increment" or " autoincrement"
        a, b = [], []
        for f in fields:
            f = list(f) + [STRING, None, False, True][len(f)-1:]
            # Table fields:
            # ['`id` integer not null primary key auto_increment']
            a.append("`%s` %s%s%s%s" % (
                f[0] == STRING and f[0]() or f[0], 
                f[1],
                f[4] is False and " not null" or "",
                f[2] is not None and " default "+f[2] or "",
                f[3] == PRIMARY and " primary key%s" % ("", autoincr)[f[1]==INTEGER] or ""))
            # Table field indices.
            # Note: there is no MySQL "create index if not exists", so we just overwrite.
            if f[3] in (UNIQUE, True):
                b.append("create %sindex `%s_%s` on `%s` (`%s`);" % (
                    f[3] == UNIQUE and "unique " or "", table, f[0], table, f[0]))
        self.execute("create table if not exists `%s` (%s)%s;" % (table, ", ".join(a), encoding))
        self.execute("\n".join(b), commit=True)
        self.tables[table] = None # lazy loading
        return self.tables[table]
        
    def drop(self, table):
        """ Removes the table with the given name.
        """
        if table in self.tables:
            self.tables[table].database = None
            self.tables.pop(table)
            self.execute("drop table `%s`;" % table, commit=True)
        
    def link(self, table1, key1, table2, key2, join="left"):
        """ Defines a relation between two tables in the database.
            When executing a table query, fields from the linked table will also be available
            (to disambiguate between field names, use table.field_name).
        """
        if isinstance(table1, Table): 
            table1 = table1.name
        if isinstance(table2, Table): 
            table2 = table2.name
        self.relations.append((table1, key1, table2, key2, join))

    def __repr__(self):
        return "Database(name=%s, host=%s, tables=%s)" % (
            repr(self.name), 
            repr(self.host), 
            repr(self.tables.keys()))
        
    def __delete__(self):
        try: 
            self.disconnect()
        except:
            pass

#### FIELD ###########################################################################################

class _String(str):
    # The STRING constant can be called with a length when passed to field(),
    # for example field("language", type=STRING(2), default="en", index=True).
    def __new__(self):
        return str.__new__(self, "string")
    def __call__(self, length=100):
        return "varchar(%s)" % (length>255 and 255 or (length<1 and 1 or length))

# Field type.
# Note: SQLite string fields do not impose a string limit.
# Unicode strings have more characters than actually displayed (e.g. "&#9829;").
# Boolean fields are stored as tinyint(1), returns int 0 or 1. Compare using: bool(field_value) is True.
STRING, INTEGER, FLOAT, TEXT, BLOB, BOOLEAN, DATE  = \
    _String(), "integer", "float", "text", "blob", "boolean", "date"

INT, BOOL = INTEGER, BOOLEAN

# Field index.
PRIMARY = "primary"
UNIQUE  = "unique"

# DATE default.
NOW = "current_timestamp"

#--- FIELD- ------------------------------------------------------------------------------------------

def field(name, type=STRING, default=None, index=False, null=True):
    """ Returns a table field definition that can be passed to Database.create().
        The column can be indexed by setting index to True, PRIMARY or UNIQUE.
        Primary key number columns are always auto-incremented.
    """
    if type == STRING:
        type = STRING()
    if type == FLOAT:
        type = "real"
    if type == BOOLEAN:
        type = "tinyint(1)"
    if type == DATE:
        type = "timestamp"; default=NOW
    if str(index) in "01":
        index = bool(int(index))
    if str(null) in "01":
        null = bool(int(null))
    return (name, type, default, index, null)

def primary_key(name="id"):
    """ Returns an auto-incremented integer primary key field named "id".
    """
    return field(name, INTEGER, index=PRIMARY, null=False)
    
pk = primary_key

#--- FIELD SCHEMA ------------------------------------------------------------------------------------

class Schema:
    
    def __init__(self, name, type, index=False, default=None, null=True, extra=None):
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
        if isinstance(index, basestring):
            if index.lower().startswith("pri"): 
                index = PRIMARY
            if index.lower().startswith("uni"): 
                index = UNIQUE
            if index in ("0", "1", ""):
                index = index == "1"
        self.name    = name               # Field name.
        self.type    = type               # Field type: INTEGER | FLOAT | STRING | TEXT | BLOB | DATE.
        self.length  = length             # Field length for STRING.
        self.default = default or None    # Default value.
        self.index   = index              # PRIMARY | UNIQUE | True | False.
        self.null    = null in ("YES", 0) # True or False
        self.extra   = extra or None
        
    def __repr__(self):
        return "Schema(name=%s, type=%s, default=%s, index=%s, null=%s)" % (
            repr(self.name), 
            repr(self.type),
            repr(self.default),
            repr(self.index),
            repr(self.null))

#### TABLE ###########################################################################################

ALL = "*"

class Table:
    
    def __init__(self, name, database):
        """ A collection of rows consisting of one or more fields (i.e., table columns) 
            of a certain type (i.e., strings, numbers).
        """
        self.database = database
        self.name     = name
        self.fields   = [] # List of field names (i.e., column names).
        self.schema   = {} # Dictionary of (field, Schema)-items.
        self.default  = {} # Default values for Table.insert().
        self.primary_key = None
        # Retrieve table column names.
        # Table column names are available in the Table.fields list.
        # Table column names should not contain unicode because they can also be function parameters.
        # Table column names should avoid " ", ".", "(" and ")".
        # The primary key column is stored in Table.primary_key.
        if self.db.type == MYSQL:
            q = "show columns from `%s`;" % self.name
        if self.db.type == SQLITE:
            q = "pragma table_info(`%s`);" % self.name
            i = self.db.execute("pragma index_list(`%s`)" % self.name) # look up indices
            i = dict(((v[1].replace(self.name+"_", "", 1), v[2]) for v in i))
        for f in self.db.execute(q):
            # [name, type, index, default, null, extra]
            if self.db.type == MYSQL:
                f = [f[0], f[1], f[3], f[4], f[2], f[5]] 
            if self.db.type == SQLITE:
                f = [f[1], f[2], f[5], f[4], f[3], ""]
                f[2] = f[2] == 1 and "pri" or (f[0] in i and ("1","uni")[int(i[f[0]])] or "")
            name = string(f[0])
            self.fields.append(name)
            self.schema[name] = Schema(*f)
            if self.schema[name].index == PRIMARY:
                self.primary_key = name

    @property
    def db(self):
        return self.database
    
    @property
    def pk(self):
        return self.primary_key
    
    @property
    def count(self):
        """ Yields the number of rows in the table.
        """
        return int(self.db.execute("select count(*) from `%s`;" % self.name)[0][0])
        
    def __len__(self):
        return self.count
    def __iter__(self):
        return iter(self.rows)
    def __getitem__(self, i):
        return self.rows[i]

    def abs(self, field):
        return abs(self.name, field)

    def all(self):
        """ Returns a list of all the rows in the table.
        """
        return self.db.execute("select * from `%s`;" % self.name)
    
    @property
    def rows(self):
        return self.all()

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
        return self.db.execute(q)         

    def query(self, *args, **kwargs):
        """ Returns a Query object that can be used to construct complex table queries.
        """
        return Query(self, *args, **kwargs)

    def _insert_id(self):
        # Retrieves the primary key value of the last inserted row.
        if self.db.type == MYSQL:
            return self.db._connection.insert_id() or None
        if self.db.type == SQLITE:
            return self.db.execute("select last_insert_rowid();") or None

    def insert(self, *args, **kwargs):
        """ Inserts a new row from the given field parameters.
        """
        # Table.insert(name="Taxi", age=2, type="cat")
        # Table.insert({"name":"Fricassée", "age":2, "type":"cat"})
        commit = kwargs.pop("commit", True) # As fieldname, use abs(Table.name, "commit").
        if len(args) > 0:
            kwargs = args[0]
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
        if len(args) > 0:
            kwargs = args[0]
        kv = ", ".join("`%s`=%s" % (k, self.db.escape(v)) for k, v in kwargs.items())
        q  = "update `%s` set %s where %s;" % (self.name, kv, 
            not isinstance(id, Group) and cmp(self.primary_key, id, "=", self.db.escape) \
             or id.SQL(escape=self.db.escape))
        self.db.execute(q, commit)
        
    def remove(self, id, commit=True):
        """ Removes the row which primary key equals the given id.
        """
        # Table.delete(1)
        # Table.delete(ALL)
        # Table.delete(all(("type","cat"), ("age",15,">")))
        q = "delete from `%s` where %s" % (self.name, 
            not isinstance(id, Group) and cmp(self.primary_key, id, "=", self.db.escape) \
             or id.SQL(escape=self.db.escape))
        self.db.execute(q, commit)
    
    append, edit, delete = insert, update, remove
    
    def drop(self):
        self.db.drop(self.name)
        
    @property
    def xml(self):
        return xml(self)

    def datasheet(self):
        return Datasheet(rows=self.rows, fields=[(f, self.schema[f].type) for f in self.fields])

    def __repr__(self):
        return "Table(name=%s, count=%s, database=%s)" % (
            repr(self.name), 
            repr(self.count),
            repr(self.db.name))

#### QUERY ###########################################################################################

#--- QUERY SYNTAX -----------------------------------------------------------------------------------

BETWEEN, LIKE, IN = \
    "between", "like", "in"

sql_functions = \
    "first|last|count|min|max|sum|avg|stdev|group_concat|" \
    "year|month|day|hour|minute|second|" \
    "length|lower|upper|substr|replace|trim|round|random|rand" \
    "stftime|date_format"

def abs(table, field):
    """ For a given <fieldname>, returns the absolute <tablename>.<fieldname>.
        This is useful when constructing queries with relations to other tables.
    """
    def _format(s):
        if not "." in s:
            # Field could be wrapped in a function: year(date) => year(table.date).
            p = s.endswith(")") and re.match(r"^"+sql_functions+r"\(", s) or None
            i = p and len(p.group(0)) or -1
            return "%s%s.%s" % (s[:i+1], table, s[i+1:])
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
    if isinstance(value, basestring) and (value.startswith(("*","%")) or value.endswith(("*","%"))):
        if comparison in ("=", "i=", "==", LIKE):
            return "%s like %s" % (field, escape(value.replace("*","%")))
        if comparison in ("!=", "<>"):
            return "%s not like %s" % (field, escape(value.replace("*","%")))
    # cmp("name", "markov") => "name" like 'markov'" (case-insensitive).
    if isinstance(value, basestring):
        if comparison == "i=":
            return "%s like %s" % (field, escape(value))
    # cmp("type", ("cat", "dog"), "!=") => "type not in ('cat','dog')".
    # cmp("amount", (10, 100), ":") => "amount between 10 and 100".
    if isinstance(value, (list, tuple)):
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
            return "%s in %s" % (field, escape(value))
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

#--- QUERY FILTER ------------------------------------------------------------------------------------

AND, OR = "and", "or"

def filter(field, value, comparison="="):
    return (field, value, comparison)

class Group(list):
    
    def __init__(self, *args, **kwargs):
        """ A list of SQL WHERE filters combined with AND/OR logical operator.
        """
        list.__init__(self, args)
        self.operator = kwargs.get("operator", AND)
    
    def SQL(self, **kwargs):
        """ For example, filter for small pets with tails or wings
            (which is not the same as small pets with tails or pets with wings):
            >>> Group(
            >>>     filter("type", "pet"),
            >>>     filter("weight", (4,6), ":"),
            >>>     Group(
            >>>         filter("tail", True),
            >>>         filter("wing", True), operator=OR))
            Yields: 
            "type='pet' and weight between 4 and 6 and (tail=1 or wing=1)"
        """
        # Remember to pass the right escape() function as optional parameter.
        a = []
        for filter in self:
            # Traverse subgroups recursively.
            if isinstance(filter, Group):
                a.append("(%s)" % filter.SQL(**kwargs))
                continue
            # Convert filter() to string with cmp() - see above.
            if isinstance(filter, (list, tuple)):
                a.append(cmp(*filter, **kwargs))
                continue
            raise TypeError, "Group can contain other Group or filter(), not %s" % type(filter)
        return (" %s " % self.operator).join(a)
        
    sql = SQL

def all(*args): # AND
    return Group(*args, **dict(operator=AND))
    
def any(*args): # OR
    return Group(*args, **dict(operator=OR))
    
# From a GET-query dict:
# all(*dict.items())

# filter() value can also be a Query with comparison=IN.

#--- QUERY -------------------------------------------------------------------------------------------

# Relations:
INNER = "inner" # The rows for which there is a match in both tables (same as join=None).
LEFT  = "left"  # All rows from this table, with field values from the related table when possible.
RIGHT = "right" # All rows from the related table, with field values from this table when possible.
FULL  = "full"  # All rows form both tables.

def relation(table, key1, key2, join=LEFT):
    return (table, key1, key2, join)
    
rel = relation

# Sorting:
ASCENDING  = "asc"
DESCENDING = "desc"

# Grouping:
FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV, CONCATENATE = \
    "first", "last", "count", "max", "min", "sum", "avg", "stdev", "group_concat"

class Query:
    
    id, cache = 0, {}
    
    def __init__(self, table, fields=ALL, filters=[], relations=[], sort=None, order=ASCENDING, group=None, function=FIRST, range=None):
        """ A selection of rows from the given table, filtered by any() and all() constraints.
        """
        # Table.query(ALL, filters=any(("type","cat"), ("type","dog")) => cats and dogs.
        # Table.query(("type", "name")), group="type", function=COUNT) => all types + amount per type.
        # Table.query(("name", "types.has_tail"), relations=[("types","type","id")]) => links type to types.id.
        Query.id += 1
        filters = Group(*filters, **dict(operator=isinstance(filters, Group) and filters.operator or AND))
        self._id       = Query.id
        self._table    = table
        self.fields    = fields    # A field name, list of field names or ALL.
        self.filters   = filters   # A group of filter() objects.
        self.relations = relations # A list of relation() objects. 
        self.sort      = sort      # A field name, list of field names or field index for sorting.
        self.order     = order     # ASCENDING or DESCENDING.
        self.group     = group     # A field name, list of field names or field index for folding.
        self.function  = function  # FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV or CONCATENATE (or list).
        self.range     = range     # A (index1, index2)-tuple. The first row in the table is 0.
        
    @property
    def table(self):
        return self._table

    def __len__(self):
        return len(self.rows)
    def __iter__(self):
        return iter(self.rows)
    def __getitem__(self, i):
        return self.rows[i]

    def SQL(self):
        """ Yields the SQL syntax of the query, which can be passed to Database.execute().
            The SQL string will be cached for faster reuse.
        """
        if self._id in Query.cache: 
            return Query.cache[self._id]
        # Construct the SELECT clause from Query.fields.
        # With a GROUPY BY clause, fields not used for grouping are wrapped in the given function.
        g = not isinstance(self.group, (list, tuple)) and [self.group] or self.group
        g = [abs(self._table.name, f) for f in g if f is not None]
        fields = not isinstance(self.fields, (list, tuple)) and [self.fields] or self.fields
        fields = abs(self._table.name, fields)
        fields = self.function and g and [f in g and f or "%s(%s)" % (self.function, f) for f in fields] or fields
        q = []
        q.append("select %s" % ", ".join(fields))
        # Construct the FROM clause from Query.relations.
        # Table relations defined on the database are taken into account,
        # but overridden by relations defined on the query.
        q.append("from `%s`" % self._table.name)
        relations = {}
        for table, key1, key2, join in (rel(*r) for r in self.relations):
            table = isinstance(table, Table) and table.name or table
            relations[table] = (key1, key2, join)
        for table1, key1, table2, key2, join in self._table.db.relations:
            if table1 == self._table.name:
                relations.setdefault(table2, (key1, key2, join))
            if table2 == self._table.name:
                relations.setdefault(table1, (key1, key2, join==LEFT and RIGHT or (join==RIGHT and LEFT or join)))
        for (table, (key1, key2, join)) in relations.items():
            q.append("%sjoin `%s`" % (join and join+" " or "", table))
            q.append("on %s=%s" % (abs(self._table.name, key1), abs(self._table.db[table].name, key2)))
        # Construct the WHERE clause from Query.filters.SQL().
        # Use the database's escape function and absolute field names.
        if len(self.filters) > 0:
            q.append("where %s" % self.filters.SQL(escape=self._table.db.escape, table=self._table.name))
        # Construct the ORDER BY clause from Query.sort and Query.order.
        # Construct the GROUP BY clause from Query.group.
        for clause, value in (("order", self.sort), ("group", self.group)):
            if isinstance(value, basestring) and value != "": 
                q.append("%s by %s" % (clause, abs(self._table.name, value)))
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                q.append("%s by %s" % (clause, ", ".join(abs(self._table.name, value))))
            elif isinstance(value, int):
                q.append("%s by %s" % (clause, abs(self._table.name, self._table.fields[value])))
            if self.sort and clause == "order":
                q.append("%s" % self.order or ASCENDING)
        # Construct the LIMIT clause from Query.range.
        if self.range:
            q.append("limit %s, %s" % (str(self.range[0]), str(self.range[1])))
        q = " ".join(q) + ";"
        # Cache the SQL-string for faster retrieval.
        if len(Query.cache) > 100: 
            Query.cache.clear()
        Query.cache[self._id] = q
        return q
        
    sql = SQL
    
    def update(self):
        """ Clears the cached SQL string (e.g., when you change the query parameters).
        """
        Query.cache.pop(self._id)
    
    def execute(self):
        """ Executes the query and returns the matching rows from the table.
            Each field is handled by Table.format (e.g. by default entities are encoded).
        """
        return self._table.db.execute(self.SQL())

    def all(self):
        return self.execute()

    @property
    def rows(self):
        return self.all()
        
    @property
    def xml(self):
        return xml(self)

    def __repr__(self):
        return "Query(sql=%s)" % repr(self.SQL())

#### OBJECT ###########################################################################################
# A representation of data based on a table in the database.
# The render() method can be overridden to output data in a certain format (e.g., HTML for a web app).

class Object:
    
    def __init__(self, database, table, schema=[]):
        """ A representation of data.
            Object.schema and Object.render() should be overridden in a subclass.
        """
        self.database = database
        self._table   = isinstance(table, Table) and table.name or table
        self.schema   = schema # A list of table fields - see field().
    
    @property
    def db(self):
        return self.database
    
    @property
    def table(self):
        # If it doesn't exist, create the table from Object.schema.
        if not self._table in self.db:
            self.setup() 
        self.table = self.db[self._table]
        return self.table

    def setup(self, overwrite=False):
        """ Creates the database table from Object.schema, optionally overwriting the old table.
        """
        if overwrite:
            self.db.drop(self._table)
        if not self._table in self.db:
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
    def default(self, *args, **kwargs):
        return self.render(*args, **kwargs)
        
    default.exposed = True

#### XML PARSER #######################################################################################

def xml_format(a):
    """ Returns the given attribute (string, int, float, bool, None) as a quoted unicode string.
    """
    if isinstance(a, basestring):
        return "\"%s\"" % encode_entities(a)
    if isinstance(a, bool):
        return "\"%s\"" % int(a)
    if isinstance(a, (int, long)):
        return "\"%s\"" % a
    if isinstance(a, float):
        return "\"%s\"" % round(a, 5)
    if isinstance(a, type(None)):
        return "\"\""

def xml(rows):
    """ Returns the rows in the given Table or Query as an XML-string, for example:
        <table name="pets", fields="id, name, type", count="2">
            <schema>
                <field name="id", type="integer", index="primary", null="0" />
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
        root, table = "table", rows
    if isinstance(rows, Query): 
        root, table = "query", rows.table
    # Strip the table name from absolute field names.
    # Fields from related tables will keep the table name prefix.
    # This could cause problems when importing, we end up with a field name that has a "."
    # (see parse_xml() below).
    fields = [xml_format(f.replace(table.name+".", "", 1)).strip("\"") for f in rows.fields]
    try:
        # Replace "*" with the actual field names.
        i = fields.index(ALL)
        fields = fields[:i] + table.fields + fields[i+1:]
    except:
        pass
    xml = []
    xml.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
    # <table name="" fields="" count="">
    # <query table="" fields="" count="">
    xml.append("<%s %s=%s fields=\"%s\" count=\"%s\">" % (
        root, root!="table" and "table" or "name", xml_format(table.name), ", ".join(fields), len(rows)))
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
        # <field name="" type="" length="" default="" index="" null="" extra="" />
        xml.append("\t\t<field name=%s type=%s%s%s%s%s%s />" % (
            xml_format(f),
            xml_format(s.type),
            s.length is not None and " length=%s" % xml_format(s.length) or "",
            s.default is not None and " default=%s" % xml_format(s.default) or "",
            s.index is not False and " index=%s" % xml_format(s.index) or "",
            s.null is not True and " null=%s" % xml_format(s.null) or "",
            s.extra is not None and " extra=%s" % xml_format(s.extra) or ""))
    xml.append("\t</schema>")
    xml.append("\t<rows>")
    # <rows>
    for r in rows:
        # <row field="value" />
        xml.append("\t\t<row %s />" % " ".join("%s=%s" % (k, xml_format(v)) for k, v in zip(fields, r)))
    xml.append("\t</rows>")
    xml.append("</%s>" % root)
    xml = "\n".join(xml)
    xml = encode_utf8(xml)
    return xml

def parse_xml(database, xml):
    """ Creates a new table in the database from the given XML-string.
        The XML must be in the format generated by Table.xml.
        If the table already exists, raises an ImportError.
    """
    def _attr(node, attribute, default=""):
        return node.getAttribute(attribute) or default
    # parseString() will decode entities, no need for decode_entities().
    from xml.dom.minidom import parseString
    dom = parseString(encode_utf8(xml))
    a = dom.getElementsByTagName("table")
    b = dom.getElementsByTagName("query")
    if len(a) > 0:
        table = _attr(a[0], "name", "")
    if len(b) > 0:
        table = _attr(b[0], "table", "")
    # Parse field information (i.e., field name, field type, etc.)
    fields, schema, rows = [], [], []
    for f in dom.getElementsByTagName("field"):
        fields.append(_attr(f, "name"))
        schema.append(field(
            name = _attr(f, "name"),
            type = _attr(f, "type") == STRING and STRING(int(_attr(f, "length", 255))) or _attr(f, "type"),
         default = _attr(f, "default", None),
           index = _attr(f, "index", False),
            null = _attr(f, "null", True)
        ))
        # Integer primary key is always auto-increment.
        # The id's in the new table will differ from those in the XML.
        if _attr(f, "index") == PRIMARY and _attr(f, "type") == INTEGER:
            fields.pop()
    # Parse row data.
    for r in dom.getElementsByTagName("row"):
        rows.append(dict((f, _attr(r, f, None)) for f in fields))
    # Create table if not exists and insert rows.
    if database.connected is False:
        database.connect()
    if table in database:
        raise ImportError, "database table '%s' already exists" % table
    database.create(table, fields=schema)
    for r in rows:
        database[table].insert(r, commit=False)
    database.commit()
    return database[table]

#### DATASHEET ########################################################################################

#--- CSV ----------------------------------------------------------------------------------------------

def csv_header_encode(field, type=STRING):
    # csv_header_encode("age", INTEGER) => "age (INTEGER)".
    return "%s (%s)" % (encode_utf8(field or ""), type.upper())
    
def csv_header_decode(s):
    # csv_header_decode("age (INTEGER)") => ("age", INTEGER).
    p = "STRING|INTEGER|FLOAT|TEXT|BLOB|BOOLEAN|DATE"
    p = re.match(r"(.*?) \(("+p+")\)", s)
    return p and (string(p.group(1), default=None), p.group(2).lower()) or (None, None)

class CSV(list):

    def __init__(self, rows=[], fields=None):
        """ A list of lists that can be exported as a comma-separated text file.
        """
        self.__dict__["fields"] = fields # List of (name, type)-tuples, with type = STRING, INTEGER, etc.
        self.extend(rows)

    def save(self, path, separator=",", encoder=lambda j,v:v, headers=False):
        """ Exports the table to a unicode text file at the given path.
            Rows in the file are separated with a newline.
            Columns in a row are separated with the given separator (by default, comma).
            For data types other than string, int, float, bool or None, a custom string encoder can be given.
        """
        # csv.writer will handle str, int, float and bool:
        s = StringIO()
        w = csv.writer(s, delimiter=separator)
        if headers and self.fields is not None:
            w.writerows([[csv_header_encode(name, type) for name, type in self.fields]])
        w.writerows([[encode_utf8(encoder(j,v)) for j, v in enumerate(row)] for row in self])
        f = open(path, "wb")
        f.write(BOM_UTF8)
        f.write(s.getvalue())
        f.close()

    @classmethod
    def load(self, path, separator=",", decoder=lambda j,v:v, headers=False):
        """ Returns a table from the data in the given text file.
            Rows are expected to be separated by a newline. 
            Columns are expected to be separated by the given separator (by default, comma).
            Strings will be converted to int, float, bool, date or None if headers are parsed.
            For other data types, a custom string decoder can be given.
        """
        # Date objects are saved and loaded as strings, but it is easy to convert these back to dates:
        # - set a DATE field type for the column,
        # - or do Table.columns[x].map(lambda s: date(s))
        data = open(path, "rb").read().lstrip(BOM_UTF8)
        data = StringIO(data)
        data = [row for row in csv.reader(data, delimiter=separator)]
        if headers:
            fields = [csv_header_decode(field) for field in data.pop(0)]
        else:
            fields = []
        if not fields:
            # Cast fields using the given decoder (by default, all strings).
            data = [[decoder(j, v) for j, v in enumerate(row)] for row in data]
        else:
            # Cast fields to their defined field type (STRING, INTEGER, ...)
            for i, row in enumerate(data):
                for j, v in enumerate(row):
                    type = fields[j][1]
                    if row[j] == "None":
                        row[j] = decoder(j, None)
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
                        row[j] = decoder(j, v)
        return self(rows=data, fields=fields)

#--- DATASHEET ----------------------------------------------------------------------------------------

class Datasheet(CSV):
    
    def __init__(self, rows=[], fields=None):
        """ A matrix of rows and columns, where each row and column can be retrieved as a list.
            Values can be any kind of Python object.
        """
        self.__dict__["_rows"] = DatasheetRows(self)
        self.__dict__["_columns"] = DatasheetColumns(self)
        self.__dict__["_m"] = 0 # Number of columns per row, see Datasheet.insert().
        CSV.__init__(self, rows, fields)
    
    def _get_rows(self):
        return self._rows
    def _set_rows(self, rows):
        # Datasheet.rows property can't be set, except in special case Datasheet.rows += row.
        if isinstance(rows, DatasheetRows) and rows._datasheet == self:
            self._rows = rows; return
        raise AttributeError, "can't set attribute"
    rows = property(_get_rows, _set_rows)
    
    def _get_columns(self):
        return self._columns
    def _set_columns(self, columns):
        # Datasheet.columns property can't be set, except in special case Datasheet.columns += column.
        if isinstance(columns, DatasheetColumns) and columns._datasheet == self:
            self._columns = columns; return
        raise AttributeError, "can't set attribute"
    columns = cols = property(_get_columns, _set_columns)
    
    def __getattr__(self, k):
        """ Columns can be retrieved by field name, e.g., Datasheet.date.
        """
        #print "Datasheet.__getattr__", k
        if k in self.__dict__:
            return self.__dict__[k]
        for i, f in enumerate(f[0] for f in self.__dict__["fields"]):
            if f == k: 
                return self.__dict__["_columns"][i]
        raise AttributeError, "'Datasheet' object has no attribute '%s'" % k
        
    def __setattr__(self, k, v):
        """ Columns can be set by field name, e.g., Datasheet.date = [...].
        """
        #print "Datasheet.__setattr__", k
        if k in self.__dict__:
            self.__dict__[k] = v; return
        for i, f in enumerate(f[0] for f in self.__dict__["fields"]):
            if f == k: 
                self.__dict__["_columns"].__setitem__(i, v); return
        raise AttributeError, "'Datasheet' object has no attribute '%s'" % k
    
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
            raise TypeError, "Datasheet indices must be int or tuple"
    
    def __getitem__(self, index):
        """ Returns an item, row or slice from the matrix.
            For Datasheet[i], returns the row at the given index.
            For Datasheet[i,j], returns the value in row i and column j.
        """
        if isinstance(index, int):
            # Datasheet[i] => row i.
            return list.__getitem__(self, index)
        if isinstance(index, tuple):
            i, j = index
            if isinstance(i, slice):
                # Datasheet[i1:i2,j1:j2] => columns j1-j2 from rows i1-i2.
                # Datasheet[i1:i2,j] => column j from rows i1-i2.
                return [row[j] for row in list.__getitem__(self, i)]
            # Datasheet[i,j1:j2] => columns j1-j2 from row i.
            # Datasheet[i,j] => item from column j in row i.
            return list.__getitem__(self, i)[j]
        raise TypeError, "Datasheet indices must be int or tuple"

    def __getslice__(self, i, j):
        return list.__getslice__(self, i, j)
            
    def __delitem__(self, index):
        self.pop(index)

    # datasheet1 = datasheet2 + datasheet3
    # datasheet1 = [[...],[...]] + datasheet2
    # datasheet1 += datasheet2
    def __add__(self, datasheet):
        m = self.copy(); m.extend(datasheet); return m
    def __radd__(self, datasheet):
        m = Datasheet(datasheet); m.extend(self); return m
    def __iadd__(self, datasheet):
        self.extend(datasheet); return self

    def insert(self, i, row, default=None):
        """ Inserts the given row into the matrix.
            Missing columns at the end (right) will be filled with the default value.
        """
        try:
            # Copy the row (fast + safe for generators and DatasheetColumns).
            row = [v for v in row]
        except:
            raise TypeError, "Datasheet.insert(x): x must be list"
        list.insert(self, i, row)
        m = max((len(self) > 1 and self._m or 0, len(row)))
        if len(row) < m:
            row.extend([default] * (m-len(row)))
        if self._m < m:
            # The given row might have more columns than the rows in the matrix.
            # Performance takes a hit when these rows have to be expanded:
            for row in self:
                if len(row) < m:
                    row.extend([default] * (m-len(row)))
        self.__dict__["_m"] = m
        
    def append(self, row, default=None, _m=None):
        self.insert(len(self), row, default)
    def extend(self, rows, default=None):
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
        for i, f in enumerate(function):
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
                function[i] = lambda a: sum([x for x in a if x is not None])
            if f == AVG: 
                function[i] = lambda a: avg([x for x in a if x is not None])
            if f == STDEV:
                function[i] = lambda a: stdev([x for x in a if x is not None])
            if f == CONCATENATE:
                function[i] = lambda a: ", ".join(decode_utf8(x) for x in a if x is not None)
        J = j
        # Map unique values in column j to a list of rows that contain this value.
        g = {}; [g.setdefault(key(v), []).append(i) for i, v in enumerate(self.columns[j])]
        # Map unique values in column j to a sort index in the new, grouped list.
        o = [(g[v][0], v) for v in g]
        o = dict([(v, i)  for i, (ii,v) in enumerate(sorted(o))])
        # Create a list of rows with unique values in column j,
        # applying the group function to the other columns.
        u = [None] * len(o)
        for v in g:
            # List the column values for each group row.
            u[o[v]] = [[list.__getitem__(self, i)[j] for i in g[v]] for j in range(self._m)]
            # Apply the group function to each row, except the unique value in column j.
            u[o[v]] = [function[j](column) for j, column in enumerate(u[o[v]])]
            u[o[v]][J] = v#list.__getitem__(self, i)[J]
        return Datasheet(rows=u)
                
    def map(self, function=lambda item: item):
        """ Applies the given function to each item in the matrix.
        """
        for i, row in enumerate(self):
            for j, item in enumerate(row):
                row[j] = function(item)

    def slice(self, i, j, n, m):
        """ Returns a new Datasheet starting at row i and column j and spanning n rows and m columns.
        """
        return Datasheet(rows=[list.__getitem__(self, i)[j:j+m] for i in range(i, i+n)])

    def copy(self, rows=ALL, columns=ALL):
        """ Returns a new Datasheet from a selective list of row and/or column indices.
        """
        if rows == ALL and columns == ALL:
            return Datasheet(rows=self)
        if rows == ALL:
            return Datasheet(rows=zip(*(self.columns[j] for j in columns)))
        if columns == ALL:
            return Datasheet(rows=(self.rows[i] for i in rows))
        z = zip(*(self.columns[j] for j in columns))
        return Datasheet(rows=(z[i] for i in rows))

def flip(datasheet):
    return Datasheet(rows=datasheet.columns)

#--- DATASHEET ROWS -----------------------------------------------------------------------------------
# Datasheet.rows mimics the operations on Datasheet:

class DatasheetRows(list):
    
    def __init__(self, datasheet):
        self._datasheet = datasheet

    def __setitem__(self, i, row):
        self._datasheet.pop(i)
        self._datasheet.insert(i, row)
    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)
    def __delitem__(self, i):
        self.pop(i)
    def __len__(self):
        return len(self._datasheet)
    def __iter__(self):
        for i in xrange(len(self)): yield list.__getitem__(self._datasheet, i)
    def __repr__(self):
        return repr(self._datasheet)
    def __add__(self, row):
        raise TypeError, "unsupported operand type(s) for +: 'Datasheet.rows' and '%s'" % row.__class__.__name__
    def __iadd__(self, row):
        self.append(row); return self

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

#--- DATASHEET COLUMNS --------------------------------------------------------------------------------

class DatasheetColumns(list):
    
    def __init__(self, datasheet):
        self._datasheet = datasheet
        self._cache  = {} # Keep a reference to DatasheetColumn objects generated with Datasheet.columns[j].
                          # This way we can unlink them when they are deleted.

    def __setitem__(self, j, column):
        self.pop(j)
        self.insert(j, column)
    def __getitem__(self, j):
        if j < 0: j += len(self) # DatasheetColumns[-1]
        if j >= len(self): 
            raise IndexError, "list index out of range"
        return self._cache.setdefault(j, DatasheetColumn(self._datasheet, j))
    def __delitem__(self, j):
        self.pop(j)
    def __len__(self):
        return len(self._datasheet) > 0 and len(self._datasheet[0]) or 0
    def __iter__(self):
        for i in xrange(len(self)): yield self.__getitem__(i)
    def __repr__(self):
        return repr(list(iter(self)))    
    def __add__(self, column):
        raise TypeError, "unsupported operand type(s) for +: 'Datasheet.columns' and '%s'" % column.__class__.__name__
    def __iadd__(self, column):
        self.append(column); return self

    def insert(self, j, column, default=None):
        """ Inserts the given column into the matrix.
            Missing rows at the end (bottom) will be filled with the default value.
        """
        try: column = [v for v in column]
        except:
            raise TypeError, "Datasheet.columns.insert(x): x must be list"
        column = column + [default] * (len(self._datasheet) - len(column))
        if len(column) > len(self._datasheet):
            self._datasheet.extend([[None]] * (len(column)-len(self._datasheet)))
        for i, row in enumerate(self._datasheet):
            row.insert(j, column[i])
        self._datasheet.__dict__["_m"] += 1 # Increase column count.

    def append(self, column, default=None):
        self.insert(len(self), column, default)
    def extend(self, columns, default=None):
        for column in columns: 
            self.insert(len(self), column, default)
    
    def remove(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            self.pop(column._j); return
        raise ValueError, "list.remove(x): x not in list"
    
    def pop(self, j):
        column = list(self[j]) # Return a list copy.
        for row in self._datasheet: 
            row.pop(j)
        # At one point a DatasheetColumn object was created with Datasheet.columns[j].
        # It might still be in use somewhere, so we unlink it from the datasheet:
        self._cache[j]._datasheet = Datasheet(rows=[[v] for v in column])
        self._cache[j]._j = 0
        self._cache.pop(j)
        for j in range(j+1, len(self)+1):
            if j in self._cache:
                # Shift the DatasheetColumn objects on the right to the left.
                self._cache[j-1] = self._cache.pop(j)
                self._cache[j-1]._j = j-1
        self._datasheet.__dict__["_m"] -= 1 # Decrease column count.
        return column

    def count(self, column):
        return len([True for c in self if c == column])
    
    def index(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            return column._j
        raise ValueError, "list.index(x): x not in list"
    
    def sort(self, cmp=None, key=None, reverse=False, order=None):
        # This makes most sense if the order in which columns should appear is supplied.
        o = order and order or _order(self, cmp, key, reverse)
        for i, row in enumerate(self._datasheet):
            # The main difficulty is modifying each row in-place,
            # since other variables might be referring to it.
            r=list(row); [row.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
    
    def swap(self, j1, j2):
        self[j1], self[j2] = self[j2], self[j1]

#--- DATASHEET COLUMN ---------------------------------------------------------------------------------

class DatasheetColumn(list):
    
    def __init__(self, datasheet, j):
        """ A dynamic column in a Datasheet.
            If the actual column is deleted with Datasheet.columns.remove() or Datasheet.columms.pop(),
            the DatasheetColumn object will be orphaned (i.e. it is no longer part of the Table).
        """
        self._datasheet = datasheet
        self._j = j
    
    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)[self._j]
    def __setitem__(self, i, value):
        list.__getitem__(self._datasheet, i)[self._j] = value
    def __len__(self):
        return len(self._datasheet)
    def __iter__(self): # Can be put more simply but optimized for performance:
        for i in xrange(len(self)): yield list.__getitem__(self._datasheet, i)[self._j]
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
        return isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet and column._j == self._j
    def __ne__(self, column):
        return not self.__eq__(column)
    def __add__(self, value):
        raise TypeError, "unsupported operand type(s) for +: 'Datasheet.columns[x]' and '%s'" % column.__class__.__name__
    def __iadd__(self, value):
        self.append(value); return self
    def __contains__(self, value):
        for v in self:
            if v == value: return True
        return False
    
    def count(self, value):
        return len([True for v in self if v == value])
        
    def index(self, value):
        for i, v in enumerate(self):
            if v == value: 
                return i
        raise ValueError, "list.index(x): x not in list"

    def remove(self, value):
        """ Removes the matrix row that has the given value in this column.
        """
        for i, v in enumerate(self):
            if v == value:
                self._datasheet.pop(i); return
        raise ValueError, "list.remove(x): x not in list"
        
    def pop(self, i):
        """ Removes the entire row from the matrix and returns the value at the given index.
        """
        row = self._datasheet.pop(i); return row[self._j]

    def sort(self, cmp=None, key=None, reverse=False):
        """ Sorts the rows in the matrix according to the values in this column,
            e.g. clicking ascending / descending on a column header in a datasheet viewer.
        """
        o = order(list(self), cmp, key, reverse)
        # Modify the table in place, more than one variable may be referencing it:
        r=list(self._datasheet); [self._datasheet.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
        
    def insert(self, i, value, default=None):
        """ Inserts the given value in the column.
            This will create a new row in the matrix, where other columns are set to the default.
        """
        self._datasheet.insert(i, [default]*self._j + [value] + [default]*(len(self._datasheet)-self._j-1))
        
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
            
    def swap(self, i1, i2):
        self._datasheet.swap(i1, i2)
        
    def _set_unique(self, b):
        if b is True and self._uindex is None:
            d = []
            self._uindex = {}
            for i, v in enumerate(self):
                if v in self._uindex:
                    d.append(i)
                else:
                    self._uindex[v] = i
            for i in d:
                self.pop(i)
    
    def _get_unique(self, b):
        return self._uindex is not None

#-----------------------------------------------------------------------------------------------------

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
        return (w[:length-1] + "-", 
                w[length-1:] + " " + " ".join(words[1:]))
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
            head, tail = _truncate(decode_utf8(v), truncate)
            lines = []
            lines.append(head)
            w[j] = max(w[j], len(head))
            while len(tail) > 0:
                head, tail = _truncate(tail, truncate)
                lines.append(head)
                w[j] = max(w[j], len(head))
            fields.append(lines)
        R.append(fields)
    for i, fields in enumerate(R):
        # Add empty lines to each field so they are of equal height.
        n = max([len(lines) for lines in fields])
        fields = [lines+[""] * (n-len(lines)) for lines in fields]
        # Print the row line per line, justifying the fields with spaces.
        for k in range(n):
            for j, lines in enumerate(fields):
                s  = lines[k]
                s += ((k==0 or len(lines[k]) > 0) and fill or " ") * (w[j] - len(lines[k])) 
                s += padding
                print s,
            print


