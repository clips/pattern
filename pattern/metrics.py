#### PATTERN | METRICS #############################################################################
# coding: utf-8
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

from time import time
from math import sqrt, floor, modf, exp, pi, log

#### PROFILER ######################################################################################

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

#### PRECISION & RECALL ############################################################################
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

#### AGREEMENT #####################################################################################
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

#### STRING SIMILARITY #############################################################################

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

#### STRING READABILITY ############################################################################
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

#### STATISTICS ####################################################################################

#--- MEAN ------------------------------------------------------------------------------------------

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

#--- MOMENT ----------------------------------------------------------------------------------------

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

#--- QUANTILE --------------------------------------------------------------------------------------

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

#--- FISHER'S EXACT TEST ---------------------------------------------------------------------------

def fisher_exact_test(a, b, c, d, **kwargs):
    """ Fast implementation of Fisher's exact test (two-tailed).
        Returns the significance for the given 2x2 contingency table:
        < 0.05: significant
        < 0.01: very significant
        The following test shows a very significant correlation between gender & dieting:
        -----------------------------
        |             | men | women |
        |     dieting |  1  |   9   |
        | non-dieting | 11  |   3   |
        -----------------------------
        fisher_exact_test(a=1, b=9, c=11, d=3) => 0.0028
    """
    _cache = {}
    # Hypergeometric distribution.
    # (a+b)!(c+d)!(a+c)!(b+d)! / a!b!c!d!n! for n=a+b+c+d
    def p(a, b, c, d):
        return C(a + b, a) * C(c + d, c) / C(a + b + c + d, a + c)
    # Binomial coefficient.
    # n! / k!(n-k)! for 0 <= k <= n
    def C(n, k):
        if len(_cache) > 10000:
            _cache.clear()
        if k > n - k: # 2x speedup.
            k = n - k
        if 0 <= k <= n and (n, k) not in _cache:
            c = 1.0
            for i in range(1, int(k + 1)):
                c *= n - k + i
                c /= i
            _cache[(n, k)] = c # 3x speedup.
        return _cache.get((n, k), 0.0)
    # Probability of the given data.
    cutoff = p(a, b, c, d)
    # Probabilities of "more extreme" data, in both directions (two-tailed).
    # Based on: http://www.koders.com/java/fid868948AD5196B75C4C39FEA15A0D6EAF34920B55.aspx?s=252
    s = [cutoff] + \
        [p(a+i, b-i, c-i, d+i) for i in range(1, min(b, c) + 1)] + \
        [p(a-i, b+i, c+i, d-i) for i in range(1, min(a, d) + 1)]
    return sum(v for v in s if v <= cutoff) or 0.0
    
fisher_test = fisher_exact_test

FISHER, CHI2, LLR = "fisher", "chi2", "llr"
def significance(*args, **kwargs):
    """ Returns the significance for the given test (FISHER, CHI2, LLR).
    """
    test = kwargs.pop("test", FISHER)
    if test == FISHER:
        return fisher_exact_test(*args, **kwargs)
    if test == CHI2:
        return pearson_chi_squared_test(*args, **kwargs)[1]
    if test == LLR:
        return pearson_log_likelihood_ratio(*args, **kwargs)[1]

#--- PEARSON'S CHI-SQUARED TEST --------------------------------------------------------------------

LOWER = "lower"
UPPER = "upper" 

def _expected(observed):
    """ Returns the table of (absolute) expected frequencies
        from the given table of observed frequencies.
    """
    O = observed
    if len(O) == 0:
        return []
    if len(O) == 1:
        return [[sum(O[0]) / float(len(O[0]))] * len(O[0])]
    n = [sum(O[i]) for i in range(len(O))]
    m = [sum(O[i][j] for i in range(len(O))) for j in range(len(O[0]))]
    s = float(sum(n))
    # Each cell = row sum * column sum / total.
    return [[n[i] * m[j] / s for j in range(len(O[i]))] for i in range(len(O))]

def pearson_chi_squared_test(observed=[], expected=[], df=None, tail=UPPER):
    """ Returns (X2, P) for the n x m observed and expected data (containing absolute frequencies).
        If expected is None, an equal distribution over all classes is assumed.
        If df is None, it is the number of classes-1 (i.e., len(observed[0]) - 1).
        P < 0.05: significant
        P < 0.01: very significant
        This means that if P < 5%, the data is unevenly distributed (e.g., biased).
        The following test shows that the die is fair:
        ---------------------------------------
        |       | 1  | 2  | 3  | 4  | 5  | 6  | 
        | rolls | 22 | 21 | 22 | 27 | 22 | 36 |
        ---------------------------------------
        chi2([[22, 21, 22, 27, 22, 36]]) => (6.72, 0.24)
    """
    # The P-value (upper tail area) is obtained from the incomplete gamma integral:
    # P(X2 | v) = gammai(v/2, x/2) with v degrees of freedom.
    # See: Cephes, https://github.com/scipy/scipy/blob/master/scipy/special/cephes/chdtr.c
    O  = observed
    E  = expected or _expected(observed)
    df = df or (len(O) > 0 and len(O[0])-1 or 0)
    X2 = 0.0
    for i in range(len(O)):
        for j in range(len(O[i])):
            if O[i][j] != 0 and E[i][j] != 0:
                X2 += (O[i][j] - E[i][j]) ** 2.0 / E[i][j]
    P = gammai(df * 0.5, X2 * 0.5, tail)
    return (X2, P)
    
