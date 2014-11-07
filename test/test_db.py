# -*- coding: utf-8 -*-

from __future__ import print_function

from util import *

from pattern import db

# To test MySQL, you need MySQLdb and a username + password with rights to
# create a database.
HOST, PORT, USERNAME, PASSWORD = "localhost", 3306, "root", ""


def create_db_mysql():
    global DB_MYSQL
    global DB_MYSQL_EXCEPTION
    DB_MYSQL = DB_MYSQL_EXCEPTION = None
    try:
        DB_MYSQL = db.Database(
            type=db.MYSQL,
            name="pattern_unittest_db",
            host=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD)
    except ImportError as e:
        DB_MYSQL_EXCEPTION = None  # "No module named MySQLdb"
    except Exception as e:
        DB_MYSQL_EXCEPTION = e
create_db_mysql()


def create_db_sqlite():
    global DB_SQLITE
    global DB_SQLITE_EXCEPTION
    DB_SQLITE = DB_SQLITE_EXCEPTION = None
    try:
        DB_SQLITE = db.Database(
            type=db.SQLITE,
            name="pattern_unittest_db",
            host=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD)
    except Exception as e:
        DB_SQLITE_EXCEPTION = e
create_db_sqlite()

#-------------------------------------------------------------------------


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
        print("pattern.db.decode_utf8()")

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(db.encode_utf8(s), str))
        print("pattern.db.encode_utf8()")

    def test_string(self):
        # Assert string() with default for "" and None.
        for v, s in ((True, u"True"), (1, u"1"), (1.0, u"1.0"), ("", u"????"), (None, u"????")):
            self.assertEqual(db.string(v, default="????"), s)
        print("pattern.db.string()")

#-------------------------------------------------------------------------


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
        print("pattern.db.encode_entities()")

    def test_decode_entities(self):
        # Assert HMTL entity decoder (e.g., "&amp;" => "&")
        for a, b in (
                ("&#38;", "&"),
                ("&amp;", "&"),
                ("&#x0026;", "&"),
                ("&#160;", u"\xa0"),
                ("&foo;", "&foo;")):
            self.assertEqual(db.decode_entities(a), b)
        print("pattern.db.decode_entities()")

