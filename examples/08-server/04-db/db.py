import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.server import App, Database, html

# This example demonstrates a web app with a simple database back-end.
# The pattern.server module has a Database object 
# that can be used with SQLite and MySQL databases.
# SQLite is part of Python 2.5+.
# MySQL requires the mysql-python bindings (http://sourceforge.net/projects/mysql-python/).

app = App("store")

# In this example we'll use SQLite.
# The advantage is that you don't need to install anything,
# and that the database is a file at a location of your choice.
# We use SQLite Database browser (Mac OS X) to browse the file.
# (http://sourceforge.net/projects/sqlitebrowser/)

# The disadvantage is that SQLite is not multi-threaded.
# This will lead to problems ("database is locked") in larger projects.
# The app server uses multiple threads to handle concurrent requests. 
# If two request want to write to the database at the same time,
# one of them will have to wait while the other finishes writing.
# If enough requests are waiting in line, the database may crash.
# The next example uses a DatabaseTransaction to remedy this.
# Reading from the database is no problem.

# The following code creates a new database "store.db",
# in the same folder as this script.
# Databases can be queried and modified with SQL statements.
# The SQL code below creates a "products" table in the database.
# Each table has fields (or columns) with a type (text, int, float, ...).

STORE = os.path.join(os.path.dirname(__file__), "store.db")

if not os.path.exists(STORE):
    db = Database(STORE, schema="""
        create table if not exists `products` (
                 `id` integer primary key autoincrement,
               `name` text,
              `price` float
        );
        create index if not exists products_name on products(name);
        """
    )
    # Add some rows of data to the "products" table:
    db.execute("insert into `products` (name, price) values (?, ?)", values=("rubber chicken", "199"), commit=False)
    db.execute("insert into `products` (name, price) values (?, ?)", values=("donkey costume", "249"), commit=False)
    db.execute("insert into `products` (name, price) values (?, ?)", values=("mysterious box", "999"), commit=False)
    db.commit()

# The most interesting part in this example is the code below.
# Because the server is multi-threaded,
# each separate thread needs its own Database object.
# This is handled for us by using @app.bind().
# It creates an optional parameter "db" that is available in every URL handler,
# and which contains a connection to the database for the active thread.

@app.bind("db")
def db():
    return Database(STORE)
    
# Note how the path handler for http://127.0.0.1:8080/products
# takes the optional parameter "db".
# For http://127.0.0.1:8080/products, it displays an overview of all products.
# For http://127.0.0.1:8080/products/rubber-chicken, it displays the product with the given name.

# The html.table() helper function returns a HTML-string with a <table> element.
    
@app.route("/products")
def products(name, db=None):
    if name is None:
        sql, v = "select * from `products`", ()
    else:
        sql, v = "select * from `products` where name=?", (name.replace("-", " "),)
    rows = db.execute(sql, values=v)
    rows = [(row.id, row.name, row.price) for row in rows]
    return html.table(rows, headers=("id", "name", "price"))
    
app.run("127.0.0.1", 8080, threads=30, queue=20)