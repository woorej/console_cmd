

def prettyjson(obj, indent=2, maxlinelength=80):
	"""Renders JSON content with indentation and line splits/concatenations to fit maxlinelength.
	Only dicts, lists and basic types are supported"""

	items, _ = getsubitems(obj, itemkey="", islast=True, maxlinelength=maxlinelength)
	res = indentitems(items, indent, indentcurrent=0)
	return res


def getsubitems(obj, itemkey, islast, maxlinelength):
	items = []
	can_concat = True  # assume we can concatenate inner content unless a child node returns an expanded list

	isdict = isinstance(obj, dict)
	islist = isinstance(obj, list)
	istuple = isinstance(obj, tuple)

	# building json content as a list of strings or child lists
	if isdict or islist or istuple:
		if isdict:
			opening, closing, keys = ("{", "}", iter(obj.keys()))
		elif islist:
			opening, closing, keys = ("[", "]", range(0, len(obj)))
		elif istuple:
			opening, closing, keys = ("[", "]", range(0, len(obj)))  # tuples are converted into json arrays

		if itemkey != "": opening = itemkey + ": " + opening
		if not islast: closing += ","

		# Get list of inner tokens as list
		count = 0
		subitems = []
		itemkey = ""
		for k in keys:
			count += 1
			islast_ = count == len(obj)
			itemkey_ = ""
			if isdict: itemkey_ = basictype2str(k)
			inner, can_concat_ = getsubitems(obj[k], itemkey_, islast_, maxlinelength)  # inner = (items, indent)
			subitems.extend(inner)  # inner can be a string or a list
			can_concat = can_concat and can_concat_  # if a child couldn't concat, then we are not able either

		# atttempt to concat subitems if all fit within maxlinelength
		if (can_concat):
			totallength = 0
			for item in subitems:
				totallength += len(item)
			totallength += len(subitems) - 1  # spaces between items
			if (totallength <= maxlinelength):
				str = ""
				for item in subitems:
					str += item + " "  # add space between items, comma is already there
				str = str.strip()
				subitems = [str]  # wrap concatenated content in a new list
			else:
				can_concat = False

		# attempt to concat outer brackets + inner items
		if (can_concat):
			if (len(opening) + totallength + len(closing) <= maxlinelength):
				items.append(opening + subitems[0] + closing)
			else:
				can_concat = False

		if (not can_concat):
			items.append(opening)  # opening brackets
			items.append(subitems)  # Append children to parent list as a nested list
			items.append(closing)  # closing brackets

	else:
		# basic types
		strobj = itemkey
		if strobj != "": strobj += ": "
		strobj += basictype2str(obj)
		if not islast: strobj += ","
		items.append(strobj)

	return items, can_concat


def basictype2str(obj):
	if isinstance(obj, str):
		strobj = "\"" + str(obj) + "\""
	elif isinstance(obj, bool):
		strobj = {True: "true", False: "false"}[obj]
	else:
		strobj = str(obj)
	return strobj


def indentitems(items, indent, indentcurrent):
	"""Recursively traverses the list of json lines, adds indentation based on the current depth"""
	res = ""
	indentstr = " " * indentcurrent
	for item in items:
		if (isinstance(item, list)):
			res += indentitems(item, indent, indentcurrent + indent)
		else:
			res += indentstr + item + "\n"
	return res


if __name__ == '__main__':
	o = dict(a1=dict(a2_1 = 10))
	s = prettyjson(o)
	print(f"pretty json\n{s}")
	pass
