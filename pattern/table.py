#### PATTERN | EN | TABLE ############################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

######################################################################################################

import csv

from cStringIO import StringIO
from codecs    import BOM_UTF8
from datetime  import datetime, timedelta
from math      import sqrt

try:
    from email.utils import parsedate_tz, mktime_tz
except:
    from email.Utils import parsedate_tz, mktime_tz

_UID = 0
def uid():
    global _UID; _UID+=1; return _UID

#### STRING FUNCTIONS ################################################################################

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

def decode_utf8(string):
    """ Returns the given string as a unicode string (if possible).
    """
    if isinstance(string, str):
        try: 
            return string.decode("utf-8")
        except:
            return string
    return unicode(string)
    
def encode_utf8(string):
    """ Returns the given string as a Python byte string (if possible).
    """
    if isinstance(string, unicode):
        try: 
            return string.encode("utf-8")
        except:
            return string
    return str(string)

def _eval(string):
    """ Casts the string to int, float, bool or None if applicable.
    """
    if not isinstance(string, basestring):
        return string
    if string == "None": 
        return None
    if string == "True":
        return True
    if string == "False":
        return False
    if string.isdigit():
        return int(string)
    try:
        return float(string)
    except ValueError:
        return decode_utf8(string)

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

FIRST = lambda list: list[+0]
LAST  = lambda list: list[-1]
COUNT = lambda list: len(list)
MAX   = lambda list: max(list)
MIN   = lambda list: min(list)
SUM   = lambda list: sum(list)
AVG   = lambda list: avg(list)
STDEV = lambda list: stdev(list)

#### DATE ############################################################################################

NOW = "now"

# Date formats can be found in the Python documentation:
# http://docs.python.org/library/time.html#time.strftime
DEFAULT = "%Y-%m-%d %H:%M:%S"
formats = [
    DEFAULT,               # 2010-09-21 09:27:01  => table.py
    "%Y-%m-%dT%H:%M:%SZ",  # 2010-09-20T09:27:01Z => Bing
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d %B %Y",
    "%B %d %Y",            # July 20 1969
    "%B %d, %Y",           # July 20, 1969
]

class DateError(Exception):
    pass

class Date(datetime):
    # A wrapper for datetime with an internal string format.
    format = DEFAULT
    def __str__(self):
        return self.strftime(self.format)
    def __repr__(self):
        return repr(self.__str__())
    def __add__(self, time):
        d = datetime.__add__(self, time)
        return date(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, self.format)
            

def date(*args, **kwargs):
    """ Returns a Date from the given parameters:
        - date(format=Date.format) => now
        - date(int)
        - date(string)
        - date(string, format=Date.format)
        - date(string, inputformat, format=Date.format)
        - date(year, month, day, hours, minutes, seconds, format=Date.format)
        If a string is given without an explicit input format, all known formats will be tried.
    """
    d = None
    if len(args) == 0 or args[0] == NOW:
        # No parameters, return NOW.
        d = Date.now()
    elif len(args) == 1 \
     and isinstance(args[0], int) \
      or isinstance(args[0], basestring) and args[0].isdigit():
        # One parameter, an int or string timestamp.
        d = Date.fromtimestamp(int(args[0]))
    elif len(args) == 1 and isinstance(args[0], basestring):
        # One parameter, a date string for which we guess the input format.
        # First, try to parse as a RFC2822 date.
        # Otherwise, try to parse with a list of known formats.
        try: d = Date.fromtimestamp(mktime_tz(parsedate_tz(args[0])))
        except:
            for f in (kwargs.get("format") or []) + formats:
                try: d = Date.strptime(args[0], f); break
                except:
                    pass
        if d is None:
            raise DateError, "unknown date format for %s" % repr(args[0])
    elif len(args) == 2 and isinstance(args[0], basestring):
        # Two parameters, a date string and an explicit input format.
        d = Date.strptime(args[0], args[1])
    else:
        # Many parameters: year, month, day, hours, minutes, seconds.
        d = Date(*args[:7], **kwargs)
    d.format = kwargs.get("format") or len(args)>7 and args[7] or Date.format
    return d
    
def time(days=0, seconds=0, minutes=0, hours=0):
    return timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours)

#### TABLE ###########################################################################################

ALL = "all"

