from __future__ import print_function
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import Google, plaintext

# A search engine in pattern.web sometimes has custom methods that the others don't.
# For example, Google has Google.translate() and Google.identify().

# This example demonstrates the Google Translate API.
# It will only work with a license key, since it is a paid service.
# In the Google API console (https://code.google.com/apis/console/),
# activate Translate API.

g = Google(license=None)  # Enter your license key.
# en
q = "Your mother was a hamster and your father smelled of elderberries!"
# "Ihre Mutter war ein Hamster und euer Vater roch nach Holunderbeeren!"  # de
print(q)
# fr, de, nl, es, cs, ja, ...
print(plaintext(g.translate(q, input="en", output="de")))
print()

q = "C'est un lapin, lapin de bois, un cadeau."
print(q)
print(g.identify(q))  # (language, confidence)
