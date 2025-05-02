#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import re

from docling_core.types.doc import DocItemLabel, CoordOrigin
from docling_core.types.doc.document import DocItem, ProvenanceItem
from docling_core.types.doc.document import TextItem, TableItem, DoclingDocument, PictureItem, FormulaItem, CodeItem

from app import logger
from .image_extractor import ImageExtractor


class SlicePositionExtractor:
    """
    SlicePositionExtractor is responsible for extracting position information from a slice in a Docling document.
    """

    def __init__(self, prov: ProvenanceItem):
        """
        Initializes the SlicePositionExtractor with a Docling document and item.

        Args:
            prov: The provenance item to extract from.
        """
        self.prov = prov

    def get_page_num(self) -> int:
        """Returns the page number of the item."""
        return self.prov.page_no

    def get_top(self, bbox_precision: int = 2) -> float:
        """Returns the top coordinate of the bounding box."""
        return round(self.prov.bbox.t, bbox_precision)

    def get_right(self, bbox_precision: int = 2) -> float:
        """Returns the right coordinate of the bounding box."""
        return round(self.prov.bbox.r, bbox_precision)

    def get_bottom(self, bbox_precision: int = 2) -> float:
        """Returns the bottom coordinate of the bounding box."""
        return round(self.prov.bbox.b, bbox_precision)

    def get_left(self, bbox_precision: int = 2) -> float:
        """Returns the left coordinate of the bounding box."""
        return round(self.prov.bbox.l, bbox_precision)

    def get_coord_origin(self) -> CoordOrigin:
        """Returns the coordinate origin of the bounding box."""
        return self.prov.bbox.coord_origin


class SliceExtractor:
    """
    SliceExtractor is responsible for extracting information from a slice in a Docling document.
    """

    glyph_pattern = re.compile(r'(?i)glyph<(?:c=\d+,font=/[A-Z0-9]+\+[A-Za-z0-9-]+|\d+)>')

    def __init__(
            self,
            dl_document: DoclingDocument,
            dl_item: DocItem,
            *,
            slice_num: int = 0,
            level: int
    ):
        """
        Initializes the SliceExtractor with a Docling document and item.

        Args:
            dl_document: The Docling document to extract from.
            dl_item: The item to extract from.
            slice_num: The number of the slice.
            level: The level of the item in the document.
        """
        self.dl_document = dl_document
        self.dl_item = dl_item
        self.slice_num = slice_num
        self.level = level
        self._logger = logger.getChild(__name__)

    def get_ref(self) -> str:
        """
        Returns the reference of the item.

        Returns:
            The reference of the item as a string.
        """
        return self.dl_item.self_ref

    def get_parent_ref(self) -> str | None:
        """
        Returns the reference of the parent item.

        Returns:
            The reference of the parent item as a string or None if not applicable.
        """
        return self.dl_item.parent.cref if self.dl_item.parent else None

    def get_label(self) -> DocItemLabel:
        """
        Returns the label of the item.

        Returns:
            The label of the item as a DocItemLabel object.
        """
        return self.dl_item.label

    def get_content_text(self) -> str | None:
        """
        Returns the text content of the item.

        Returns:
            The text content as a string or None if not applicable.
        """
        self._logger.debug("Extracting content text for %s", self.dl_item.self_ref)
        if not isinstance(self.dl_item, TextItem):
            return None

        text = self.dl_item.text
        if not text:
            return None
        text = self._clean_pdf_glyphs(text)
        return text

    def get_caption_text(self) -> str | None:
        """
        Returns the caption text of the item.

        Returns:
            The caption text as a string or None if not applicable.
        """
        if not isinstance(self.dl_item, (TableItem, PictureItem)):
            return None

        text = self.dl_item.caption_text(self.dl_document)
        if not text:
            return None
        text = self._clean_pdf_glyphs(text)
        return text

    def get_table_data(self) -> list[list[str | int | None]] | None:
        """
        Returns the table data of the item.

        Returns:
            The table data as a list of lists or None if not applicable.
        """
        self._logger.debug("Extracting table data for %s", self.dl_item.self_ref)
        if not isinstance(self.dl_item, TableItem):
            return None

        df = self.dl_item.export_to_dataframe()
        table_data = []

        # Extract headers and values
        if headers := df.columns.tolist():
            table_data.append(headers)
        if values := df.values.tolist():
            table_data.extend(values)

        if not table_data:
            return None

        # Cleanup table data
        for i, row in enumerate(table_data):
            for j, col in enumerate(row):
                if isinstance(col, str):
                    clean_col = self._clean_pdf_glyphs(col)
                    if clean_col != col:
                        # noinspection PyTypeChecker
                        table_data[i][j] = clean_col

        return table_data

    def get_positions(self) -> list[SlicePositionExtractor]:
        """
        Returns the positions of the item.

        Returns:
            The positions of the item as a list of Position objects.
        """
        self._logger.debug("Extracting positions for %s", self.dl_item.self_ref)
        return [
            SlicePositionExtractor(prov)
            for prov in self.dl_item.prov
        ]

    def get_screenshot(self) -> ImageExtractor | None:
        """
        Returns the screenshot of the item.

        Returns:
            The screenshot as an ImageExtractor object or None if not applicable.
        """
        self._logger.debug("Extracting screenshot for %s", self.dl_item.self_ref)
        if not isinstance(self.dl_item, (PictureItem, TableItem, FormulaItem, CodeItem)):
            return None

        item_image = self.dl_item.get_image(self.dl_document)

        if not item_image:
            return None

        return ImageExtractor(item_image)

    def _clean_pdf_glyphs(self, text: str) -> str:
        """
        Remove PDF tags from the text.

        Args:
            text: The text to clean.

        Returns:
            The cleaned text without PDF tags.
        """
        cleaned_text = self.glyph_pattern.sub(' ', text)  # Replace all matches with empty string
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Remove extra spaces
        cleaned_text = cleaned_text.strip()
        return cleaned_text
