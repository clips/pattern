#### PATTERN | DB ####################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################

import re
import htmlentitydefs
import urllib

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
    if engine == SQLITE:
        try:
            # Python 2.5+
            import sqlite3 as sqlite
        except: 
            # Python 2.4 with pysqlite2
            import pysqlite2.dbapi2 as sqlite

#### STRING FUNCTIONS ################################################################################

def string(value, default=""):
    """ Returns the value cast to unicode string, or default if it is None/empty.
    """
    if value is None or value == "": # Don't do value != None because this includes 0.
        return default
    if isinstance(value, str):
        try:
            return value.decode("utf-8")
        except:
            return value
    return unicode(value)

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
                return unichr(int('0x'+name, 16))        # ""&#x0026;"" = > "&"
        else:
            cp = htmlentitydefs.name2codepoint.get(name) # "&amp;" => "&"
            return cp and unichr(cp) or match.group()    # "&foo;" => "&foo;"
    if isinstance(string, (str, unicode)):
        return RE_UNICODE.subn(replace_entity, string)[0]
    return string

def escape(value, quote=lambda string: "'%s'" % string.replace("'", "\\'")):
    """ Returns the quoted, escaped string (e.g., "'a bird\'s feathers'") for database entry.
        Anything that is not a string (e.g., an integer) is converted to string.
        Booleans are converted to "0" and "1", None is converted to "null".
    """
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
    if isinstance(value, type(None)):
        # None is converted to NULL.
        return "null"
    if isinstance(value, Query):
        # A Query is converted to "("+Query.SQL()+")" (=subquery).
        return "(%s)" % value.SQL().rstrip(";")
    return value

#### SQLITE AGGREGATE FUNCTIONS ######################################################################
# Functions missing in pysqlite2, these are created each Database.connect().
        
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
                self._connection.create_aggregate("first", 1, sqlite_first)
                self._connection.create_aggregate("last", 1, sqlite_last)
                self._connection.create_aggregate("group_concat", 1, sqlite_group_concat)
            if self.type == MYSQL:
                self._connection = MySQLdb.connect(self.host, self.user, self.password, self.name, use_unicode=unicode)
                self._connection.autocommit(False)
                if unicode: 
                    self._connection.set_character_set("utf8")
        except:
            raise DatabaseConnectionError
            
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
        print ">>>", SQL
        self._query = SQL
        if not SQL:
            return # MySQL doesn't like empty queries.
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
                return "'%s'" % self._connection.escape_string(string)
            if self.type == SQLITE:
                return "'%s'" % string.replace("'", "''")
        return escape(value, quote)
        
    def create(self, table, fields, encoding="utf-8"):
        """ Creates a new table with the given fields.
            The given list of fields must contain values returned from the field() command.
        """
        encoding = self.type == MYSQL and " default charset=" + encoding.replace("utf-8", "utf8") or ""
        autoincr = self.type == MYSQL and " auto_increment" or " autoincrement"
        a, b = [], []
        for f in fields:
            f = list(f) + [STRING, None, False, True][len(f)-1:]
            # Table fields.
            a.append("`%s` %s%s%s%s" % (
                f[0] == STRING and f[0]() or f[0], 
                f[1],
                f[4] is False and " not null" or "",
                f[2] is not None and " default "+f[2] or "",
                f[3] == PRIMARY and " primary key%s" % ("", autoincr)[f[1]==INTEGER] or ""))
            # Table field indices.
            if f[3] in (UNIQUE, True):
                #b.append("create %sindex if not exists `%s_%s` on `%s` (`%s`);" % ( # XXX
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
    # for example field("language", typeSTRING(2), default="en", index=True).
    def __new__(self):
        return str.__new__(self, "string")
    def __call__(self, length=100):
        return "varchar(%s)" % (length>255 and 255 or (length<1 and 1 or length))

