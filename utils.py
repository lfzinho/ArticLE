import pathlib
import textwrap


def to_markdown(text):
  text = text.replace('•', '  *')
  return textwrap.indent(text, '> ', predicate=lambda _: True)


def get_key():
  with open('AuthKey.txt') as f:
    return f.read().strip()
