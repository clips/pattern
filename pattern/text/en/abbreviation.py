def acronym_of(string):
	# Empty string
	acronym = ''
	# For knowing where to split
	previous = ''
	for character in string:
		if previous in " -" or previous.islower() and character.isupper():
			acronym += character.upper() + "."
		previous = character
	return acronym
