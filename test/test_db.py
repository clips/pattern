# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))
import datetime
import unittest

from pattern import db

# To test MySQL, you need MySQLdb and a username + password with rights to create a database.
HOST, PORT, USERNAME, PASSWORD = \
    "localhost", 3306, "root", "root"

DB_MYSQL  = DB_MYSQL_EXCEPTION  = None
DB_SQLITE = DB_SQLITE_EXCEPTION = None

try:
    DB_MYSQL = db.Database(
            type = db.MYSQL,
            name = "pattern_unittest_db", 
            host = HOST,
            port = PORT,
        username = USERNAME,
        password = PASSWORD)
except ImportError, e: 
    # "No module named MySQLdb"
    DB_MYSQL_EXCEPTION = None
except Exception, e:
    DB_MYSQL_EXCEPTION = e
    
try:
    DB_SQLITE = db.Database(
            type = db.SQLITE,
            name = "pattern_unittest_db",
            host = HOST,
            port = PORT,
        username = USERNAME,
        password = PASSWORD)
except Exception, e:
    DB_SQLITE_EXCEPTION = e

#-----------------------------------------------------------------------------------------------------

class TestUnicode(unittest.TestCase):
    
    def setUp(self):
        # Test data with different (or wrong) encodings.
        self.strings = (
            u"ünîcøde",
            u"ünîcøde".encode("utf-16"),
            u"ünîcøde".encode("latin-1"),
            u"ünîcøde".encode("windows-1252"),
             "ünîcøde",
            u"אוניקאָד"
        )
        
    def test_decode_utf8(self):
        # Assert unicode.
        for s in self.strings:
            self.assertTrue(isinstance(db.decode_utf8(s), unicode))
        print "pattern.db.decode_utf8()"

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(db.encode_utf8(s), str))
        print "pattern.db.encode_utf8()"
        
    def test_string(self):
        # Assert string() with default for "" and None.
        for v, s in ((True, u"True"), (1, u"1"), (1.0, u"1.0"), ("", u"????"), (None, u"????")):
            self.assertEqual(db.string(v, default="????"), s)
        print "pattern.db.string()"

#-----------------------------------------------------------------------------------------------------

