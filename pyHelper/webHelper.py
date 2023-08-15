# MIT License
#
# Copyright (c) 2022 Pascal Brand

# w3c verification
from tidylib import tidy_document

# do not use css_html_js_minify as it is buggy (crash or wrong html results)
import htmlmin
import csscompressor
import jsmin
import slimit     # another js minifier
import re


# look at libtidy options at http://api.html-tidy.org/tidy/tidylib_api_next/tidy_quickref.html
def w3c_validation(text, filters=[]):
  if filters is None:
    filters = []
  document, errors = tidy_document(text,
    options={
      'drop-empty-elements':0,    # empty span that displays icons becuase of :after and :before with content
      'doctype': 'html5'          # do not care about html4 format specification - only html5 is stressed
    })

  nb_errors = 0
  for error in errors.split("\n"):
    # check the error is empty, which can be the case because of split
    if error == '':
      continue

    # check if this error must be filtered
    to_be_filtered = False
    for f in filters:
      if f in error:
        to_be_filtered = True

    if not to_be_filtered:
      print(error)
      nb_errors = nb_errors + 1
  
  return nb_errors



def css_minify(text):
  try:
    text = csscompressor.compress(text)
  except:
    print('Error while minifying css - keep the original file')
  return text

def js_minify(text):
  # https://github.com/rspivak/slimit/issues/97
  # removes warnings from slimit, the js minifier
  if not(js_minify._init):
    js_minify._init = True
    slimit.lexer.ply.lex.PlyLogger =  \
      slimit.parser.ply.yacc.PlyLogger = \
        type('_NullLogger', (slimit.lexer.ply.lex.NullLogger,),
            dict(__init__=lambda s, *_, **__: (None, s.super().__init__())[0]))

  try:
    text = slimit.minify(text, mangle=True)
  except:
    try:
      text = jsmin.jsmin(text)
    except:
      print('Error while minifying js - keep the original file')
  return text

def html_minify(text):
  try:
    text = htmlmin.minify(text, remove_comments=True)
  except:
    print('Error while minifying html - keep the original file')
    return text

  split = re.split('(<style[^>]*>|</style>)', text, flags=re.IGNORECASE)
  for i in range(0, len(split)):
      #if we are on in a style
      if split[i].startswith('<style'):
          split[i+1] = csscompressor.compress(split[i+1])
  text = ''.join(split)

  split = re.split('(<script>|<script[^>]*text/javascript[^>]*>|</script>)', text, flags=re.IGNORECASE)
  for i in range(0, len(split)):
      #if we are on in a style
      if split[i].startswith('<script'):
          split[i+1] = jsmin.jsmin(split[i+1])

  return ''.join(split)


# global variable initialization
js_minify._init = False

