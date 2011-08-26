# -*- coding: utf-8 -*-
import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.db import Database, SQLITE, MYSQL
from pattern.db import field, pk, STRING, INTEGER, DATE, NOW
from pattern.db import relation

# In this example, we'll build a mini-store:
# with products, customers and orders.
# We can combine the data from the three tables in an invoice query.

# Create a new database. 
# Once it is created, you can use Database(name) to access it.
# SQLite will create the database file in the current folder.
# MySQL databases require a username and a password.
# MySQL also requires that you install MySQLdb, see the installation instructions at:
# http://www.clips.ua.ac.be/pages/pattern-db
db = Database("store", type=MYSQL, user="root", password="root")
#db._delete()

# Create the products table if it doesn't exist yet.
# Add sample data.
if not "products" in db:
    db.create("products", fields=(
        pk(), # Auto-incremental id.
        field("description", STRING(50)),
        field("price", INTEGER)
    ))
    db.products.append(description="pizza", price=15)
    db.products.append(description="garlic bread", price=3)

# Create the customers table if it doesn't exist yet.
# Add sample data.
if not "customers" in db:
    db.create("customers", fields=(
        pk(),
        field("name", STRING(50)),
        field("address", STRING(200))
    ))
    db.customers.append(name=u"Schrödinger") # Unicode is supported.
    db.customers.append(name=u"Hofstadter")

# Create the orders table if it doesn't exist yet.
# Add sample data.
if not "orders" in db:
    db.create("orders", fields=(
        pk(),
        field("product_id", INTEGER),
        field("customer_id", INTEGER),
        field("date", DATE, default=NOW)
    ))
    db.orders.append(product_id=1, customer_id=2) # Hofstadter orders pizza.

# Show all the products in the database:
print "There are", db.products.count(), "products available:"
for row in db.products.rows():
    print row

# Note how the orders table only contains integer id's.
# This is much more efficient than storing entire strings (e.g., customer address).
# To get the related data, we can create a query with relations between the tables.
q = db.orders.search(
       fields = ["products.description", "products.price", "customers.name", "date"],
    relations = [
        relation("product_id", "products.id", "products"),
        relation("customer_id", "customers.id", "customers")
    ]
)
print
print "Invoices:"
for row in q.rows():
    print row # (product description, product price, customer name, date created)
print
print "Invoice query SQL syntax:"
print q.sql()
print
print "Invoice query XML:"
print q.xml