class Table(list):
    
    def __init__(self, rows=[]):
        """ A matrix of rows and columns, where each row and column can be retrieved as a list.
            Values can be any kind of Python object, but only string, int, float, bool and None
            are correctly imported from file with Table.load().
        """
        self._rows, self._columns = Rows(self), Columns(self)
        self._m = 0 # Number of columns per row, see Table.insert().
        self.extend(rows)
    
    def _get_rows(self):
        return self._rows
    def _set_rows(self, rows):
        # Table.rows property can't be set, except in special cases such as Table.rows += row.
        if isinstance(rows, Rows) and rows._table == self:
            self._rows = rows; return
        raise AttributeError, "can't set attribute"
    rows = property(_get_rows, _set_rows)
    
    def _get_columns(self):
        return self._columns
    def _set_columns(self, columns):
        # Table.columns property can't be set, except in special cases such as Table.columns += column.
        if isinstance(columns, Columns) and columns._table == self:
            self._columns = columns; return
        raise AttributeError, "can't set attribute"
    columns = cols = property(_get_columns, _set_columns)

    def __setitem__(self, index, value):
        """ Sets an item or row in the table.
            For Table[i] = v, sets the row at index i to v.
            For Table[i,j] = v, sets the value in row i and column j to v.
        """
        if isinstance(index, tuple):
            list.__getitem__(self, index[0])[index[1]] = value
        elif isinstance(index, int):
            self.pop(index)
            self.insert(index, value)
        else:
            raise TypeError, "Table indices must be int or tuple"
    
    def __getitem__(self, index):
        """ Returns an item, row or slice from the table.
            For Table[i], returns the row at the given index.
            For Table[i,j], returns the value in row i and column j.
        """
        if isinstance(index, int):
            return list.__getitem__(self, index)
        if isinstance(index, tuple):
            return list.__getitem__(self, index[0])[index[1]]
        raise TypeError, "Table indices must be int or tuple"

    def __getslice__(self, i, j):
        return Table(rows=[list.__getitem__(self, i) for i in range(i, j)])
            
    def __delitem__(self, index):
        self.pop(index)

    # table1 = table2 + table3
    # table1 = [[...],[...]] + table2
    # table1 += table2
    def __add__(self, table):
        t = self.copy(); t.extend(table); return t
    def __radd__(self, table):
        t = Table(table); t.extend(self); return t
    def __iadd__(self, table):
        self.extend(table); return self

    def insert(self, i, row, default=None):
        """ Inserts the given row into the table.
            Missing columns at the end (right) will be filled with the default value.
        """
        try: row = [v for v in row] # Creates a copy of the row (fast + safe for generators and Columns).
        except:
            raise TypeError, "Table.insert(x): x must be list"
        list.insert(self, i, row)
        m = max((len(self) > 1 and self._m or 0, len(row)))
        if len(row) < m:
            row.extend([default] * (m-len(row)))
        if self._m < m:
            # The given row might have more columns than the rows in the table.
            # Performance takes a hit when these rows have to be expanded:
            for row in self:
                if len(row) < m:
                    row.extend([default] * (m-len(row)))
        self._m = m
        
    def append(self, row, default=None, _m=None):
        self.insert(len(self), row, default)
    def extend(self, rows, default=None):
        for row in rows:
            self.insert(len(self), row, default)
            
    def group(self, j, function=FIRST, key=lambda v: v):
        """ Returns a table with unique values in column j by grouping rows with the given function.
            The function takes a list of column values as input and returns a single value,
            e.g. FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV.
            The function can also be a list of functions (one for each column).
            TypeError will be raised when the function cannot handle the data in a column.
            The key argument can be used to map the values in column j, for example: 
            key=lambda date: date.year to group Date objects by year.
        """
        if not isinstance(function, (tuple, list)):
            function = [function] * self._m
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
        return Table(rows=u)
                
    def map(self, function=lambda item: item):
        """ Applies the given function to each item in the table.
        """
        for i, row in enumerate(self):
            for j, item in enumerate(row):
                row[j] = function(item)

    def save(self, path, separator=",", encoder=lambda j,v: v):
        """ Exports the table to a unicode text file at the given path.
            Rows in the file are separated with a newline.
            Columns in a row are separated with the given separator (by default, comma).
            For data types other than string, int, float, bool or None, a custom string encoder can be given.
        """
        # csv.writer will handle str, int, float and bool:
        s = StringIO()
        w = csv.writer(s, delimiter=separator)
        w.writerows([[encode_utf8(encoder(j,v)) for j,v in enumerate(row)] for row in self])
        f = open(path, "wb")
        f.write(BOM_UTF8)
        f.write(s.getvalue())
        f.close()

    @classmethod
    def load(self, path, separator=",", decoder=lambda j,v: v):
        """ Returns a table from the data in the given text file.
            Rows are expected to be separated by a newline. 
            Columns are expected to be separated by the given separator (by default, comma).
            Strings will be converted to int, float, bool or None if possible.
            For other data types, a custom string decoder can be given.
        """
        # Date objects are saved and loaded as strings, but it is easy to convert these back to dates:
        # Table.columns[x].map(lambda s: date(s))
        data = open(path, "rb").read().lstrip(BOM_UTF8)
        data = StringIO(data)
        data = [row for row in csv.reader(data, delimiter=separator)]
        data = [[_eval(decoder(j,v)) for j,v in enumerate(row)] for row in data]
        return Table(data)

    def slice(self, i, j, n, m):
        """ Returns a Table copy starting at row i and column j and spanning n rows and m columns.
        """
        return Table(rows=[list.__getitem__(self, i)[j:j+m] for i in range(i, i+n)])

    def copy(self, rows=ALL, columns=ALL):
        """ Returns a copy of the table from a selective list of row and/or column indices.
        """
        if rows == ALL and columns == ALL:
            return Table(rows=self)
        if rows == ALL:
            return Table(rows=zip(*(self.columns[j] for j in columns)))
        if columns == ALL:
            return Table(rows=(self.rows[i] for i in rows))
        z = zip(*(self.columns[j] for j in columns))
        return Table(rows=(z[i] for i in rows))
        
    def index(self, column):
        # See the index() function below.
        return index(column)