class TestEntities(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_encode_entities(self):
        # Assert HTML entity encoder (e.g., "&" => "&&amp;")
        for a, b in (
          ("&#201;", "&#201;"), 
          ("&", "&amp;"), 
          ("<", "&lt;"), 
          (">", "&gt;"), 
          ('"', "&quot;"),
          ("'", "&#39;")):
            self.assertEqual(db.encode_entities(a), b)
        print "pattern.db.encode_entities()"
            
    def test_decode_entities(self):
        # Assert HMTL entity decoder (e.g., "&amp;" => "&")
        for a, b in (
          ("&#38;", "&"),
          ("&amp;", "&"),
          ("&#x0026;", "&"),
          ("&#160;", u"\xa0"),
          ("&foo;", "&foo;")):
            self.assertEqual(db.decode_entities(a), b)
        print "pattern.db.decode_entities()"

#-----------------------------------------------------------------------------------------------------

class TestDate(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_date(self):
        # Assert string input and default date formats.
        for s in (
          "2010-09-21 09:27:01",
          "2010-09-21T09:27:01Z",
          "2010-09-21T09:27:01+0000",
          "2010-09-21 09:27",
          "2010-09-21",
          "21/09/2010",
          "21 September 2010",
          "September 21 2010",
          "September 21, 2010",
          1285054021):
            v = db.date(s)
            self.assertEqual(v.format, "%Y-%m-%d %H:%M:%S")
            self.assertEqual(v.year,   2010)
            self.assertEqual(v.month,  9)
            self.assertEqual(v.day,    21)
        # Assert NOW.
        for v in (db.date(), db.date(db.NOW)):
            self.assertEqual(v.year,  datetime.datetime.now().year)
            self.assertEqual(v.month, datetime.datetime.now().month)
            self.assertEqual(v.day,   datetime.datetime.now().day)
        self.assertEqual(db.date().year, db.YEAR)
        # Assert integer input.
        v1 = db.date(2010, 9, 21, format=db.DEFAULT_DATE_FORMAT)
        v2 = db.date(2010, 9, 21, 9, 27, 1, 0, db.DEFAULT_DATE_FORMAT)
        v3 = db.date(2010, 9, 21, hour=9, minute=27, second=01, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(str(v1), "2010-09-21 00:00:00")
        self.assertEqual(str(v2), "2010-09-21 09:27:01")
        self.assertEqual(str(v3), "2010-09-21 09:27:01")
        # Assert DateError for other input.
        self.assertRaises(db.DateError, db.date, None)
        print "pattern.db.date()"
            
    def test_format(self):
        # Assert custom input formats.
        v = db.date("2010-09", "%Y-%m")
        self.assertEqual(str(v), "2010-09-01 00:00:00")
        self.assertEqual(v.year, 2010)
        # Assert custom output formats.
        v = db.date("2010-09", "%Y-%m", format="%Y-%m")
        self.assertEqual(v.format, "%Y-%m")
        self.assertEqual(str(v), "2010-09")
        self.assertEqual(v.year, 2010)
        # Assert strftime() for date < 1900.
        v = db.date(1707, 4, 15)
        self.assertEqual(str(v), "1707-04-15 00:00:00")
        self.assertRaises(ValueError, lambda: v.timestamp)
        print "pattern.db.Date.__str__()"

    def test_timestamp(self):
        # Assert Date.timestamp.
        v = db.date(2010, 9, 21, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(v.timestamp, 1285020000)
        print "pattern.db.Date.timestamp"
        
    def test_time(self):
        # Assert Date + time().
        v = db.date("2010-09-21 9:27:00")
        v = v - db.time(days=1, hours=1, minutes=1, seconds=1)
        self.assertEqual(str(v), "2010-09-20 08:25:59")
        print "pattern.db.time()"

#-----------------------------------------------------------------------------------------------------

class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_order(self):
        # Assert a list of indices in the order as when the given list is sorted.
        v = [3,1,2]
        self.assertEqual(db.order(v), [1,2,0])
        self.assertEqual(db.order(v, reverse=True), [0,2,1])
        self.assertEqual(db.order(v, cmp=lambda a,b: a-b), [1,2,0])
        self.assertEqual(db.order(v, key=lambda i:i), [1,2,0])
        print "pattern.db.order()"

    def test_avg(self):
        # Assert (1+2+3+4) / 4 = 2.5.
        self.assertEqual(db.avg([1,2,3,4]), 2.5)
        print "pattern.db.avg()"
        
    def test_variance(self):
        # Assert 2.5.
        self.assertEqual(db.variance([1,2,3,4,5]), 2.5)
        print "pattern.db.variance()"
        
    def test_stdev(self):
        # Assert 2.429.
        self.assertAlmostEqual(db.stdev([1,5,6,7,6,8]), 2.429, places=3)
        print "pattern.db.stdev()"
    
    def test_sqlite_functions(self):
        # Assert year(), month(), day(), ..., first(), last() and group_concat() for SQLite.
        v = "1707-04-15 01:02:03"
        self.assertEqual(db.sqlite_year(v),   1707)
        self.assertEqual(db.sqlite_month(v),  4)
        self.assertEqual(db.sqlite_day(v),    15)
        self.assertEqual(db.sqlite_hour(v),   1)
        self.assertEqual(db.sqlite_minute(v), 2)
        self.assertEqual(db.sqlite_second(v), 3)
        # Aggregate functions.
        for f, a, b in (
          (db.sqlite_first, [1,2,3], 1),
          (db.sqlite_last,  [1,2,3], 3),
          (db.sqlite_group_concat, [1,2,3], "1,2,3")):
            f = f()
            for x in a:
                f.step(x)
            self.assertEqual(f.finalize(), b)
        print "pattern.db.sqlite_year()"
        print "pattern.db.sqlite_month()"
        print "pattern.db.sqlite_day()"
        print "pattern.db.sqlite_hour()"
        print "pattern.db.sqlite_minute()"
        print "pattern.db.sqlite_second()"
        print "pattern.db.sqlite_first()"
        print "pattern.db.sqlite_last()"
        print "pattern.db.sqlite_group_concat()"

#-----------------------------------------------------------------------------------------------------

class TestDatabase(unittest.TestCase):
    
    db, type = None, None
    
    def setUp(self):
        pass
    
    def tearDown(self):
        for table in self.db:
            self.db.drop(table)
        
    def test_escape(self):
        # Assert str, unicode, int, long, float, bool and None field values.
        for v, s in (
          (  "a", "'a'"),
          ( u"a", "'a'"),
          (    1, "1"),
          (   1L, "1"),
          (  1.0, "1.0"),
          ( True, "1"),
          (False, "0"),
          ( None, "null")):
            self.assertEqual(db._escape(v), s)
        # Assert date.   
        v = db.date("1707-04-15")
        self.assertEqual(db._escape(v), "'1707-04-15 00:00:00'")
        # Assert current date.
        v = "current_timestamp"
        self.assertEqual(db._escape(v), "current_timestamp")
        # Assert subquery.
        v = self.db.create("dummy", fields=[db.pk()])
        v = v.query()
        self.assertEqual(db._escape(v), "(select dummy.* from `dummy`)")
        # Assert MySQL and SQLite quotes.
        if self.db.type == db.MYSQL:
            self.assertEqual(self.db.escape("'"), "'\\''")
        if self.db.type == db.SQLITE:
            self.assertEqual(self.db.escape("'"), "''''")
        print "pattern.db._escape()"

    def test_database(self):
        # Assert Database properties.
        self.assertTrue(self.db.type       == self.type)
        self.assertTrue(self.db.name       == "pattern_unittest_db")
        self.assertTrue(self.db.host       == HOST)
        self.assertTrue(self.db.port       == PORT)
        self.assertTrue(self.db.username   == USERNAME)
        self.assertTrue(self.db.password   == PASSWORD)
        self.assertTrue(self.db.tables     == {})
        self.assertTrue(self.db.relations  == [])
        self.assertTrue(self.db.connected  == True)
        self.db.disconnect()
        self.assertTrue(self.db.connected  == False)
        self.assertTrue(self.db.connection == None)
        self.db.connect()
        print "pattern.db.Database(type=%s)" % self.type.upper()
        
    def test_create_table(self):
        # Assert Database.create() new table.
        v = self.db.create("products", fields=[
            db.primary_key("pid"),
            db.field("name", db.STRING, index=True, optional=False),
            db.field("price", db.FLOAT)
        ])
        # Assert that the last query executed is stored.
        if self.db.type == db.SQLITE:
            self.assertEqual(self.db.query, "pragma table_info(`products`);")
        if self.db.type == db.MYSQL:
            self.assertEqual(self.db.query, "show columns from `products`;")
        # Assert new Table exists in Database.tables.
        self.assertTrue(isinstance(v, db.Table))
        self.assertTrue(len(self.db)             == 1)
        self.assertTrue(v.pk                     == "pid")
        self.assertTrue(v.fields                 == ["pid", "name", "price"])
        self.assertTrue(self.db[v.name]          == v)
        self.assertTrue(self.db.tables[v.name]   == v)
        self.assertTrue(getattr(self.db, v.name) == v)
        # Assert Database._field_SQL subroutine for Database.create().
        for field, sql1, sql2 in (
          (db.primary_key("pid"), 
           ("`pid` integer not null primary key auto_increment", None),
           ("`pid` integer not null primary key autoincrement", None)),
          (db.field("name", db.STRING, index=True, optional=False), 
           ("`name` varchar(100) not null", "create index `products_name` on `products` (`name`);"),
           ("`name` varchar(100) not null", "create index `products_name` on `products` (`name`);")),
          (db.field("price", db.INTEGER),
           ("`price` integer null", None),
           ("`price` integer null", None))):
            if self.db.type == db.MYSQL:
                self.assertEqual(self.db._field_SQL(self.db["products"].name, field), sql1)
            if self.db.type == db.SQLITE:
                self.assertEqual(self.db._field_SQL(self.db["products"].name, field), sql2)
        # Assert TableError if table already exists.
        self.assertRaises(db.TableError, self.db.create, "products")
        # Assert remove table.
        self.db.drop("products")
        self.assertTrue(len(self.db) == 0)
        print "pattern.db.Database.create()"

class TestCreateMySQLDatabase(unittest.TestCase):
    def runTest(self):
        if DB_MYSQL_EXCEPTION: 
            raise DB_MYSQL_EXCEPTION
            
class TestCreateSQLiteDatabase(unittest.TestCase):
    def runTest(self):
        if DB_SQLITE_EXCEPTION: 
            raise DB_SQLITE_EXCEPTION

class TestDeleteMySQLDatabase(unittest.TestCase):
    def runTest(self):
        DB_MYSQL._delete()
        
class TestDeleteSQLiteDatabase(unittest.TestCase):
    def runTest(self):
        DB_SQLITE._delete()

class TestMySQLDatabase(TestDatabase):
    db, type = DB_MYSQL, db.MYSQL
    
class TestSQLiteDatabase(TestDatabase):
    db, type = DB_SQLITE, db.SQLITE

#-----------------------------------------------------------------------------------------------------

class TestSchema(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def test_string(self):
        # Assert callable String.
        v1 = db._String()
        v2 = db._String()(0)
        v3 = db._String()(200)
        v4 = db._String()(300)
        self.assertEqual(v1, "string")
        self.assertEqual(v2, "varchar(1)")
        self.assertEqual(v3, "varchar(200)")
        self.assertEqual(v4, "varchar(255)")
        
    def test_field(self):
        # Assert field() return value with different optional parameters.
        #                                                         NAME     TYPE            DEFAULT INDEX      OPTIONAL
        for kwargs, f in (
          (dict(name="id",    type=db.INT),                      ("id",    "integer",      None,   False,     True)),
          (dict(name="id",    type=db.INT,    index=db.PRIMARY), ("id",    "integer",      None,   "primary", True)),
          (dict(name="id",    type=db.INT,    index=db.UNIQUE),  ("id",    "integer",      None,   "unique",  True)),
          (dict(name="id",    type=db.INT,    index="0"),        ("id",    "integer",      None,   False,     True)),
          (dict(name="id",    type=db.INT,    index="1"),        ("id",    "integer",      None,   True,      True)),
          (dict(name="id",    type=db.INT,    index=True),       ("id",    "integer",      None,   True,      True)),
          (dict(name="id",    type=db.INT,    default=0),        ("id",    "integer",      0,      False,     True)),
          (dict(name="name",  type=db.STRING),                   ("name",  "varchar(100)", None,   False,     True)),
          (dict(name="name",  type=db.STRING, optional=False),   ("name",  "varchar(100)", None,   False,     False)),
          (dict(name="name",  type=db.STRING, optional="0"),     ("name",  "varchar(100)", None,   False,     False)),
          (dict(name="name",  type=db.STRING(50)),               ("name",  "varchar(50)",  None,   False,     True)),
          (dict(name="price", type=db.FLOAT,  default=0),        ("price", "real",         0,      False,     True)),
          (dict(name="show",  type=db.BOOL),                     ("show",  "tinyint(1)",   None,   False,     True)),
          (dict(name="show",  type=db.BOOL,   default=True),     ("show",  "tinyint(1)",   True,   False,     True)),
          (dict(name="show",  type=db.BOOL,   default=False),    ("show",  "tinyint(1)",   False,  False,     True)),
          (dict(name="date",  type=db.DATE),                     ("date",  "timestamp",    "now",  False,     True)),
          (dict(name="date",  type=db.DATE,   default=db.NOW),   ("date",  "timestamp",    "now",  False,     True)), 
          (dict(name="date",  type=db.DATE,   default="1999-12-31 23:59:59"), 
                                                                 ("date", "timestamp", "1999-12-31 23:59:59", False, True))):
            self.assertEqual(db.field(**kwargs), f)
        # Assert primary_key() return value.
        self.assertTrue(db.primary_key() == db.pk() == ("id", "integer", None, "primary", False))
        print "pattern.db.field()"
    
    def test_schema(self):
        now1 =  "current_timestamp"
        now2 = "'CURRENT_TIMESTAMP'"
        # Assert Schema (= table schema in a uniform way across database engines).
        #   NAME    TYPE            DEFAULT INDEX  OPTIONAL
        for args, v in (
          (("id",   "integer",      None,   "pri", False), ("id",   db.INT,    None,   db.PRIMARY, False, None)),
          (("id",   "integer",      None,   "uni", False), ("id",   db.INT,    None,   db.UNIQUE,  False, None)),
          (("id",   "int",          None,   "yes", True),  ("id",   db.INT,    None,   True,       True,  None)),
          (("id",   "real",         None,   "mul", True),  ("id",   db.FLOAT,  None,   True,       True,  None)),
          (("id",   "real",         None,   "1",   True),  ("id",   db.FLOAT,  None,   True,       True,  None)),
          (("id",   "double",       None,   "0",   True),  ("id",   db.FLOAT,  None,   False,      True,  None)),
          (("id",   "double",       0,      False, False), ("id",   db.FLOAT,  0,      False,      False, None)),
          (("text", "varchar(10)",  "?",    False, True),  ("text", db.STRING, "?",    False,      True,  10)),
          (("text", "char(20)",     "",     False, True),  ("text", db.STRING, None,   False,      True,  20)),
          (("text", "text",         None,   False, True),  ("text", db.TEXT,   None,   False,      True,  None)),
          (("text", "blob",         None,   False, True),  ("text", db.BLOB,   None,   False,      True,  None)),
          (("show", "tinyint(1)",   None,   False, True),  ("show", db.BOOL,   None,   False,      True,  None)),
          (("date", "timestamp",    None,   False, True),  ("date", db.DATE,   None,   False,      True,  None)),
          (("date", "timestamp",    now1,   False, True),  ("date", db.DATE,   db.NOW, False,      True,  None)),
          (("date", "time",         now2,   False, "YES"), ("date", db.DATE,   db.NOW, False,      True,  None))):
            s = db.Schema(*args)
            self.assertEqual(s.name,     v[0])
            self.assertEqual(s.type,     v[1])
            self.assertEqual(s.default,  v[2])
            self.assertEqual(s.index,    v[3])
            self.assertEqual(s.optional, v[4])
            self.assertEqual(s.length,   v[5])
        print "pattern.db.Schema()"

#-----------------------------------------------------------------------------------------------------

class TestTable(unittest.TestCase):

    db = None

    def setUp(self):
        # Create test tables.
        self.db.create("persons", fields=[
            db.primary_key("id"),
            db.field("name", db.STRING)
        ])
        self.db.create("products", fields=[
            db.primary_key("id"),
            db.field("name", db.STRING),
            db.field("price", db.FLOAT, default=0.0)
        ])
        self.db.create("orders", fields=[
            db.primary_key("id"),
            db.field("person", db.INTEGER, index=True),
            db.field("product", db.INTEGER, index=True),
        ])
        
    def tearDown(self):
        # Drop test tables.
        for table in self.db:
            self.db.drop(table)
            
    def test_table(self):
        # Assert Table properties.
        v = self.db.persons
        self.assertTrue(v.db          == self.db)
        self.assertTrue(v.pk          == "id")
        self.assertTrue(v.fields      == ["id", "name"])
        self.assertTrue(v.name        == "persons")
        self.assertTrue(v.abs("name") == "persons.name")
        self.assertTrue(v.rows()      == [])
        self.assertTrue(v.schema["id"].type  == db.INTEGER)
        self.assertTrue(v.schema["id"].index == db.PRIMARY)
        print "pattern.db.Table"
        
    def test_rename(self):
        # Assert ALTER TABLE when name changes.
        v = self.db.persons
        v.name = "clients"
        self.assertEqual(self.db.query, "alter table `persons` rename to `clients`;")
        self.assertEqual(self.db.tables.get("clients"), v)
        print "pattern.db.Table.name"
        
    def test_fields(self):
        # Assert ALTER TABLE when column is inserted.
        v = self.db.products
        v.fields.append(db.field("description", db.TEXT))
        self.assertEqual(v.fields, ["id", "name", "price", "description"])
        print "pattern.db.Table.fields"
        
    def test_insert_update_delete(self):
        # Assert Table.insert().
        v1 = self.db.persons.insert(name=u"Kurt Gödel")
        v2 = self.db.products.insert(name="pizza", price=10.0)
        v3 = self.db.products.insert({"name":"garlic bread", "price":3.0})
        v4 = self.db.orders.insert(person=v1, product=v3)
        self.assertEqual(v1, 1)
        self.assertEqual(v2, 1)
        self.assertEqual(v3, 2)
        self.assertEqual(v4, 1)
        self.assertEqual(self.db.persons.rows(),  [(1, u"Kurt Gödel")])
        self.assertEqual(self.db.products.rows(), [(1, u"pizza", 10.0), (2, u"garlic bread", 3.0)])
        self.assertEqual(self.db.orders.rows(),   [(1, 1, 2)])
        self.assertEqual(self.db.orders.count(),  1)
        self.assertEqual(self.db.products.xml.replace(' extra="auto_increment"', ""),
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<table name="products" fields="id, name, price" count="2">\n'
            '\t<schema>\n'
            '\t\t<field name="id" type="integer" index="primary" optional="no" />\n'
            '\t\t<field name="name" type="string" length="100" />\n'
            '\t\t<field name="price" type="float" default="0.0" />\n'
            '\t</schema>\n'
            '\t<rows>\n'
            '\t\t<row id="1" name="pizza" price="10.0" />\n'
            '\t\t<row id="2" name="garlic bread" price="3.0" />\n'
            '\t</rows>\n'
            '</table>'
        )
        # Assert transactions with commit=False.
        if self.db.type == db.SQLITE:
            self.db.orders.insert(person=v1, product=v2, commit=False)
            self.db.rollback()
            self.assertEqual(len(self.db.orders), 1)
        self.db.orders.insert(person=v1, product=v2, commit=False)
        # Assert Table.update().
        self.db.products.update(2, price=4.0)
        self.db.products.update(2, {"price":4.5})
        self.db.products.update(db.all(db.filter("name", "pi*")), name="deeppan pizza")
        self.assertEqual(self.db.products.rows(), [(1, u"deeppan pizza", 10.0), (2, u"garlic bread", 4.5)])
        # Assert Table.delete().
        self.db.products.delete(db.all(db.filter("name", "deeppan*")))
        self.db.products.delete(db.ALL)
        self.db.orders.delete(1)
        self.assertEqual(len(self.db.products), 0)
        self.assertEqual(len(self.db.orders), 1)
        print "pattern.db.Table.insert()"
        print "pattern.db.Table.update()"
        print "pattern.db.Table.delete()"
    
    def test_filter(self):
        # Assert Table.filter().
        self.db.persons.insert(name=u"Kurt Gödel")
        self.db.persons.insert(name=u"M. C. Escher")
        self.db.persons.insert(name=u"Johann Sebastian Bach")
        f = self.db.persons.filter
        self.assertEqual(f(("name",), id=1),        [(u"Kurt Gödel",)])
        self.assertEqual(f(db.ALL, id=(1,2)),       [(1, u"Kurt Gödel"), (2, u"M. C. Escher")])
        self.assertEqual(f({"id":(1,2)}),           [(1, u"Kurt Gödel"), (2, u"M. C. Escher")])
        self.assertEqual(f("id", name="Johan*"),    [(3,)])
        self.assertEqual(f("id", name=("J*","K*")), [(1,), (3,)])
        print "pattern.db.Table.filter()"
        
    def test_search(self):
        pass
        

class TestMySQLTable(TestTable):
    db = DB_MYSQL
    
class TestSQLiteTable(TestTable):
    db = DB_SQLITE

#-----------------------------------------------------------------------------------------------------

class TestQuery(unittest.TestCase):

    db = None

    def setUp(self):
        # Create test tables.
        self.db.create("persons", fields=[
            db.primary_key("id"),
            db.field("name", db.STRING),
            db.field("age", db.INTEGER),
            db.field("gender", db.INTEGER)
        ])
        self.db.create("gender", fields=[
            db.primary_key("id"),
            db.field("name", db.STRING)
        ])
        # Create test data.
        self.db.persons.insert(name="john", age="30", gender=2)
        self.db.persons.insert(name="jack", age="20", gender=2)
        self.db.persons.insert(name="jane", age="30", gender=1)
        self.db.gender.insert(name="female")
        self.db.gender.insert(name="male")
        
    def tearDown(self):
        # Drop test tables.
        for table in self.db:
            self.db.drop(table)
        
    def _query(self, *args, **kwargs):
        """ Returns a pattern.db.Query object on a mock Table and Database.
        """
        class Database:
            escape, relations = lambda self, v: db._escape(v), []
        class Table:
            name, fields, db = "persons", ["id", "name", "age", "sex"], Database()
        return db.Query(Table(), *args, **kwargs)
        
    def test_abs(self):
        # Assert absolute fieldname for trivial cases.
        self.assertEqual(db.abs("persons", "name"), "persons.name")
        self.assertEqual(db.abs("persons", ("id", "name")), ["persons.id", "persons.name"])
        # Assert absolute fieldname with SQL functions (e.g., avg(product.price)).
        for f in db.sql_functions.split("|"):
            self.assertEqual(db.abs("persons", "%s(name)" % f), "%s(persons.name)" % f)
        print "pattern.db.abs()"
        
    def test_cmp(self):
        # Assert WHERE-clause from cmp() function.
        q = self.db.persons.search(fields=["name"])
        self.assertTrue(isinstance(q, db.Query))
        for args, sql in (
          (("name", u"Kurt%",    db.LIKE),    u"name like 'Kurt%'"),
          (("name", u"Kurt*",    "="),        u"name like 'Kurt%'"),
          (("name", u"*Gödel",   "=="),       u"name like '%Gödel'"),
          (("name", u"Kurt*",    "!="),       u"name not like 'Kurt%'"),
          (("name", u"Kurt*",    "<>"),       u"name not like 'Kurt%'"),
          (("name", u"Gödel",    "i="),       u"name like 'Gödel'"),     # case-insensitive search
          (("id",   (1, 2),      db.IN),      u"id in (1,2)"),
          (("id",   (1, 2),      "="),        u"id in (1,2)"),
          (("id",   (1, 2),      "=="),       u"id in (1,2)"),
          (("id",   (1, 2),      "!="),       u"id not in (1,2)"),
          (("id",   (1, 2),      "<>"),       u"id not in (1,2)"),
          (("id",   (1, 3),      db.BETWEEN), u"id between 1 and 3"),
          (("id",   (1, 3),      ":"),        u"id between 1 and 3"),
          (("name", ("G","K*"),  "="),        u"(name='G' or name like 'K%')"),
          (("name", None,        "="),        u"name is null"),
          (("name", None,        "=="),       u"name is null"),
          (("name", None,        "!="),       u"name is not null"),
          (("name", None,        "<>"),       u"name is not null"),
          (("name", q,           "="),        u"name in (select persons.name from `persons`)"),
          (("name", q,           "=="),       u"name in (select persons.name from `persons`)"),
          (("name", q,           "!="),       u"name not in (select persons.name from `persons`)"),
          (("name", q,           "<>"),       u"name not in (select persons.name from `persons`)"),
          (("name", u"Gödel",    "="),        u"name='Gödel'"),
          (("id",   1,           ">"),        u"id>1")):
            self.assertEqual(db.cmp(*args), sql)
        print "pattern.db.cmp()"
        
    def test_group(self):
        # Assert WHERE with AND/OR combinations from Group object().
        yesterday  = db.date()
        yesterday -= db.time(days=1)
        g1 = db.Group(("name", "garlic bread"))
        g2 = db.Group(("name", "pizza"), ("price", 10, "<"), operator=db.AND)
        g3 = db.Group(g1, g2, operator=db.OR)
        g4 = db.Group(g3, ("date", yesterday, ">"), operator=db.AND)
        self.assertEqual(g1.SQL(), "name='garlic bread'")
        self.assertEqual(g2.SQL(), "name='pizza' and price<10")
        self.assertEqual(g3.SQL(), "(name='garlic bread') or (name='pizza' and price<10)")
        self.assertEqual(g4.SQL(), "((name='garlic bread') or (name='pizza' and price<10)) and date>'%s'" % yesterday)
        # Assert subquery in group.
        q = self._query(fields=["name"])
        g = db.any(("name", u"Gödel"), ("name", q))
        self.assertEqual(g.SQL(), u"name='Gödel' or name in (select persons.name from `persons`)")
        print "pattern.db.Group"
        
    def test_query(self):
        # Assert table query results from Table.search().
        for kwargs, sql, rows in (
          (dict(fields=db.ALL),
            "select persons.* from `persons`;",
            [(1, u"john", 30, 2), 
             (2, u"jack", 20, 2), 
             (3, u"jane", 30, 1)]),
          (dict(fields=db.ALL, range=(0, 2)),
            "select persons.* from `persons` limit 0, 2;",
            [(1, u"john", 30, 2), 
             (2, u"jack", 20, 2)]),
          (dict(fields=db.ALL, filters=[("age", 30, "<")]),
            "select persons.* from `persons` where persons.age<30;",
            [(2, u"jack", 20, 2)]),
          (dict(fields=db.ALL, filters=db.any(("age", 30, "<"), ("name", "john"))),
            "select persons.* from `persons` where persons.age<30 or persons.name='john';",
            [(1, u"john", 30, 2), 
             (2, u"jack", 20, 2)]),
          (dict(fields=["name", "gender.name"], relations=[db.relation("gender", "id", "gender")]),
            "select persons.name, gender.name from `persons` left join `gender` on persons.gender=gender.id;",
            [(u"john", u"male"), 
             (u"jack", u"male"), 
             (u"jane", u"female")]),
          (dict(fields=["name","age"], sort="name"),
            "select persons.name, persons.age from `persons` order by persons.name asc;",
            [(u"jack", 20), 
             (u"jane", 30),
             (u"john", 30)]),
          (dict(fields=["name","age"], sort=1, order=db.DESCENDING),
            "select persons.name, persons.age from `persons` order by persons.name desc;",
            [(u"john", 30),
             (u"jane", 30),
             (u"jack", 20)]),
          (dict(fields=["age","name"], sort=["age","name"], order=[db.ASCENDING, db.DESCENDING]),
            "select persons.age, persons.name from `persons` order by persons.age asc, persons.name desc;",
            [(20, u"jack"),
             (30, u"john"),
             (30, u"jane")]),
          (dict(fields=["age","name"], group="age", function=db.CONCATENATE),
            "select persons.age, group_concat(persons.name) from `persons` group by persons.age;",
            [(20, u"jack"), 
             (30, u"john,jane")]),
          (dict(fields=["id", "name","age"], group="age", function=[db.COUNT, db.CONCATENATE]),
            "select count(persons.id), group_concat(persons.name), persons.age from `persons` group by persons.age;",
            [(1, u"jack", 20), 
             (2, u"john,jane", 30)])):
            v = self.db.persons.search(**kwargs)
            self.assertEqual(v.SQL(), sql)
            self.assertEqual(v.rows(), rows)
        # Assert Database.link() permanent relations.
        self.db.link("persons", "gender", "gender", "id", join=db.LEFT)
        v = self.db.persons.search(fields=["name", "gender.name"])
        v.aliases["gender.name"] = "gender"
        self.assertEqual(v.SQL(), 
            "select persons.name, gender.name as gender from `persons` left join `gender` on persons.gender=gender.id;")
        self.assertEqual(v.rows(),
            [(u'john', u'male'), 
             (u'jack', u'male'), 
             (u'jane', u'female')])
        # Assert Query.xml dump.
        self.assertEqual(v.xml,
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<query table="persons" fields="name, gender" count="3">\n'
            '\t<schema>\n'
            '\t\t<field name="name" type="string" length="100" />\n'
            '\t\t<field name="gender" type="string" length="100" />\n'
            '\t</schema>\n'
            '\t<rows>\n'
            '\t\t<row name="john" gender="male" />\n'
            '\t\t<row name="jack" gender="male" />\n'
            '\t\t<row name="jane" gender="female" />\n'
            '\t</rows>\n'
            '</query>'
        )
        print "pattern.db.Table.search()"
        print "pattern.db.Table.Query"

class TestMySQLQuery(TestQuery):
    db = DB_MYSQL
    
class TestSQLiteQuery(TestQuery):
    db = DB_SQLITE

#-----------------------------------------------------------------------------------------------------

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEntities))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDate))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSchema))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCreateMySQLDatabase))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCreateSQLiteDatabase))
    if DB_MYSQL:
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMySQLDatabase))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMySQLTable))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMySQLQuery))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDeleteMySQLDatabase))
    if DB_SQLITE:
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSQLiteDatabase))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSQLiteTable))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSQLiteQuery))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDeleteSQLiteDatabase))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())