#-------------------------------------------------------------------------


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
        v3 = db.date(
            2010, 9, 21, hour=9, minute=27, second=0o1, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(str(v1), "2010-09-21 00:00:00")
        self.assertEqual(str(v2), "2010-09-21 09:27:01")
        self.assertEqual(str(v3), "2010-09-21 09:27:01")
        # Assert week and weekday input
        v4 = db.date(
            2014, week=1, weekday=1, hour=12, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(str(v4), "2013-12-30 12:00:00")
        # Assert Date input.
        v5 = db.date(db.date(2014, 1, 1))
        self.assertEqual(str(v5), "2014-01-01 00:00:00")
        # Assert timestamp input.
        v6 = db.date(db.date(2014, 1, 1).timestamp)
        self.assertEqual(str(v5), "2014-01-01 00:00:00")
        # Assert DateError for other input.
        self.assertRaises(db.DateError, db.date, None)
        print("pattern.db.date()")

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
        print("pattern.db.Date.__str__()")

    def test_timestamp(self):
        # Assert Date.timestamp.
        if True:
            raise unittest.SkipTest("FIXME see GH issue 94.")

        v = db.date(2010, 9, 21, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(v.timestamp, 1285041600)
        print("pattern.db.Date.timestamp")

    def test_time(self):
        # Assert Date + time().
        v = db.date("2010-09-21 9:27:00")
        v = v - db.time(days=1, hours=1, minutes=1, seconds=1)
        self.assertEqual(str(v), "2010-09-20 08:25:59")
        # Assert Date + time(years, months)
        v = db.date(2014, 1, 31)
        v = v + db.time(years=1, months=1)
        self.assertEqual(str(v), "2015-02-28 00:00:00")
        print("pattern.db.time()")

#-------------------------------------------------------------------------


class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_encryption(self):
        # Assert string password encryption.
        v1 = "test"
        v2 = db.encrypt_string(v1, key="1234")
        v3 = db.decrypt_string(v2, key="1234")
        self.assertTrue(v2 != "test")
        self.assertTrue(v3 == "test")
        print("pattern.db.encrypt_string()")
        print("pattern.db.decrypt_string()")

    def test_json(self):
        # Assert JSON input and output.
        v1 = ["a,b", 1, 1.0, True, False, None, [1, 2], {
            "a:b": 1.2, "a,b": True, "a": [1, {"2": 3}], "1": "None"}]
        v2 = db.json.dumps(v1)
        v3 = db.json.loads(v2)
        self.assertEqual(v1, v3)
        print("pattern.db.json.dumps()")
        print("pattern.db.json.loads()")

    def test_order(self):
        # Assert a list of indices in the order as when the given list is
        # sorted.
        v = [3, 1, 2]
        self.assertEqual(db.order(v), [1, 2, 0])
        self.assertEqual(db.order(v, reverse=True), [0, 2, 1])
        self.assertEqual(db.order(v, cmp=lambda a, b: a - b), [1, 2, 0])
        self.assertEqual(db.order(v, key=lambda i: i), [1, 2, 0])
        print("pattern.db.order()")

    def test_avg(self):
        # Assert (1+2+3+4) / 4 = 2.5.
        self.assertEqual(db.avg([1, 2, 3, 4]), 2.5)
        print("pattern.db.avg()")

    def test_variance(self):
        # Assert 2.5.
        self.assertEqual(db.variance([1, 2, 3, 4, 5]), 2.5)
        print("pattern.db.variance()")

    def test_stdev(self):
        # Assert 2.429.
        self.assertAlmostEqual(db.stdev([1, 5, 6, 7, 6, 8]), 2.429, places=3)
        print("pattern.db.stdev()")

    def test_sqlite_functions(self):
        # Assert year(), month(), day(), ..., first(), last() and
        # group_concat() for SQLite.
        v = "1707-04-15 01:02:03"
        self.assertEqual(db.sqlite_year(v),   1707)
        self.assertEqual(db.sqlite_month(v),  4)
        self.assertEqual(db.sqlite_day(v),    15)
        self.assertEqual(db.sqlite_hour(v),   1)
        self.assertEqual(db.sqlite_minute(v), 2)
        self.assertEqual(db.sqlite_second(v), 3)
        # Aggregate functions.
        for f, a, b in (
                (db.sqlite_first, [1, 2, 3], 1),
                (db.sqlite_last,  [1, 2, 3], 3),
                (db.sqlite_group_concat, [1, 2, 3], "1,2,3")):
            f = f()
            for x in a:
                f.step(x)
            self.assertEqual(f.finalize(), b)
        print("pattern.db.sqlite_year()")
        print("pattern.db.sqlite_month()")
        print("pattern.db.sqlite_day()")
        print("pattern.db.sqlite_hour()")
        print("pattern.db.sqlite_minute()")
        print("pattern.db.sqlite_second()")
        print("pattern.db.sqlite_first()")
        print("pattern.db.sqlite_last()")
        print("pattern.db.sqlite_group_concat()")

#-------------------------------------------------------------------------


class AbstractTestDatabase(object):

    def setUp(self):
        # Define self.db and self.type in a subclass.
        raise unittest.SkipTest("abstract method, must be defined on subclass")

    def tearDown(self):
        for table in list(self.db):
            self.db.drop(table)

    def test_escape(self):
        # Assert str, unicode, int, long, float, bool and None field values.
        for v, s in (
                ("a", "'a'"),
                (u"a", "'a'"),
                (1, "1"),
                (1, "1"),
                (1.0, "1.0"),
                (True, "1"),
                (False, "0"),
                (None, "null")):
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
        print("pattern.db._escape()")

    def test_database(self):
        # Assert Database properties.
        self.assertTrue(self.db.type == self.type)
        self.assertTrue(self.db.name == "pattern_unittest_db")
        self.assertTrue(self.db.host == HOST)
        self.assertTrue(self.db.port == PORT)
        self.assertTrue(self.db.username == USERNAME)
        self.assertTrue(self.db.password == PASSWORD)
        self.assertTrue(self.db.tables == {})
        self.assertTrue(self.db.relations == [])
        self.assertTrue(self.db.connected == True)
        self.db.disconnect()
        self.assertTrue(self.db.connected == False)
        self.assertTrue(self.db.connection == None)
        self.db.connect()
        print("pattern.db.Database(type=%s)" % self.type.upper())

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
        self.assertTrue(len(self.db) == 1)
        self.assertTrue(v.pk == "pid")
        self.assertTrue(v.fields == ["pid", "name", "price"])
        self.assertTrue(self.db[v.name] == v)
        self.assertTrue(self.db.tables[v.name] == v)
        self.assertTrue(getattr(self.db, v.name) == v)
        # Assert Database._field_SQL subroutine for Database.create().
        for field, sql1, sql2 in (
            (db.primary_key("pid"),
             ("`pid` integer not null primary key auto_increment", None),
                ("`pid` integer not null primary key autoincrement", None)),
            (db.field("name", db.STRING, index=True, optional=False),
                ("`name` varchar(100) not null",
                 "create index `products_name` on `products` (`name`);"),
                ("`name` varchar(100) not null", "create index `products_name` on `products` (`name`);")),
            (db.field("price", db.INTEGER),
                ("`price` integer null", None),
                ("`price` integer null", None))):
            if self.db.type == db.MYSQL:
                self.assertEqual(
                    self.db._field_SQL(self.db["products"].name, field), sql1)
            if self.db.type == db.SQLITE:
                self.assertEqual(
                    self.db._field_SQL(self.db["products"].name, field), sql2)
        # Assert TableError if table already exists.
        self.assertRaises(db.TableError, self.db.create, "products")
        # Assert remove table.
        self.db.drop("products")
        self.assertTrue(len(self.db) == 0)
        print("pattern.db.Database.create()")

    def test_delete(self):
        self.db ._delete()


class TestMySQLDatabase(AbstractTestDatabase, unittest.TestCase):

    def setUp(self):
        create_db_mysql()
        self.db = DB_MYSQL
        self.type = db.MYSQL
        if self.db is None:
            raise unittest.SkipTest("Mysql database was not created.")


class TestCreateSQLiteDatabase(AbstractTestDatabase, unittest.TestCase):

    def setUp(self):
        create_db_sqlite()
        self.db = DB_SQLITE
        self.type = db.SQLITE
        if self.db is None:
            raise unittest.SkipTest("Sqlite database was not created.")


#-------------------------------------------------------------------------

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
        # NAME     TYPE            DEFAULT INDEX      OPTIONAL
        for kwargs, f in (
            (dict(name="id",    type=db.INT),
             ("id",    "integer",      None,   False,     True)),
            (dict(name="id",    type=db.INT,    index=db.PRIMARY),
                ("id",    "integer",      None,   "primary", True)),
            (dict(name="id",    type=db.INT,    index=db.UNIQUE),
                ("id",    "integer",      None,   "unique",  True)),
            (dict(name="id",    type=db.INT,    index="0"),
                ("id",    "integer",      None,   False,     True)),
            (dict(name="id",    type=db.INT,    index="1"),
                ("id",    "integer",      None,   True,      True)),
            (dict(name="id",    type=db.INT,    index=True),
                ("id",    "integer",      None,   True,      True)),
            (dict(name="id",    type=db.INT,    default=0),
                ("id",    "integer",      0,      False,     True)),
            (dict(name="name",  type=db.STRING),
                ("name",  "varchar(100)", None,   False,     True)),
            (dict(name="name",  type=db.STRING, optional=False),
                ("name",  "varchar(100)", None,   False,     False)),
            (dict(name="name",  type=db.STRING, optional="0"),
                ("name",  "varchar(100)", None,   False,     False)),
            (dict(name="name",  type=db.STRING(50)),
                ("name",  "varchar(50)",  None,   False,     True)),
            (dict(name="price", type=db.FLOAT,  default=0),
                ("price", "real",         0,      False,     True)),
            (dict(name="show",  type=db.BOOL),
                ("show",  "tinyint(1)",   None,   False,     True)),
            (dict(name="show",  type=db.BOOL,   default=True),
                ("show",  "tinyint(1)",   True,   False,     True)),
            (dict(name="show",  type=db.BOOL,   default=False),
                ("show",  "tinyint(1)",   False,  False,     True)),
            (dict(name="date",  type=db.DATE),
                ("date",  "timestamp",    "now",  False,     True)),
            (dict(name="date",  type=db.DATE,   default=db.NOW),
                ("date",  "timestamp",    "now",  False,     True)),
            (dict(name="date",  type=db.DATE,   default="1999-12-31 23:59:59"),
                ("date", "timestamp", "1999-12-31 23:59:59", False, True))):
            self.assertEqual(db.field(**kwargs), f)
        # Assert primary_key() return value.
        self.assertTrue(db.primary_key() == db.pk() == (
            "id", "integer", None, "primary", False))
        print("pattern.db.field()")

    def test_schema(self):
        now1 = "current_timestamp"
        now2 = "'CURRENT_TIMESTAMP'"
        # Assert Schema (= table schema in a uniform way across database engines).
        #   NAME    TYPE            DEFAULT INDEX  OPTIONAL
        for args, v in (
                (("id",   "integer",      None,   "pri", False),
                 ("id",   db.INT,    None,   db.PRIMARY, False, None)),
                (("id",   "integer",      None,   "uni", False),
                    ("id",   db.INT,    None,   db.UNIQUE,  False, None)),
                (("id",   "int",          None,   "yes", True),
                    ("id",   db.INT,    None,   True,       True,  None)),
                (("id",   "real",         None,   "mul", True),
                    ("id",   db.FLOAT,  None,   True,       True,  None)),
                (("id",   "real",         None,   "1",   True),
                    ("id",   db.FLOAT,  None,   True,       True,  None)),
                (("id",   "double",       None,   "0",   True),
                    ("id",   db.FLOAT,  None,   False,      True,  None)),
                (("id",   "double",       0,      False, False),
                    ("id",   db.FLOAT,  0,      False,      False, None)),
                (("text", "varchar(10)",  "?",    False, True),
                    ("text", db.STRING, "?",    False,      True,  10)),
                (("text", "char(20)",     "",     False, True),
                    ("text", db.STRING, None,   False,      True,  20)),
                (("text", "text",         None,   False, True),
                    ("text", db.TEXT,   None,   False,      True,  None)),
                (("text", "blob",         None,   False, True),
                    ("text", db.BLOB,   None,   False,      True,  None)),
                (("show", "tinyint(1)",   None,   False, True),
                    ("show", db.BOOL,   None,   False,      True,  None)),
                (("date", "timestamp",    None,   False, True),
                    ("date", db.DATE,   None,   False,      True,  None)),
                (("date", "timestamp",    now1,   False, True),
                    ("date", db.DATE,   db.NOW, False,      True,  None)),
                (("date", "time",         now2,   False, "YES"), ("date", db.DATE,   db.NOW, False,      True,  None))):
            s = db.Schema(*args)
            self.assertEqual(s.name,     v[0])
            self.assertEqual(s.type,     v[1])
            self.assertEqual(s.default,  v[2])
            self.assertEqual(s.index,    v[3])
            self.assertEqual(s.optional, v[4])
            self.assertEqual(s.length,   v[5])
        print("pattern.db.Schema()")

#-------------------------------------------------------------------------


class AbstractTestTable(object):

    def setUp(self):
        if self.db is None:
            raise unittest.SkipTest()

        # Define self.db in a subclass.
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
        for table in list(self.db):
            self.db.drop(table)

    def test_table(self):
        # Assert Table properties.
        v = self.db.persons
        self.assertTrue(v.db == self.db)
        self.assertTrue(v.pk == "id")
        self.assertTrue(v.fields == ["id", "name"])
        self.assertTrue(v.name == "persons")
        self.assertTrue(v.abs("name") == "persons.name")
        self.assertTrue(v.rows() == [])
        self.assertTrue(v.schema["id"].type == db.INTEGER)
        self.assertTrue(v.schema["id"].index == db.PRIMARY)
        print("pattern.db.Table")

    def test_rename(self):
        # Assert ALTER TABLE when name changes.
        v = self.db.persons
        v.name = "clients"
        self.assertEqual(
            self.db.query, "alter table `persons` rename to `clients`;")
        self.assertEqual(self.db.tables.get("clients"), v)
        print("pattern.db.Table.name")

    def test_fields(self):
        # Assert ALTER TABLE when column is inserted.
        v = self.db.products
        v.fields.append(db.field("description", db.TEXT))
        self.assertEqual(v.fields, ["id", "name", "price", "description"])
        print("pattern.db.Table.fields")

    def test_insert_update_delete(self):
        # Assert Table.insert().
        v1 = self.db.persons.insert(name=u"Kurt Gödel")
        v2 = self.db.products.insert(name="pizza", price=10.0)
        v3 = self.db.products.insert({"name": "garlic bread", "price": 3.0})
        v4 = self.db.orders.insert(person=v1, product=v3)
        self.assertEqual(v1, 1)
        self.assertEqual(v2, 1)
        self.assertEqual(v3, 2)
        self.assertEqual(v4, 1)
        self.assertEqual(self.db.persons.rows(),  [(1, u"Kurt Gödel")])
        self.assertEqual(
            self.db.products.rows(), [(1, u"pizza", 10.0), (2, u"garlic bread", 3.0)])
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
        self.db.products.update(2, {"price": 4.5})
        self.db.products.update(
            db.all(db.filter("name", "pi*")), name="deeppan pizza")
        self.assertEqual(self.db.products.rows(), [
                         (1, u"deeppan pizza", 10.0), (2, u"garlic bread", 4.5)])
        # Assert Table.delete().
        self.db.products.delete(db.all(db.filter("name", "deeppan*")))
        self.db.products.delete(db.ALL)
        self.db.orders.delete(1)
        self.assertEqual(len(self.db.products), 0)
        self.assertEqual(len(self.db.orders), 1)
        print("pattern.db.Table.insert()")
        print("pattern.db.Table.update()")
        print("pattern.db.Table.delete()")

    def test_filter(self):
        # Assert Table.filter().
        self.db.persons.insert(name=u"Kurt Gödel")
        self.db.persons.insert(name=u"M. C. Escher")
        self.db.persons.insert(name=u"Johann Sebastian Bach")
        f = self.db.persons.filter
        self.assertEqual(f(("name",), id=1),        [(u"Kurt Gödel",)])
        self.assertEqual(
            f(db.ALL, id=(1, 2)),       [(1, u"Kurt Gödel"), (2, u"M. C. Escher")])
        self.assertEqual(
            f({"id": (1, 2)}),           [(1, u"Kurt Gödel"), (2, u"M. C. Escher")])
        self.assertEqual(f("id", name="Johan*"),    [(3,)])
        self.assertEqual(f("id", name=("J*", "K*")), [(1,), (3,)])
        print("pattern.db.Table.filter()")

    def test_search(self):
        # Assert Table.search => Query object.
        v = self.db.persons.search()
        self.assertTrue(isinstance(v, db.Query))
        self.assertTrue(v.table == self.db.persons)

    def test_datasheet(self):
        # Assert Table.datasheet() => Datasheet object.
        v = self.db.persons.datasheet()
        self.assertTrue(isinstance(v, db.Datasheet))
        self.assertTrue(v.fields[0] == ("id", db.INTEGER))
        print("pattern.db.Table.datasheet()")


class TestMySQLTable(AbstractTestTable, unittest.TestCase):

    def setUp(self):
        self.db = DB_MYSQL
        AbstractTestTable.setUp(self)


class TestSQLiteTable(AbstractTestTable, unittest.TestCase):

    def setUp(self):
        self.db = DB_SQLITE
        AbstractTestTable.setUp(self)

#-------------------------------------------------------------------------


class AbstractTestQuery(object):

    def setUp(self):
        if self.db is None:
            raise unittest.SkipTest()

        # Define self.db in a subclass.
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
        for table in list(self.db):
            self.db.drop(table)

    def _query(self, *args, **kwargs):
        """Returns a pattern.db.Query object on a mock Table and Database."""
        class Database:
            escape, relations = lambda self, v: db._escape(v), []

        class Table:
            name, fields, db = "persons", [
                "id", "name", "age", "sex"], Database()
        return db.Query(Table(), *args, **kwargs)

    def test_abs(self):
        # Assert absolute fieldname for trivial cases.
        self.assertEqual(db.abs("persons", "name"), "persons.name")
        self.assertEqual(
            db.abs("persons", ("id", "name")), ["persons.id", "persons.name"])
        # Assert absolute fieldname with SQL functions (e.g.,
        # avg(product.price)).
        for f in db.sql_functions.split("|"):
            self.assertEqual(
                db.abs("persons", "%s(name)" % f), "%s(persons.name)" % f)
        print("pattern.db.abs()")

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
                # case-insensitive search
                (("name", u"Gödel",    "i="),       u"name like 'Gödel'"),
                (("id",   (1, 2),      db.IN),      u"id in (1,2)"),
                (("id",   (1, 2),      "="),        u"id in (1,2)"),
                (("id",   (1, 2),      "=="),       u"id in (1,2)"),
                (("id",   (1, 2),      "!="),       u"id not in (1,2)"),
                (("id",   (1, 2),      "<>"),       u"id not in (1,2)"),
                (("id",   (1, 3),      db.BETWEEN), u"id between 1 and 3"),
                (("id",   (1, 3),      ":"),        u"id between 1 and 3"),
                (("name", ("G", "K*"),  "="),
                    u"(name='G' or name like 'K%')"),
                (("name", None,        "="),        u"name is null"),
                (("name", None,        "=="),       u"name is null"),
                (("name", None,        "!="),       u"name is not null"),
                (("name", None,        "<>"),       u"name is not null"),
                (("name", q,           "="),
                    u"name in (select persons.name from `persons`)"),
                (("name", q,           "=="),
                    u"name in (select persons.name from `persons`)"),
                (("name", q,           "!="),
                    u"name not in (select persons.name from `persons`)"),
                (("name", q,           "<>"),
                    u"name not in (select persons.name from `persons`)"),
                (("name", u"Gödel",    "="),        u"name='Gödel'"),
                (("id",   1,           ">"),        u"id>1")):
            self.assertEqual(db.cmp(*args), sql)
        print("pattern.db.cmp()")

    def test_filterchain(self):
        # Assert WHERE with AND/OR combinations from FilterChain object().
        yesterday = db.date()
        yesterday -= db.time(days=1)
        f1 = db.FilterChain(("name", "garlic bread"))
        f2 = db.FilterChain(
            ("name", "pizza"), ("price", 10, "<"), operator=db.AND)
        f3 = db.FilterChain(f1, f2, operator=db.OR)
        f4 = db.FilterChain(f3, ("date", yesterday, ">"), operator=db.AND)
        self.assertEqual(f1.SQL(), "name='garlic bread'")
        self.assertEqual(f2.SQL(), "name='pizza' and price<10")
        self.assertEqual(
            f3.SQL(), "(name='garlic bread') or (name='pizza' and price<10)")
        self.assertEqual(
            f4.SQL(), "((name='garlic bread') or (name='pizza' and price<10)) and date>'%s'" % yesterday)
        # Assert subquery in filter chain.
        q = self._query(fields=["name"])
        f = db.any(("name", u"Gödel"), ("name", q))
        self.assertEqual(
            f.SQL(), u"name='Gödel' or name in (select persons.name from `persons`)")
        print("pattern.db.FilterChain")

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
            (dict(fields=["name", "age"], sort="name"),
                "select persons.name, persons.age from `persons` order by persons.name asc;",
                [(u"jack", 20),
                 (u"jane", 30),
                 (u"john", 30)]),
            (dict(fields=["name", "age"], sort=1, order=db.DESCENDING),
                "select persons.name, persons.age from `persons` order by persons.name desc;",
                [(u"john", 30),
                 (u"jane", 30),
                 (u"jack", 20)]),
            (dict(fields=["age", "name"], sort=["age", "name"], order=[db.ASCENDING, db.DESCENDING]),
                "select persons.age, persons.name from `persons` order by persons.age asc, persons.name desc;",
                [(20, u"jack"),
                 (30, u"john"),
                 (30, u"jane")]),
            (dict(fields=["age", "name"], group="age", function=db.CONCATENATE),
                "select persons.age, group_concat(persons.name) from `persons` group by persons.age;",
                [(20, u"jack"),
                 (30, u"john,jane")]),
            (dict(fields=["id", "name", "age"], group="age", function=[db.COUNT, db.CONCATENATE]),
                "select count(persons.id), group_concat(persons.name), persons.age from `persons` group by persons.age;",
                [(1, u"jack", 20),
                 (2, u"john,jane", 30)])):
            v = self.db.persons.search(**kwargs)
            v.xml
            self.assertEqual(v.SQL(), sql)
            self.assertEqual(v.rows(), rows)
        # Assert Database.link() permanent relations.
        v = self.db.persons.search(fields=["name", "gender.name"])
        v.aliases["gender.name"] = "gender"
        self.db.link("persons", "gender", "gender", "id", join=db.LEFT)
        self.assertEqual(v.SQL(),
                         "select persons.name, gender.name as gender from `persons` left join `gender` on persons.gender=gender.id;")
        self.assertEqual(v.rows(),
                         [(u'john', u'male'),
                          (u'jack', u'male'),
                          (u'jane', u'female')])
        print("pattern.db.Table.search()")
        print("pattern.db.Table.Query")

    def test_xml(self):
        # Assert Query.xml dump.
        v = self.db.persons.search(fields=["name", "gender.name"])
        v.aliases["gender.name"] = "gender"
        self.db.link("persons", "gender", "gender", "id", join=db.LEFT)
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
        # Assert Database.create() from XML.
        # table 'persons' already exists
        self.assertRaises(db.TableError, self.db.create, v.xml)
        self.db.create(v.xml, name="persons2")
        self.assertTrue("persons2" in self.db)
        self.assertTrue(self.db.persons2.fields == ["name", "gender"])
        self.assertTrue(len(self.db.persons2) == 3)
        print("pattern.db.Query.xml")


class TestMySQLQuery(AbstractTestQuery, unittest.TestCase):

    def setUp(self):
        self.db = DB_MYSQL
        AbstractTestQuery.setUp(self)


class TestSQLiteQuery(AbstractTestQuery, unittest.TestCase):

    def setUp(self):
        self.db = DB_SQLITE
        AbstractTestQuery.setUp(self)

#-------------------------------------------------------------------------


class AbstactTestView(object):

    def setUp(self):
        # Define self.db in a subclass.
        if self.db is None:
            raise unittest.SkipTest()

    def tearDown(self):
        # Drop test tables.
        for table in list(self.db):
            self.db.drop(table)

    def test_view(self):
        if True:
            raise unittest.SkipTest("FIXME")

        class Products(db.View):

            def __init__(self, database):
                db.View.__init__(self, database, "products", schema=[
                    db.pk(),
                    db.field("name", db.STRING),
                    db.field("price", db.FLOAT)
                ])
                self.setup()
                self.table.insert(name="pizza", price=15.0)

            def render(self, query, **kwargs):
                q = self.table.search(
                    fields=["name", "price"], filters=[("name", "*%s*" % query)])
                s = []
                for row in q.rows():
                    s.append("<tr>%s</tr>" % "".join(
                        ["<td class=\"%s\">%s</td>" % f for f in zip(q.fields, row)]))
                return "<table>" + "".join(s) + "</table>"

        # Assert View with automatic Table creation.
        v = Products(self.db)
        self.assertEqual(v.render("iz"),
                         "<table>"
                         "<tr>"
                         "<td class=\"name\">pizza</td>"
                         "<td class=\"price\">15.0</td>"
                         "</tr>"
                         "</table>"
                         )
        print("pattern.db.View")


class TestMySQLView(AbstactTestView, unittest.TestCase):

    def setUp(self):
        self.db = DB_MYSQL
        AbstactTestView.setUp(self)


class TestSQLiteView(AbstactTestView, unittest.TestCase):

    def setUp(self):
        self.db = DB_SQLITE
        AbstactTestView.setUp(self)

#-------------------------------------------------------------------------


class TestCSV(unittest.TestCase):

    def setUp(self):
        # Create test table.
        self.csv = db.CSV(
            rows=[
                [u"Schrödinger", "cat", True, 3, db.date(2009, 11, 3)],
                [u"Hofstadter", "labrador", True, 5, db.date(2007, 8, 4)]
            ],
            fields=[
                ["name", db.STRING],
                ["type", db.STRING],
                ["tail", db.BOOLEAN],
                ["age", db.INTEGER],
                ["date", db.DATE],
            ])

    def test_csv_header(self):
        # Assert field headers parser.
        v1 = db.csv_header_encode("age", db.INTEGER)
        v2 = db.csv_header_decode("age (INTEGER)")
        self.assertEqual(v1, "age (INTEGER)")
        self.assertEqual(v2, ("age", db.INTEGER))
        print("pattern.db.csv_header_encode()")
        print("pattern.db.csv_header_decode()")

    def test_csv(self):
        # Assert saving and loading data (field types are preserved).
        v = self.csv
        v.save("test.csv", headers=True)
        v = db.CSV.load("test.csv", headers=True)
        self.assertTrue(isinstance(v, list))
        self.assertTrue(v.headers[0] == (u"name", db.STRING))
        self.assertTrue(
            v[0] == [u"Schrödinger", "cat", True, 3, db.date(2009, 11, 3)])
        os.unlink("test.csv")
        print("pattern.db.CSV")
        print("pattern.db.CSV.save()")
        print("pattern.db.CSV.load()")

    def test_file(self):
        # Assert CSV file contents.
        v = self.csv
        v.save("test.csv", headers=True)
        v = open("test.csv", "rb").read()
        v = db.decode_utf8(v.lstrip(codecs.BOM_UTF8))
        v = v.replace("\r\n", "\n")
        self.assertEqual(v,
                         u'"name (STRING)","type (STRING)","tail (BOOLEAN)","age (INTEGER)","date (DATE)"\n'
                         u'"Schrödinger","cat","True","3","2009-11-03 00:00:00"\n'
                         u'"Hofstadter","labrador","True","5","2007-08-04 00:00:00"'
                         )
        os.unlink("test.csv")

#-------------------------------------------------------------------------


class TestDatasheet(unittest.TestCase):

    def setUp(self):
        pass

    def test_rows(self):
        # Assert Datasheet.rows DatasheetRows object.
        v = db.Datasheet(rows=[[1, 2], [3, 4]])
        v.rows += [5, 6]
        v.rows[0] = [0, 0]
        v.rows.swap(0, 1)
        v.rows.insert(1, [1, 1])
        v.rows.pop(1)
        self.assertTrue(isinstance(v.rows, db.DatasheetRows))
        self.assertEqual(v.rows, [[3, 4], [0, 0], [5, 6]])
        self.assertEqual(v.rows[0], [3, 4])
        self.assertEqual(v.rows[-1], [5, 6])
        self.assertEqual(v.rows.count([3, 4]), 1)
        self.assertEqual(v.rows.index([3, 4]), 0)
        self.assertEqual(
            sorted(v.rows, reverse=True), [[5, 6], [3, 4], [0, 0]])
        self.assertRaises(AttributeError, v._set_rows, [])
        # Assert default for new rows with missing columns.
        v.rows.extend([[7], [9]], default=0)
        self.assertEqual(v.rows, [[3, 4], [0, 0], [5, 6], [7, 0], [9, 0]])
        print("pattern.db.Datasheet.rows")

    def test_columns(self):
        # Assert Datasheet.columns DatasheetColumns object.
        v = db.Datasheet(rows=[[1, 3], [2, 4]])
        v.columns += [5, 6]
        v.columns[0] = [0, 0]
        v.columns.swap(0, 1)
        v.columns.insert(1, [1, 1])
        v.columns.pop(1)
        self.assertTrue(isinstance(v.columns, db.DatasheetColumns))
        self.assertEqual(v.columns, [[3, 4], [0, 0], [5, 6]])
        self.assertEqual(v.columns[0], [3, 4])
        self.assertEqual(v.columns[-1], [5, 6])
        self.assertEqual(v.columns.count([3, 4]), 1)
        self.assertEqual(v.columns.index([3, 4]), 0)
        self.assertEqual(
            sorted(v.columns, reverse=True), [[5, 6], [3, 4], [0, 0]])
        self.assertRaises(AttributeError, v._set_columns, [])
        # Assert default for new columns with missing rows.
        v.columns.extend([[7], [9]], default=0)
        self.assertEqual(v.columns, [[3, 4], [0, 0], [5, 6], [7, 0], [9, 0]])
        print("pattern.db.Datasheet.columns")

    def test_column(self):
        # Assert DatasheetColumn object.
        # It has a reference to the parent Datasheet, as long as it is not
        # deleted from the datasheet.
        v = db.Datasheet(rows=[[1, 3], [2, 4]])
        column = v.columns[0]
        column.insert(1, 0, default=None)
        self.assertEqual(v, [[1, 3], [0, None], [2, 4]])
        del v.columns[0]
        self.assertTrue(column._datasheet, None)
        print("pattern.db.DatasheetColumn")

    def test_fields(self):
        # Assert Datasheet with incomplete headers.
        v = db.Datasheet(
            rows=[[u"Schrödinger", "cat"]], fields=[("name", db.STRING)])
        self.assertEqual(v.fields, [("name", db.STRING)])
        # Assert (None, None) for missing headers.
        v.columns.swap(0, 1)
        self.assertEqual(v.fields, [(None, None), ("name", db.STRING)])
        v.columns[0] = ["dog"]
        self.assertEqual(v.fields, [(None, None), ("name", db.STRING)])
        # Assert removing a column removes the header.
        v.columns.pop(0)
        self.assertEqual(v.fields, [("name", db.STRING)])
        # Assert new columns with header description.
        v.columns.append(["cat"])
        v.columns.append([3], field=("age", db.INTEGER))
        self.assertEqual(
            v.fields, [("name", db.STRING), (None, None), ("age", db.INTEGER)])
        # Assert column by name.
        self.assertEqual(v.name, [u"Schrödinger"])
        print("pattern.db.Datasheet.fields")

    def test_group(self):
        # Assert Datasheet.group().
        v1 = db.Datasheet(
            rows=[[1, 2, "a"], [1, 3, "b"], [1, 4, "c"], [0, 0, "d"]])
        v2 = v1.group(0)
        v3 = v1.group(0, function=db.LAST)
        v4 = v1.group(0, function=(db.FIRST, db.COUNT, db.CONCATENATE))
        v5 = v1.group(0, function=db.CONCATENATE, key=lambda j: j > 0)
        self.assertEqual(v2, [[1, 2, "a"], [0, 0, "d"]])
        self.assertEqual(v3, [[1, 4, "c"], [0, 0, "d"]])
        self.assertEqual(v4, [[1, 3, u"a,b,c"], [0, 1, u"d"]])
        self.assertEqual(v5, [[True, u"2,3,4", u"a,b,c"], [False, u"0", u"d"]])
        print("pattern.db.Datasheet.group()")

    def test_slice(self):
        # Assert Datasheet slices.
        v = db.Datasheet([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        v = v.copy()
        self.assertEqual(v.slice(0, 1, 3, 2), [[2, 3], [5, 6], [8, 9]])
        self.assertEqual(v[2],       [7, 8, 9])
        self.assertEqual(v[2, 2],     9)
        self.assertEqual(v[2, 1:],    [8, 9])
        self.assertEqual(v[0:2],     [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(v[0:2, 1],   [2, 5])
        self.assertEqual(v[0:2, 0:2], [[1, 2], [4, 5]])
        # Assert new Datasheet for i:j slices.
        self.assertTrue(isinstance(v[0:2],     db.Datasheet))
        self.assertTrue(isinstance(v[0:2, 0:2], db.Datasheet))
        print("pattern.db.Datasheet.slice()")

    def test_copy(self):
        # Assert Datasheet.copy().
        v = db.Datasheet([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertTrue(v.copy(), [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertTrue(v.copy(rows=[0]), [[1, 2, 3]])
        self.assertTrue(v.copy(rows=[0], columns=[0]), [[1]])
        self.assertTrue(v.copy(columns=[0]), [[1], [4], [7]])
        print("pattern.db.Datasheet.copy()")

    def test_map(self):
        # Assert Datasheet.map() (in-place).
        v = db.Datasheet(rows=[[1, 2], [3, 4]])
        v.map(lambda x: x + 1)
        self.assertEqual(v, [[2, 3], [4, 5]])
        print("pattern.db.Datasheet.map()")

    def test_json(self):
        # Assert JSON output.
        v = db.Datasheet(rows=[[u"Schrödinger", 3], [u"Hofstadter", 5]])
        self.assertEqual(v.json, u'[["Schrödinger", 3], ["Hofstadter", 5]]')
        # Assert JSON output with headers.
        v = db.Datasheet(rows=[[u"Schrödinger", 3], [u"Hofstadter",  5]],
                         fields=[("name", db.STRING), ("age", db.INT)])
        random.seed(0)
        self.assertEqual(
            v.json, u'[{"age": 3, "name": "Schrödinger"}, {"age": 5, "name": "Hofstadter"}]')
        print("pattern.db.Datasheet.json")

    def test_flip(self):
        # Assert flip matrix.
        v = db.flip(db.Datasheet([[1, 2], [3, 4]]))
        self.assertEqual(v, [[1, 3], [2, 4]])
        print("pattern.db.flip()")

    def test_truncate(self):
        # Assert string truncate().
        v1 = "a" * 50
        v2 = "a" * 150
        v3 = "aaa " * 50
        self.assertEqual(db.truncate(v1), (v1, ""))
        self.assertEqual(db.truncate(v2), ("a" * 99 + "-", "a" * 51))
        self.assertEqual(db.truncate(v3), (("aaa " * 25).strip(), "aaa " * 25))
        print("pattern.db.truncate()")

    def test_pprint(self):
        pass

#-------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
