# MIT License
#
# Copyright (c) 2022 Pascal Brand

from tidylib import tidy_document

# look at libtidy options at http://api.html-tidy.org/tidy/tidylib_api_next/tidy_quickref.html
def w3c_validation(text, filters=[]):
  document, errors = tidy_document(text,
    options={
      'drop-empty-elements':0
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