chi2 = chi_squared = pearson_chi_squared_test

def chi2p(X2, df=1, tail=UPPER):
    """ Returns P-value for given X2 and degrees of freedom.
    """
    return gammai(df * 0.5, X2 * 0.5, tail)

#o, e = [[44,56]], [[50,50]]
#assert round(chi_squared(o, e)[0], 4)  == 1.4400
#assert round(chi_squared(o, e)[1], 4)  == 0.2301

#--- PEARSON'S LOG LIKELIHOOD RATIO APPROXIMATION --------------------------------------------------

def pearson_log_likelihood_ratio(observed=[], expected=[], df=None, tail=UPPER):
    """ Returns (G, P) for the n x m observed and expected data (containing absolute frequencies).
        If expected is None, an equal distribution over all classes is assumed.
        If df is None, it is the number of classes-1 (i.e., len(observed[0]) - 1).
        P < 0.05: significant
        P < 0.01: very significant
    """
    O  = observed
    E  = expected or _expected(observed)
    df = df or (len(O) > 0 and len(O[0])-1 or 0)
    G  = 0.0
    for i in range(len(O)):
        for j in range(len(O[i])):
            if O[i][j] != 0 and E[i][j] != 0:
                G += O[i][j] * log(O[i][j] / E[i][j])
    G = G * 2
    P = gammai(df * 0.5, G * 0.5, tail)
    return (G, P)
    
llr = likelihood = pearson_log_likelihood_ratio

#### SPECIAL FUNCTIONS #############################################################################

#--- INCOMPLETE GAMMA FUNCTION ---------------------------------------------------------------------
# Based on: http://www.johnkerl.org/python/sp_funcs_m.py.txt, Tom Loredo
# See also: http://www.mhtl.uwaterloo.ca/courses/me755/web_chap1.pdf

def gammaln(x):
    """ Returns the logarithm of the gamma function.
    """
    x = x - 1.0
    y = x + 5.5
    y = (x + 0.5) * log(y) - y
    n = 1.0
    for i in range(6):
        x += 1
        n += (76.18009173, -86.50532033, 24.01409822, -1.231739516e0, 0.120858003e-2, -0.536382e-5)[i] / x
    return y + log(2.50662827465 * n)
    
def gamma(x):
    return exp(gammaln(x))

def gammai(a, x, tail=UPPER):
    """ Returns the incomplete gamma function for LOWER or UPPER tail.
    """
    
    # Series approximation to the incomplete gamma function.
    def gs(a, x, epsilon=3.e-7, iterations=700):
        ln = gammaln(a)
        s = 1.0 / a
        d = 1.0 / a
        for i in range(1, iterations):
            d = d * x / (a + i)
            s = s + d
            if abs(d) < abs(s) * epsilon:
                return (s * exp(-x + a * log(x) - ln), ln)
        raise StopIteration, (abs(d), abs(s) * epsilon)
    
    # Continued fraction approximation of the incomplete gamma function.
    def gf(a, x, epsilon=3.e-7, iterations=200):
        ln = gammaln(a)
        g0 = 0.0
        a0 = 1.0
        b0 = 0.0
        a1 = x
        b1 = 1.0
        f  = 1.0
        for i in range(1, iterations):
            a0 = (a1 + a0 * (i - a)) * f
            b0 = (b1 + b0 * (i - a)) * f
            a1 = x * a0 + a1 * i * f
            b1 = x * b0 + b1 * i * f
            if a1 != 0.0:
                f = 1.0 / a1
                g = b1 * f
                if abs((g - g0) / g) < epsilon:
                    return (g * exp(-x + a * log(x) - ln), ln)
                g0 = g
        raise StopIteration, (abs((g-g0) / g))

    if a <= 0.0:
        return 1.0
    if x <= 0.0:
        return 1.0
    if x < a + 1:
        if tail == LOWER:
            return gs(a, x)[0]
        return 1 - gs(a, x)[0]
    else:
        if tail == UPPER:
            return gf(a, x)[0]
        return 1 - gf(a, x)[0]

#--- COMPLEMENTARY ERROR FUNCTION ------------------------------------------------------------------
# Based on: http://www.johnkerl.org/python/sp_funcs_m.py.txt, Tom Loredo

def erfc(x):
    """ Complementary error function.
    """
    z = abs(x)
    t = 1 / (1 + 0.5 * z)
    r = 0
    for y in [
      0.17087277, 
     -0.82215223, 
      1.48851587, 
     -1.13520398, 
      0.27886807, 
     -0.18628806, 
      0.09678418, 
      0.37409196, 
      1.00002368, 
     -1.26551223]:
        r = y + t * r
    r = t * exp(-z*z + r)
    if x >= 0:
        return r
    return 2 - r

def cdf(x, mu=0, sigma=1):
    """ Cumulative distribution function.
    """
    return min(1.0, 0.5 * erfc((-x + mu) / (sigma * 2**0.5)))

def pdf(x, mu=0, sigma=1):
    """ Probability density function.
    """
    u = (x - mu) / abs(sigma)
    return (1 / sqrt(2*pi) * abs(sigma)) * exp(-u*u / 2)
