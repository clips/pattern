import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.table import Table
from pattern.table import uid, pprint

# The main purpose of the pattern module is to facilitate automated processes
# for (text) data acquisition and (linguistical) data mining.
# Often, this involves a tangle of messy text files and custom formats to store the data.
# The Table class offers a useful datasheet (cfr. MS Excel) in Python code.
# It can be saved as a CSV text file that is both human/machine readable.
# See also: examples/01-web/03-twitter.py
# Supported values that are imported and exported correctly:
# str, unicode, int, float, bool, None
# For other data types, custom encoder and decoder functions can be used.

t = Table(rows=[
    [uid(), "broccoli",  "vegetable"],
    [uid(), "turnip",    "vegetable"],
    [uid(), "asparagus", "vegetable"],
    [uid(), "banana",    "fruit"    ],
])

print t.rows[0]    # A list of rows.
print t.columns[1] # A list of columns, where each column is a list of values.
print

# Columns can be manipulated directly like any other Python list.
# This can be slow for large tables. If you need a fast way to do matrix math,
# use numpy (http://numpy.scipy.org/) instead. 
# The purpose of Table is data storage.
t.columns.append([
    "green",
    "purple",
    "white",
    "yellow"
])

# Save as a comma-separated (unicode) text file.
t.save("food.txt") 

# Load a table from file.
t = Table.load("food.txt")

pprint(t, truncate=50, padding=" ", fill=".")
