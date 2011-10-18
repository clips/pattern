import os, sys; sys.path.insert(0, os.path.join("..", ".."))

from pattern.web import Google, plaintext

q = "Your mother was a hamster and your father smelled of elderberries!"
print q
print plaintext(Google().translate(q, input="en", output="de")) # fr, de, nl, es, cs, ja, ...
print

q = "C'est un lapin, lapin de bois, un cadeau."
print q
print Google().identify(q)