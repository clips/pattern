import os, sys; sys.path.insert(0, os.path.join("..", "..", ".."))

from pattern.table import Table
from pattern.table import uid, pprint, COUNT, FIRST

# This example demonstrates how table values can be grouped.

t = Table(rows=[
#   0-ID    1-NAME       2-TYPE       3-COLOR
    [uid(), "broccoli",  "vegetable", "green" ],
    [uid(), "turnip",    "vegetable", "purple"],
    [uid(), "asparagus", "vegetable", "white" ],
    [uid(), "banana",    "fruit",     "yellow"],
    [uid(), "orange",    "fruit",     "orange"]
])

g = t.copy(columns=[2,0]) # A copy with only the type and id columns.
g = g.group(0, COUNT)     # Group by type, count rows per type.
                          # Group functions: FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV.
pprint(g)
print

# This will group by type and concatenate all names per type:
g = t.copy(columns=[2,1])
g = g.group(0, function=lambda list: "/".join(list))

pprint(g)
print

# This will group by type, count the id's per type, and concatenate all names per type.
# Each column is given a different grouping function.
# For the column one whose values is grouped, simply use FIRST.
g = t.copy(columns=[2,0,1])
g = g.group(0, function=(FIRST, COUNT, lambda list: "/".join(list)))
g.columns[1].sort() # Sort by count.

pprint(g)