#--- ROWS --------------------------------------------------------------------------------------------
# Table.rows mimics the operations on Table:

class Rows(list):
    
    def __init__(self, table):
        self._table = table    

    def __setitem__(self, i, row):
        self._table.pop(i)
        self._table.insert(i, row)
    def __getitem__(self, i):
        return list.__getitem__(self._table, i)
    def __delitem__(self, i):
        self.pop(i)
    def __len__(self):
        return len(self._table)
    def __iter__(self):
        for i in xrange(len(self)): yield list.__getitem__(self._table, i)
    def __repr__(self):
        return repr(self._table)
    def __add__(self, row):
        raise TypeError, "unsupported operand type(s) for +: 'Table.rows' and '%s'" % row.__class__.__name__
    def __iadd__(self, row):
        self.append(row); return self

    def insert(self, i, row, default=None):
        self._table.insert(i, row, default)
    def append(self, row, default=None):
        self._table.append(row, default)    
    def extend(self, rows, default=None):
        self._table.extend(rows, default)
    def remove(self, row):
        self._table.remove(row)
    def pop(self, i):
        return self._table.pop(i)
        
    def count(self, row):
        return self._table.count(row)
    def index(self, row):
        return self._table.index(row)
    def sort(self, cmp=None, key=None, reverse=False):
        self._table.sort(cmp, key, reverse)
    def reverse(self):
        self._table.reverse()
        
    def swap(self, i1, i2):
        self[i1], self[i2] = self[i2], self[i1]

#--- COLUMNS -----------------------------------------------------------------------------------------

