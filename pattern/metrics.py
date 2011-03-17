#### PATTERN | STAT ##################################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

### AGREEMENT ########################################################################################
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

### STRING SIMILARITY ################################################################################

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
    if metric == LEVENSHTEIN:
        return levenshtein_similarity(string1, string2)
    if metric == DICE:
        return dice_coefficient(string1, string2)
