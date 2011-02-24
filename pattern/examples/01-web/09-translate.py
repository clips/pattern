import os, sys; sys.path.append(os.path.join("..", "..", ".."))

from pattern.web import Google, plaintext

q = "Your mother was a hamster and your father smelled of elderberries!"
print plaintext(Google().translate(q, input="en", output="de")) # fr, de, nl, es, cs, ja, ...