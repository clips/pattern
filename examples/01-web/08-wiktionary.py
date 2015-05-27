import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Wiktionary, DOM
from pattern.db import csv, pd

# This example retrieves male and female given names from Wiktionary (http://en.wiktionary.org).
# It then trains a classifier that can predict the gender of unknown names (about 78% correct).
# The classifier is small (80KB) and fast.

w = Wiktionary(language="en")
f = csv()  # csv() is a short alias for Datasheet().

# Collect male and female given names from Wiktionary.
# Store the data as (name, gender)-rows in a CSV-file.
# The pd() function returns the parent directory of the current script,
# so pd("given-names.csv") = pattern/examples/01-web/given-names.csv.

for gender in ("male", "female"):
    for ch in ("abcdefghijklmnopqrstuvwxyz"):
        p = w.search("Appendix:%s_given_names/%s" % (gender.capitalize(), ch.capitalize()), cached=True)
        for name in p.links:
            if not name.startswith("Appendix:"):
                f.append((name, gender[0]))
        f.save(pd("given-names.csv"))
        print(ch, gender)

# Create a classifier that predicts gender based on name.

from pattern.vector import SVM, chngrams, count, kfoldcv

class GenderByName(SVM):

    def train(self, name, gender=None):
        SVM.train(self, self.vector(name), gender)

    def classify(self, name):
        return SVM.classify(self, self.vector(name))

    def vector(self, name): 
        """ Returns a dictionary with character bigrams and suffix.
            For example, "Felix" => {"Fe":1, "el":1, "li":1, "ix":1, "ix$":1, 5:1}
        """
        v = chngrams(name, n=2)
        v = count(v)
        v[name[-2:] + "$"] = 1
        v[len(name)] = 1
        return v

data = csv(pd("given-names.csv"))

# Test average (accuracy, precision, recall, F-score, standard deviation).

print(kfoldcv(GenderByName, data, folds=3))  # (0.81, 0.79, 0.77, 0.78, 0.00)

# Train and save the classifier in the current folder.
# With final=True, discards the original training data (= smaller file).

g = GenderByName(train=data)
g.save(pd("gender-by-name.svm"), final=True)

# Next time, we can simply load the trained classifier.
# Keep in mind that the script that loads the classifier
# must include the code for the GenderByName class description,
# otherwise Python won't know how to load the data.

g = GenderByName.load(pd("gender-by-name.svm"))

for name in (
  "Felix",
  "Felicia",
  "Rover",
  "Kitty",
  "Legolas",
  "Arwen",
  "Jabba",
  "Leia",
  "Flash",
  "Barbarella"):
    print(name, g.classify(name))

# In the example above, Arwen and Jabba are misclassified.
# We can of course improve the classifier by hand:

#g.train("Arwen", gender="f")
#g.train("Jabba", gender="m")
#g.save(pd("gender-by-name.svm"), final=True)
#print(g.classify("Arwen"))
#print(g.classify("Jabba"))