# Field type.
# Note: SQLite string fields do not impose a string limit.
# Unicode strings have more characters than actually displayed (e.g. "&#9829;").
# Boolean fields are stored as tinyint(1), returns int 0 or 1. Compare using bool(field_value) == True.
STRING, INTEGER, FLOAT, TEXT, BLOB, BOOLEAN, DATE  = \
    _String(), "integer", "float", "text", "blob", "boolean", "date"

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
        self.fields   = []
        self.schema   = {}
        self.default  = {} # Default values for Table.insert().
        self.primary_key = None
        # Retrieve table column names.
        # Table column names are available in the Table.fields list.
        # Table column names should not contain unicode because they can also be function parameters.
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
            name = str(f[0])
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
        """ For a given <fieldname>, returns the absolute <tablename>.<fieldname>.
            This is useful when constructing queries with relations to other tables.
        """
        if not isinstance(field, (list, tuple)):
            return "." in field and field or "%s.%s" % (self.name, field)
        return ["." in x and x or "%s.%s" % (self.name, x) for x in field]

    def all(self):
        """ Returns a list of all the rows in the table.
        """
        return self.db.execute("select * from `%s`;" % self.name)
    
    @property
    def rows(self):
        return self.all()

    @property
    def datasheet(self):
        return Datasheet(rows=self.rows, headers=self._table.abs(self.fields))

    def filter(self, fields=ALL, **kwargs):
        """ Returns the rows that match the given constraints (using equals + AND):
        """
        # Table.filter(("name","age"), id=1)
        # Table.filter(ALL, type=("cat","dog")) => "cat" OR "dog"
        # Table.filter(ALL, type="cat", name="Taxi") => "cat" AND "Taxi"
        fields = isinstance(fields, (list, tuple)) and ", ".join(fields) or fields or ALL
        q = " and ".join(cmp(k, v, "=", self.db.escape) for k, v in kwargs.items())
        q = "select %s from `%s` where %s;" % (fields, self.name, q)
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

    def insert(self, **kwargs):
        """ Inserts a new row from the given field parameters.
        """
        # Table.insert(name="Taxi", age=2, type="cat")
        # Table.insert(**{"name":"Taxi", "age":2, "type":"cat"})
        commit = kwargs.pop("commit", True) # As fieldname, use abs("commit").
        if len(self.default) > 0:
            kwargs.update(self.default)
        k = ", ".join(kwargs.keys())
        v = ", ".join(self.db.escape(v) for v in kwargs.values())
        q = "insert into `%s` (%s) values (%s);" % (self.name, k, v)
        self.db.execute(q, commit)
        return self._insert_id()
        
    def update(self, value, field=PRIMARY, comparison="=", **kwargs):
        """ Updates the row with the given id.
        """
        # Table.update(1, age=3)
        # Table.update("Taxi", field="name", **{"age":3})
        commit = kwargs.pop("commit", True) # As fieldname, use abs("commit").
        if field == PRIMARY:
            field = self.primary_key
        kv = ", ".join("%s=%s" % (k, self.db.escape(v)) for k, v in kwargs.items())
        q  = cmp(field, value, comparison, self.db.escape)
        q  = "update `%s` set %s where %s;" % (self.name, kv, q)
        self.db.execute(q, commit)
        
    def remove(self, value, field=PRIMARY, comparison="=", commit=True):
        """ Removes the row which primary key equals the given id.
        """
        # Table.delete("cat", field="type")
        # Table.delete(ALL)
        if field == PRIMARY:
            field = self.primary_key
        q = cmp(field, value, comparison, self.db.escape)
        q = "delete from `%s` where %s" % (self.name, q)
        self.db.execute(q, commit)
    
    append, edit, delete = insert, update, remove
    
    def drop(self):
        self.db.drop(self.name)
        
    @property
    def xml(self):
        return xml(self)
    
    def __repr__(self):
        return "Table(name=%s, count=%s, database=%s)" % (
            repr(self.name), 
            repr(self.count),
            repr(self.db.name))

#### QUERY ###########################################################################################

#--- QUERY SYNTAX -----------------------------------------------------------------------------------

BETWEEN, LIKE, IN = \
    "between", "like", "in"

def cmp(field, value, comparison="=", escape=lambda v: escape(v), table=""):
    """ Returns an SQL WHERE comparison string using =, i=, !=, >, <, >=, <= or BETWEEN.
        Strings may contain wildcards (*) at the start or at the end.
        A list or tuple of values can be given when using =, != or BETWEEN.
    """
    if table: field = "%s.%s" % (table, field)
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

#--- QUERY FILTER ------------------------------------------------------------------------------------

AND, OR = "and", "or"

def filter(field, value, comparison="="):
    return (field, value, comparison)

