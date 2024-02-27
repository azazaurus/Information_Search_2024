import os
import re as regex
import traceback


def delete_extra_whitespaces(text: str) -> str:
	text = text.strip()

	# Replace each sequence of whitespaces with a single space except line breaks
	text = regex.sub("((?!\\n)\\s)+", " ", text)
	# Remove whitespaces around line breaks
	# and replace each sequence of line breaks with a single line break
	text = regex.sub("\\s*\\n\\s*", "\n", text)

	return text


def format_exception(exception: Exception) -> str:
	return os.linesep.join(traceback.format_exception_only(type(exception), exception))
