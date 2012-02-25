#### PATTERN | METRICS #############################################################################
# coding: utf-8
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

from time import time
from math import sqrt, floor, modf

### PROFILER #######################################################################################

def duration(function, *args, **kwargs):
    """ Returns the running time of the given function, in seconds.
    """
    t = time()
    function(*args, **kwargs)
    return time() - t

def profile(function, *args, **kwargs):
    """ Returns the performance statistics (as a string) of the given Python function.
    """
    def run():
        function(*args, **kwargs)
    try:
        import cProfile as profile
    except:
        import profile
    import pstats
    import os
    import sys; sys.modules["__main__"].__profile_run__ = run
    id = function.__name__ + "()"
    profile.run("__profile_run__()", id)
    p = pstats.Stats(id)
    p.stream = open(id, "w")
    p.sort_stats("time").print_stats(20)
    p.stream.close()
    s = open(id).read()
    os.remove(id)
    return s

### PRECISION & RECALL #############################################################################
# - recall: how good a system is at retrieving relevant results.
# - precision: how good it is at filtering out irrelevant results (e.g., bad web search results).

ACCURACY, PRECISION, RECALL, F1_SCORE = "accuracy", "precision", "recall", "F1-score"

def confusion_matrix(match=lambda document:False, documents=[(None,False)]):
    """ Returns the reliability of a binary classifier, as a tuple with the amount of 
        true positives (TP), true negatives (TN), false positives (FP), false negatives (FN).
        The classifier is a function that returns True or False for a document.
        The list of documents contains (document, bool)-tuples,
        where True means a document that should be identified as relevant (True) by the classifier.
    """
    TN = TP = FN = FP = 0
    for document, b1 in documents:
        b2 = match(document)
        if b1 and b2:
            TP += 1 # true positive
        elif not b1 and not b2:
            TN += 1 # true negative
        elif not b1 and b2:
            FP += 1 # false positive (type I error)
        elif b1 and not b2:
            FN += 1 # false negative (type II error)
    return TP, TN, FP, FN

def test(match=lambda document:False, documents=[]):
    """ Returns an (accuracy, precision, recall, F1-score)-tuple.
    """
    TP, TN, FP, FN = confusion_matrix(match, documents)
    a = float(TP+TN) / ((TP+TN+FP+FN) or 1)
    p = float(TP) / ((TP+FP) or 1)
    r = float(TP) / ((TP+FN) or 1)
    f = 2 * p * r / ((p + r) or 1)
    return (a, p, r, f)

def accuracy(match=lambda document:False, documents=[]):
    """ Returns the percentage of correct classifications (true positives + true negatives).
    """
    return test(match, documents)[0]

def precision(match=lambda document:False, documents=[]):
    """ Returns the percentage of correct positive classifications.
    """
    return test(match, documents)[1]

def recall(match=lambda document:False, documents=[]):
    """ Returns the percentage of positive cases correctly classified as positive.
    """
    return test(match, documents)[2]
    
def F1(match=lambda document:False, documents=[]):
    """ Returns the harmonic mean of precision and recall.
    """
    return test(match, documents)[3]
    
def F(match=lambda document:False, documents=[], beta=1):
    """ Returns the weighted harmonic mean of precision and recall,
        where recall is beta times more important than precision.
    """
    a, p, r, f = test(match, documents)
    return (beta**2 + 1) * p * r / ((beta**2 * p + r) or 1)

### AGREEMENT ######################################################################################
# +1.0 = total agreement between voters
# +0.0 = votes based on random chance
# -1.0 = total disagreement

def fleiss_kappa(m):
    """ Returns the reliability of agreement as a number between -1.0 and +1.0,
        for a number of votes per category per task.
        The given m is a list in which each row represents a task.
        Each task is a list with the number of votes per category.
        Each column represents a category.
        For example, say 5 people are asked to vote "cat" and "dog" as "good" or "bad":
         m = [# + -        
               [3,2], # cat
               [5,0]] # dog
    """
    N = len(m)    # Total number of tasks.
    n = sum(m[0]) # The number of votes per task.
    k = len(m[0]) # The number of categories.
    assert all(sum(row) == n for row in m[1:]), "numer of votes for each task differs"
    # p[j] = the proportion of all assignments which were to the j-th category.
    p = [sum(m[i][j] for i in xrange(N)) / float(N*n) for j in xrange(k)]
    # P[i] = the extent to which voters agree for the i-th subject.
    P = [(sum(m[i][j]**2 for j in xrange(k)) - n) / float(n * (n-1)) for i in xrange(N)]
    # Pm = the mean of P[i] and Pe.
    Pe = sum(pj**2 for pj in p)
    Pm = sum(P) / N
    K = (Pm - Pe) / ((1 - Pe) or 1) # kappa
    return K
    
