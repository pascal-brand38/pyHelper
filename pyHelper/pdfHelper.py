# MIT License
#
# Copyright (c) 2022 Pascal Brand

from PyPDF2 import PdfReader, PdfWriter, PageObject
from PyPDF2.generic import NameObject, TextStringObject
from PyPDF2.constants import     FieldDictionaryAttributes, FieldFlag
from PyPDF2.constants import PageAttributes as PG

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
from enum import IntFlag

class pdfReaderHelper(PdfReader):
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



OPTIONAL_READ_WRITE_FIELD = FieldFlag(0)

class pdfWriterHelper(PdfWriter):
    def __init__(self):
        PdfWriter.__init__(self)

    # copy/paste from PyPDF2/_writer.py
    # with some fixes commented with 'PASCAL'
    def update_page_form_field_values(
        self,
        page: PageObject,
        fields: Dict[str, Any],
        flags: FieldFlag = OPTIONAL_READ_WRITE_FIELD,
    ) -> None:
        """
        Update the form field values for a given page from a fields dictionary.

        Copy field texts and values from fields to page.
        If the field links to a parent object, add the information to the parent.

        :param PageObject page: Page reference from PDF writer where the
            annotations and field data will be updated.
        :param dict fields: a Python dictionary of field names (/T) and text
            values (/V)
        :param int flags: An integer (0 to 7). The first bit sets ReadOnly, the
            second bit sets Required, the third bit sets NoExport. See
            PDF Reference Table 8.70 for details.
        """
        self.set_need_appearances_writer()
        # Iterate through pages, update field values
        if PG.ANNOTS not in page:
            logger_warning("No fields to update on this page", __name__)
            return
        for j in range(len(page[PG.ANNOTS])):  # type: ignore
            writer_annot = page[PG.ANNOTS][j].get_object()  # type: ignore
            # retrieve parent field values, if present
            writer_parent_annot = {}  # fallback if it's not there
            if PG.PARENT in writer_annot:
                writer_parent_annot = writer_annot[PG.PARENT]
            for field in fields:
                if fields[field] is None:  # PASCAL
                    continue;
                if writer_annot.get(FieldDictionaryAttributes.T) == field:
                    # Pascal - changes for buttons
                    if writer_annot.get(FieldDictionaryAttributes.FT) == "/Btn":
                        writer_annot.update(
                            {
                                NameObject(FieldDictionaryAttributes.V): fields[field]
                            }
                        )
                    else:
                        writer_annot.update(
                            {
                                NameObject(FieldDictionaryAttributes.V): TextStringObject(
                                    fields[field]
                                )
                            }
                        )
                    if flags:
                        writer_annot.update(
                            {
                                NameObject(FieldDictionaryAttributes.Ff): NumberObject(
                                    flags
                                )
                            }
                        )
                elif writer_parent_annot.get(FieldDictionaryAttributes.T) == field:
                    writer_parent_annot.update(
                        {
                            NameObject(FieldDictionaryAttributes.V): TextStringObject(
                                fields[field]
                            )
                        }
                    )