class Group(list):
    
    def __init__(self, *args, **kwargs):
        """ A list of SQL WHERE filters combined with AND/OR logical operator, for example:
            Filter for small pets with tails or wings (!= small pets with tails or pets with wings).
            Group(
                filter("type", "pet"),
                filter("weight", (4,6), ":"),
                Group(
                    filter("tail", True),
                    filter("wing", True), operator=OR
                )
            )
        """
        list.__init__(self, args)
        self.operator = kwargs.get("operator", AND)
    
    def SQL(self, **kwargs):
        # "type='pet' and weight between 4 and 6 and (tail=1 or wing=1)"
        a = [isinstance(f, Group) and "(%s)" % f.SQL(escape) or cmp(*f, **kwargs) for f in self]
        a = (" %s " % self.operator).join(a)
        return a
        
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
        self.function  = function  # FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV or CONCATENATE.
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
        g = [self._table.abs(f) for f in g if f is not None]
        fields = not isinstance(self.fields, (list, tuple)) and [self.fields] or self.fields
        fields = self._table.abs(fields)
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
            q.append("on %s=%s" % (self._table.abs(key1), self._table.db[table].abs(key2)))
        # Construct the WHERE clause from Query.filters.SQL().
        # Use the database's escape function and absolute field names.
        if len(self.filters) > 0:
            q.append("where %s" % self.filters.SQL(escape=self._table.db.escape, table=self._table.name))
        # Construct the ORDER BY clause from Query.sort and Query.order.
        # Construct the GROUP BY clause from Query.group.
        for clause, value in (("order", self.sort), ("group", self.group)):
            if isinstance(value, basestring) and value != "": 
                q.append("%s by %s" % (clause, self._table.abs(value)))
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                q.append("%s by %s" % (clause, ", ".join(self._table.abs(value))))
            elif isinstance(value, int):
                q.append("%s by %s" % (clause, self._table.abs(self._table.fields[value])))
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
    def datasheet(self):
        return Datasheet(rows=self.rows, headers=self._table.abs(self.fields))

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

#### XML ##############################################################################################

def xml_format(a):
    """ Returns the given attribute (string, int, float, bool, None) as a quoted string.
    """
    if isinstance(a, str):
        try: a = a.encode("utf-8")
        except:
            pass
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
    schema = table.schema
    fields = [f.replace(table.name+".", "", 1) for f in rows.fields]
    xml = []
    xml.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
    # <table name="" fields="" count="">
    # <query table="" fields="" count="">
    xml.append("<%s %s=\"%s\" fields=\"%s\" count=\"%s\">" % (
        root, root!="table" and "table" or "name", table.name, ", ".join(fields), len(rows)))
    # <schema>
    # Field information is retrieved from the (related) table schema.
    # If the XML is imported as a Table, the related fields become part of it.
    xml.append("\t<schema>")
    for f in fields:
        if f not in schema:
            s = f.split(".")
            s = table.db[s[0]].schema[s[-1]]
        else:
            s = schema[f]
        # <field name="" type="" length="" default="" index="" null="" extra="" />
        xml.append("\t\t<field name=%s type=%s%s%s%s%s%s />" % (
            xml_format(f),
            xml_format(s.type),
            s.length  is not None  and " length=%s"  % xml_format(s.length)  or "",
            s.default is not None  and " default=%s" % xml_format(s.default) or "",
            s.index   is not False and " index=%s"   % xml_format(s.index)   or "",
            s.null    is     False and " null=%s"    % xml_format(s.null)    or "",
            s.extra   is not None  and " extra=%s"   % xml_format(s.extra)   or ""
        ))
    xml.append("\t</schema>")
    # <rows>
    xml.append("\t<rows>")
    for r in rows:
        # <row field="value" />
        xml.append("\t\t<row %s />" % " ".join("%s=%s" % (k, xml_format(v)) for k, v in zip(fields, r)))
    xml.append("\t</rows>")
    xml.append("</%s>" % root)
    return "\n".join(xml)

def parse_xml(database, xml):
    """ Creates a new table in the database from the given XML-string.
        The XML must be in the format generated by Table.xml.
        If the table alreadt exists, raises an ImportError.
    """
    from xml.dom.minidom import parseString
    def attr(node, attribute, default=""):
        return node.getAttribute(attribute) or default
    dom = parseString(xml)
    a = dom.getElementsByTagName("table")
    b = dom.getElementsByTagName("query")
    if len(a) > 0:
        table = attr(a[0], "name", "")
    if len(b) > 0:
        table = attr(b[0], "table", "")
    fields = []
    schema = []
    rows   = []
    for f in dom.getElementsByTagName("field"):
        fields.append(attr(f, "name").encode("utf-8"))
        schema.append(field(
            name = attr(f, "name"),
            type = attr(f, "type") == STRING and STRING(int(attr(f, "length", 255))) or attr(f, "type"),
         default = attr(f, "default", None),
           index = attr(f, "index", False),
            null = attr(f, "null", True)
        ))
        # Integer primary key is always auto-increment (disregard in rows).
        # The id's in the new table will differ from those in the XML.
        if attr(f, "index") == PRIMARY and attr(f, "type") == INTEGER:
            fields.pop()
    for r in dom.getElementsByTagName("row"):
        rows.append(dict((f, attr(r, f, None)) for f in fields))
    # Create table if not exists and insert rows.
    if database.connected is False:
        database.connect()
    if table in database:
        raise ImportError, "database already has a table named '%s'" % table
    database.create(table, fields=schema)
    for r in rows:
        database[table].insert(commit=False, **r)
    database.commit()
    return database[table]