agreement = fleiss_kappa

### STRING SIMILARITY ##############################################################################

def levenshtein(string1, string2):
    """ Measures the amount of difference between two strings.
        The return value is the number of operations (insert, delete, replace)
        required to transform string a into string b.
    """
    # http://hetland.org/coding/python/levenshtein.py
    n, m = len(string1), len(string2)
    if n > m: 
        # Make sure n <= m to use O(min(n,m)) space.
        string1, string2, n, m = string2, string1, m, n
    current = range(n+1)
    for i in range(1, m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1, n+1):
            insert, delete, replace = previous[j]+1, current[j-1]+1, previous[j-1]
            if string1[j-1] != string2[i-1]:
                replace += 1
            current[j] = min(insert, delete, replace)
    return current[n]
    
edit_distance = levenshtein

def levenshtein_similarity(string1, string2):
    """ Returns the similarity of string1 and string2 as a number between 0.0 and 1.0.
    """
    return 1 - levenshtein(string1, string2) / float(max(len(string1),  len(string2), 1.0))
    
def dice_coefficient(string1, string2):
    """ Returns the similarity between string1 and string1 as a number between 0.0 and 1.0,
        based on the number of shared bigrams, e.g., "night" and "nacht" have one common bigram "ht".
    """
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s)-1))
    nx = bigrams(string1)
    ny = bigrams(string2)
    nt = nx.intersection(ny)
    return 2.0 * len(nt) / ((len(nx) + len(ny)) or 1)

LEVENSHTEIN, DICE = "levenshtein", "dice"
def similarity(string1, string2, metric=LEVENSHTEIN):
    """ Returns the similarity of string1 and string2 as a number between 0.0 and 1.0,
        using LEVENSHTEIN edit distance or DICE coefficient.
    """
    if metric == LEVENSHTEIN:
        return levenshtein_similarity(string1, string2)
    if metric == DICE:
        return dice_coefficient(string1, string2)

### STRING READABILITY #############################################################################
# 0.9-1.0 = easily understandable by 11-year old.
# 0.6-0.7 = easily understandable by 13- to 15-year old.
# 0.0-0.3 = best understood by university graduates.

def flesch_reading_ease(string):
    """ Returns the readability of the string as a value between 0.0-1.0:
        0.30-0.50 (difficult) => 0.60-0.70 (standard) => 0.90-1.00 (very easy).
    """
    def count_syllables(word, vowels="aeiouy"):
        n = 0
        p = False # True if the previous character was a vowel.
        for ch in word.endswith("e") and word[:-1] or word:
            v = ch in vowels
            n += int(v and not p)
            p = v
        return n
    if len(string) <  3:
        return 1.0
    string = string.strip()
    string = string.strip("\"'().")
    string = string.lower()
    string = string.replace("!", ".")
    string = string.replace("?", ".")
    string = string.replace(",", " ")
    string = string.replace("\n", " ")
    y = [count_syllables(w) for w in string.split(" ") if w != ""]
    w = len([w for w in string.split(" ") if w != ""])
    s = len([s for s in string.split(".") if len(s) > 2])
    #R = 206.835 - 1.015 * w/s - 84.6 * sum(y)/w
    # Use the Farr, Jenkins & Patterson algorithm,
    # which uses simpler syllable counting (count_syllables() is the weak point here). 
    R = 1.599 * sum(1 for v in y if v == 1) * 100 / w - 1.015*w/s - 31.517
    R = max(0.0, min(R*0.01, 1.0))
    return R

readability = flesch_reading_ease

### STATISTICS #####################################################################################

def mean(list):
    """ Returns the arithmetic mean of the given list of values.
        For example: mean([1,2,3,4]) = 10/4 = 2.5.
    """
    return float(sum(list)) / (len(list) or 1)

avg = mean

def median(list):
    """ Returns the value that separates the lower half from the higher half of values in the list.
    """
    s = sorted(list)
    n = len(list)
    if n == 0:
        raise ValueError, "median() arg is an empty sequence"
    if n % 2 == 0:
        return float(s[(n/2)-1] + s[n/2]) / 2
    return s[n/2]

