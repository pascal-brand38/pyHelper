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

from PIL import Image

import re
import os
import json


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


# create_sprites
# Sprite generation, as png and webp, from icons
#
# TODO: comments
def create_sprites(spriteJsonFilename):
  with open(spriteJsonFilename, encoding='utf-8') as file:
    try:
      json_db = json.load(file)
    except ValueError as err:
      print(err)
      print('Wrong json at ' + spriteJsonFilename + ' - Exit')
      exit(1)

  rootDirIcons = os.path.dirname(spriteJsonFilename)
  icons = json_db['icons'].keys()

  sprite_width = 0
  sprite_height = 0
  images = []

  for icon in icons:
    desc = json_db['icons'][icon]
    name = desc['filename']
    pos_w = int(desc['posHor'])
    pos_h = int(desc['posVer'])
    i = Image.open(rootDirIcons + '/' + name)
    if sprite_width < pos_w + i.width:
      sprite_width = pos_w + i.width
    if sprite_height < pos_h + i.height:
      sprite_height = pos_h + i.height
    images.append(i)

  sprite = Image.new(
    mode='RGBA',
    size=(sprite_width, sprite_height),
    color=(0,0,0,0))  # fully transparent

  index = 0
  for icon in icons:
    i = images[index]

    desc = json_db['icons'][icon]
    name = desc['filename']
    pos_w = int(desc['posHor'])
    pos_h = int(desc['posVer'])

    sprite.paste(i, (pos_w, pos_h))
    spanPosition = desc.get('spanPosition', 'before')
    print(icon + '::' + spanPosition + ' {'
      + ' background-position: -' + str(desc['posHor']) + 'px -' + str(desc['posVer']) + 'px;'
      + ' width: ' + str(i.width) + 'px;'
      + ' height: ' + str(i.height) + 'px;'
      + ' }')
    index = index + 1
  
  png_result = rootDirIcons + '/' + json_db['spriteOutputBaseName'] + '.png'
  print('Save ' +  png_result)
  sprite.save(png_result, optimize=True)
  error = os.system('optipng ' + png_result)
  if error != 0:
    exit(1)

  # save as webp
  # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp
  # method=6 provides a better size, but is slow
  webp_result = rootDirIcons + '/' + json_db['spriteOutputBaseName'] + '.webp'
  print('Save ' +  webp_result)
  sprite.save(webp_result, method=6, quality=100, lossless=True)

  return 0    # no error
