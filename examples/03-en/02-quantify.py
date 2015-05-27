import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.en import number, numerals, quantify, reflect

# The number() command returns an int or float from a written representation.
# This is useful, for example, in combination with a parser
# to transform "CD" parts-of-speech to actual numbers.
# The algorithm ignores words that aren't recognized as numerals.
print(number("two thousand five hundred and eight"))
print(number("two point eighty-five"))
print("")

# The numerals() command returns a written representation from an int or float.
print numerals(1.249, round=2)
print numerals(1.249, round=3)
print("")

# The quantify() commands uses pluralization + approximation to enumerate words.
# This is useful to generate a human-readable summary of a set of strings.
print(quantify(["goose", "goose", "duck", "chicken", "chicken", "chicken"]))
print(quantify(["penguin", "polar bear"]))
print(quantify(["carrot"] * 1000))
print(quantify("parrot", amount=1000))
print(quantify({"carrot": 100, "parrot": 20}))
print("")

# The quantify() command only works with words (strings).
# To quantify a set of Python objects, use reflect().
# This will first create a human-readable name for each object and then quantify these.
print(reflect([0, 1, {}, False, reflect]))
print(reflect(os.path))
print(reflect([False, True], quantify=False))
print(quantify(
    ["bunny rabbit"] +
    reflect([False, True], quantify=False)))