import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.db import Datasheet, INTEGER, STRING
from pattern.db import uid, pprint

# The main purpose of the pattern module is to facilitate automated processes
# for (text) data acquisition and (linguistical) data mining.
# Often, this involves a tangle of messy text files and custom formats to store the data.
# The Datasheet class offers a useful matrix (cfr. MS Excel) in Python code.
# It can be saved as a CSV text file that is both human/machine readable.
# See also: examples/01-web/03-twitter.py

# A Datasheet can have headers: a (name, type)-tuple for each column.
# In this case, imported columns will automatically map values to the defined type.
# Supported values that are imported and exported correctly:
# str, unicode, int, float, bool, Date, None
# For other data types, custom encoder and decoder functions can be used.

ds = Datasheet(rows=[
    [uid(), "broccoli",  "vegetable"],
    [uid(), "turnip",    "vegetable"],
    [uid(), "asparagus", "vegetable"],
    [uid(), "banana",    "fruit"],
], fields=[
      ("id", INTEGER),  # Define the column headers.
    ("name", STRING),
    ("type", STRING)
])

print(ds.rows[0])     # A list of rows.
print(ds.columns[1])  # A list of columns, where each column is a list of values.
print(ds.name)
print("")

# Columns can be manipulated directly like any other Python list.
# This can be slow for large tables. If you need a fast way to do matrix math,
# use numpy (http://numpy.scipy.org/) instead.
# The purpose of Table is data storage.
ds.columns.append([
    "green",
    "purple",
    "white",
    "yellow"
], field=("color", STRING))

# Save as a comma-separated (unicode) text file.
ds.save("food.txt", headers=True)

# Load a table from file.
ds = Datasheet.load("food.txt", headers=True)

pprint(ds, truncate=50, padding=" ", fill=".")
print("")
print(ds.fields)