def variance(list, sample=True):
    """ Returns the variance of the given list of values.
        The variance is the average of squared deviations from the mean.
    """
    # Sample variance = E((xi-m)^2) / (n-1)
    # Population variance = E((xi-m)^2) / n
    m = mean(list)
    return sum((x-m)**2 for x in list) / (len(list)-int(sample) or 1)
    
def standard_deviation(list, *args, **kwargs):
    """ Returns the standard deviation of the given list of values.
        Low standard deviation => values are close to the mean.
        High standard deviation => values are spread out over a large range.
    """
    return sqrt(variance(list, *args, **kwargs))
    
stdev = standard_deviation

def histogram(list, k=10, range=None):
    """ Returns a dictionary with k items: {(start, stop): [values], ...},
        with equal (start, stop) intervals between min(list) => max(list).
    """
    # To loop through the intervals in sorted order, use:
    # for (i,j), values in sorted(histogram(list).items()):
    #     m = i + (j-i)/2 # midpoint
    #     print i, j, m, values
    if range is None:
        range = (min(list), max(list))
    k = max(int(k), 1)
    w = float(range[1] - range[0] + 0.000001) / k # interval (bin width)
    h = [[] for i in xrange(k)]
    for x in list:
        i = int(floor((x-range[0]) / w))
        if 0 <= i < len(h): 
            #print x, i, "(%.2f, %.2f)" % (range[0]+w*i, range[0]+w+w*i)
            h[i].append(x)
    return dict(((range[0]+w*i, range[0]+w+w*i), v) for i, v in enumerate(h))

def moment(list, k=1):
    """ Returns the kth central moment of the given list of values
        (2nd central moment = variance, 3rd and 4th are used to define skewness and kurtosis).
    """
    if k == 1:
        return 0.0
    m = mean(list)
    return sum([(x-m)**k for x in list]) / (len(list) or 1)
    
def skewness(list):
    """ Returns the degree of asymmetry of the given list of values:
        > 0.0 => relatively few values are higher than mean(list),
        < 0.0 => relatively few values are lower than mean(list),
        = 0.0 => evenly distributed on both sides of the mean (= normal distribution).
    """
    # Distributions with skew and kurtosis between -1 and +1 
    # can be considered normal by approximation.
    return moment(list, 3) / (moment(list, 2) ** 1.5 or 1)

skew = skewness

def kurtosis(list):
    """ Returns the degree of peakedness of the given list of values:
        > 0.0 => sharper peak around mean(list) = more infrequent, extreme values,
        < 0.0 => wider peak around mean(list),
        = 0.0 => normal distribution,
        =  -3 => flat
    """
    return moment(list, 4) / (moment(list, 2) ** 2.0 or 1) - 3

#a = 1
#b = 1000
#U = [float(i-a)/(b-a) for i in range(a,b)] # uniform distribution
#print abs(-1.2 - kurtosis(U)) < 0.0001

def quantile(list, p=0.5, sort=True, a=1, b=-1, c=0, d=1):
    """ Returns the value from the sorted list at point p (0.0-1.0).
        If p falls between two items in the list, the return value is interpolated.
        For example, quantile(list, p=0.5) = median(list)
    """
    # Based on: Ernesto P. Adorio, http://adorio-research.org/wordpress/?p=125
    # Parameters a, b, c, d refer to the algorithm by Hyndman and Fan (1996):
    # http://stat.ethz.ch/R-manual/R-patched/library/stats/html/quantile.html
    s = sort is True and sorted(list) or list
    n = len(list)
    f, i = modf(a + (b+n) * p - 1)
    if n == 0:
        raise ValueError, "quantile() arg is an empty sequence"
    if f == 0: 
        return float(s[int(i)])
    if i < 0: 
        return float(s[int(i)])
    if i >= n: 
        return float(s[-1])
    i = int(floor(i))
    return s[i] + (s[i+1] - s[i]) * (c + d * f)

#print quantile(range(10), p=0.5) == median(range(10))

def boxplot(list, **kwargs):
    """ Returns a tuple (min(list), Q1, Q2, Q3, max(list)) for the given list of values.
        Q1, Q2, Q3 are the quantiles at 0.25, 0.5, 0.75 respectively.
    """
    # http://en.wikipedia.org/wiki/Box_plot
    kwargs.pop("p", None)
    kwargs.pop("sort", None)
    s = sorted(list)
    Q1 = quantile(s, p=0.25, sort=False, **kwargs)
    Q2 = quantile(s, p=0.50, sort=False, **kwargs)
    Q3 = quantile(s, p=0.75, sort=False, **kwargs)
    return float(min(s)), Q1, Q2, Q3, float(max(s))
