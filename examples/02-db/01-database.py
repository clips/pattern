# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.db import Database, SQLITE, MYSQL
from pattern.db import field, pk, STRING, INTEGER, DATE, NOW
from pattern.db import assoc
from pattern.db import rel
from pattern.db import pd  # pd() = parent directory of current script.

# In this example, we'll build a mini-store:
# with products, customers and orders.
# We can combine the data from the three tables in an invoice query.

# Create a new database.
# Once it is created, you can use Database(name) to access it.
# SQLite will create the database file in the current folder.
# MySQL databases require a username and a password.
# MySQL also requires that you install MySQLdb, see the installation instructions at:
# http://www.clips.ua.ac.be/pages/pattern-db
db = Database(pd("store.db"), type=SQLITE)
#db._delete()

# PRODUCTS
# Create the products table if it doesn't exist yet.
# An error will be raised if the table already exists.
# Add sample data.
if not "products" in db:
    # Note: in SQLite, the STRING type is mapped to TEXT (unlimited length).
    # In MySQL, the length matters. Smaller fields have faster lookup.
    schema = (
        pk(),  # Auto-incremental id.
        field("description", STRING(50)),
        field("price", INTEGER)
    )
    db.create("products", schema)
    db.products.append(description="pizza", price=15)
    db.products.append(description="garlic bread", price=3)
    #db.products.append({"description": "garlic bread", "price": 3})

# CUSTOMERS
# Create the customers table and add data.
if not "customers" in db:
    schema = (
        pk(),
        field("name", STRING(50)),
        field("address", STRING(200))
    )
    db.create("customers", schema)
    db.customers.append(name=u"Schrödinger")  # Unicode is supported.
    db.customers.append(name=u"Hofstadter")

# ORDERS
# Create the orders table if it doesn't exist yet and add data.
if not "orders" in db:
    schema = (
        pk(),
        field("product_id", INTEGER),
        field("customer_id", INTEGER),
        field("date", DATE, default=NOW)  # By default, current date/time.
    )
    db.create("orders", schema)
    db.orders.append(product_id=1, customer_id=2)  # Hofstadter orders pizza.

# Show all the products in the database.
# The assoc() iterator yields each row as a dictionary.
print("There are %s products available:" % len(db.products))
for row in assoc(db.products):
    print(row)

# Note how the orders table only contains integer id's.
# This is much more efficient than storing entire strings (e.g., customer address).
# To get the related data, we can create a query with relations between the tables.
q = db.orders.search(
    fields = (
       "products.description", 
       "products.price", 
       "customers.name", 
       "date"
    ),
    relations = (
        rel("product_id", "products.id", "products"),
        rel("customer_id", "customers.id", "customers")
    ))

print("")
print("Invoices:")
for row in assoc(q):
    print(row) # (product description, product price, customer name, date created)

print("")
print("Invoice query SQL syntax:")
print(q)

print("")
print("Invoice query XML:")
print(q.xml)

# The XML can be passed to Database.create() to create a new table (with data).
# This is explained in the online documentation.