class Columns(list):
    
    def __init__(self, table):
        self._table = table
        self._cache = {} # Keep a reference to Column objects generated with Table.columns[j].
                         # This way we can unlink them when they are deleted.

    def __setitem__(self, j, column):
        self.pop(j)
        self.insert(j, column)
    def __getitem__(self, j):
        if j < 0: j += len(self) # Columns[-1]
        if j >= len(self): 
            raise IndexError, "list index out of range"
        return self._cache.setdefault(j, Column(self._table, j))
    def __delitem__(self, j):
        self.pop(j)
    def __len__(self):
        return len(self._table) > 0 and len(self._table[0]) or 0
    def __iter__(self):
        for i in xrange(len(self)): yield self.__getitem__(i)
    def __repr__(self):
        return repr(list(iter(self)))    
    def __add__(self, column):
        raise TypeError, "unsupported operand type(s) for +: 'Table.columns' and '%s'" % column.__class__.__name__
    def __iadd__(self, column):
        self.append(column); return self

    def insert(self, j, column, default=None):
        """ Inserts the given column into the table.
            Missing rows at the end (bottom) will be filled with the default value.
        """
        try: column = [v for v in column]
        except:
            raise TypeError, "Table.columns.insert(x): x must be list"
        column = column + [default] * (len(self._table) - len(column))
        if len(column) > len(self._table):
            self._table.extend([[None]] * (len(column)-len(self._table)))
        for i, row in enumerate(self._table):
            row.insert(j, column[i])
        self._table._m += 1 # Increase column count.

    def append(self, column, default=None):
        self.insert(len(self), column, default)
    def extend(self, columns, default=None):
        for column in columns: 
            self.insert(len(self), column, default)
    
    def remove(self, column):
        if isinstance(column, Column) and column._table == self._table:
            self.pop(column._j); return
        raise ValueError, "list.remove(x): x not in list"
    
    def pop(self, j):
        column = list(self[j]) # Return a list copy.
        for row in self._table: 
            row.pop(j)
        # At one point a Column object was created with Table.columns[j].
        # It might still be in use somewhere, so we unlink it from the table:
        self._cache[j]._table = Table(rows=[[v] for v in column])
        self._cache[j]._j = 0
        self._cache.pop(j)
        for j in range(j+1, len(self)+1):
            if j in self._cache:
                # Shift the Column objects on the right to the left.
                self._cache[j-1] = self._cache.pop(j)
                self._cache[j-1]._j = j-1
        self._table._m -= 1 # Decrease column count.
        return column

    def count(self, column):
        return len([True for c in self if c == column])
    
    def index(self, column):
        if isinstance(column, Column) and column._table == self._table:
            return column._j
        raise ValueError, "list.index(x): x not in list"
    
    def sort(self, cmp=None, key=None, reverse=False, order=None):
        # This makes most sense if the order in which columns should appear is supplied.
        o = order and order or _order(self, cmp, key, reverse)
        for i, row in enumerate(self._table):
            # The main difficulty is modifying each row in-place,
            # since other variables might be referring to it.
            r=list(row); [row.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
    
    def swap(self, j1, j2):
        self[j1], self[j2] = self[j2], self[j1]

#--- COLUMN ------------------------------------------------------------------------------------------

class Column(list):
    
    def __init__(self, table, j):
        """ A dynamic column in a Table.
            If the actual column is deleted with Table.columns.remove() or Table.columms.pop(),
            the Column object will be orphaned (i.e. it is no longer part of the Table).
        """
        self._table = table
        self._j = j
    
    def __getitem__(self, i):
        return list.__getitem__(self._table, i)[self._j]
    def __setitem__(self, i, value):
        list.__getitem__(self._table, i)[self._j] = value
    def __len__(self):
        return len(self._table)
    def __iter__(self): # Can be put more simply but optimized for performance:
        for i in xrange(len(self)): yield list.__getitem__(self._table, i)[self._j]
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
        return isinstance(column, Column) and column._table == self._table and column._j == self._j
    def __ne__(self, column):
        return not self.__eq__(column)
    def __add__(self, value):
        raise TypeError, "unsupported operand type(s) for +: 'Table.columns[x]' and '%s'" % column.__class__.__name__
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
        """ Removes the table row that has the given value in this column.
        """
        for i, v in enumerate(self):
            if v == value:
                self._table.pop(i); return
        raise ValueError, "list.remove(x): x not in list"
        
    def pop(self, i):
        """ Remove the entire row from the table and return the value at the given index.
        """
        row = self._table.pop(i); return row[self._j]

    def sort(self, cmp=None, key=None, reverse=False):
        """ Sorts the rows in the table according to the values in this column,
            e.g. clicking ascending / descending on a column header in a datasheet view.
        """
        o = order(list(self), cmp, key, reverse)
        # Modify the table in place, more than one variable may be referencing it:
        r=list(self._table); [self._table.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
        
    def insert(self, i, value, default=None):
        """ Inserts the given value in the column.
            This will create a new row in the table, where other columns are set to the default.
        """
        self._table.insert(i, [default]*self._j + [value] + [default]*(len(self._table)-self._j-1))
        
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
        self._table.swap(i1, i2)
        
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
                    

#--- INDEX -------------------------------------------------------------------------------------------

def index(list):
    """ Returns a dictionary of (value, index)-items that is efficient for lookup operations:
        - value in index <=> value in list
        - index[value] <=> list.index(value)
        For example, this can be used to append a batch of rows to a large table with a unique column.
        An index can be created for the column and used to check if the new row can be added:
         X = index(Table.columns(j))
         u = [row for row in rows if row[j] not in X]
         Table.rows.extend(u)
        Note that the index is "static": if the list changes the index will have to recreated.
    """
    n = len(list)
    return dict((v, n-i-1) for i, v in enumerate(reversed([x for x in list])))

#-----------------------------------------------------------------------------------------------------

def flip(table):
    return Table(rows=table.columns)

def pprint(table, truncate=40, padding=" ", fill="."):
    """ Prints a string where the rows in the table are organized in outlined columns.
    """
    # Calculate the width of each column, based on the longest field in each column.
    # Long fields can be split across different lines, so we need to check each line.
    w = [0 for column in table.columns]
    R = []
    for i, row in enumerate(table.rows):
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
