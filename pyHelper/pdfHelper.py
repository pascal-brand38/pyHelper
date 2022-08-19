# MIT License
#
# Copyright (c) 2022 Pascal Brand

from PyPDF2 import PdfReader

from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

class pdfHelper(PdfReader):
    def __init__(self, file):
        PdfReader.__init__(self, file)

    def get_form_fields_in_list(self, l_tags) -> Dict[str, Any]:
      """Retrieves form fields from the document with textual data (inputs, dropdowns)"""
      """
      Retrieves form fields from the document with textual data.
      The key is the name of the form field, the value is the content of the
      field.
      If the document contains multiple form fields with the same name, the
      second and following will get the suffix _2, _3, ...
      """
      # Retrieve document form fields
      formfields = self.get_fields()
      if formfields is None:
          return {}
      return {
          formfields[field]["/T"]: formfields[field].get("/V")
          for field in formfields
          if formfields[field].get("/FT") in l_tags
      }
