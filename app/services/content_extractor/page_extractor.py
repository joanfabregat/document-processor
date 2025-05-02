#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

from typing import Generator

from docling_core.types.doc.document import TextItem, TableItem, DoclingDocument, PictureItem

from app import logger
from .image_extractor import ImageExtractor
from .slice_extractor import SliceExtractor


class PageExtractor:
    """
    PageExtractor is responsible for extracting information from a page in a Docling document.
    """

    def __init__(self, dl_document: DoclingDocument, *, page_num: int = 0, first_slice_num: int = 1):
        """
        Initializes the PageExtractor with a Docling document and page number.

        Args:
            dl_document: The Docling document to extract from.
            page_num: The page number to extract from (1-indexed).
            first_slice_num: The number of the first extracted slice.
        """
        if not page_num in dl_document.pages:
            raise ValueError(f"Page {page_num} not found in Docling document")
        self.dl_document = dl_document
        self.page_num = page_num
        self.page = dl_document.pages[page_num]
        self.first_slice_num = first_slice_num
        self._logger = logger.getChild(__name__)

    def get_width(self) -> float:
        """
        Returns the width of the page.
        """
        return self.page.size.width

    def get_height(self) -> float:
        """
        Returns the height of the page.
        """
        return self.page.size.height

    def get_screenshot(self) -> ImageExtractor | None:
        """
        Returns the screenshot of the page.

        Returns:
            The screenshot as an ImageExtractor object or None if not applicable.
        """
        self._logger.debug("Getting screenshot for page %s", self.page_num)
        if not self.page.image or not self.page.image.pil_image:
            return None
        return ImageExtractor(self.page.image.pil_image)

    def has_text_slices(self) -> bool:
        """
        Verifies if the page contains any text slices.

        Returns:
            bool: True if the page contains text slices, False otherwise.
        """
        for dl_item, level in self.dl_document.iterate_items(page_no=self.page_num):
            if not isinstance(dl_item, (TextItem, TableItem, PictureItem)):
                continue
            if isinstance(dl_item, TextItem) and dl_item.text:
                return True
        return False

    def get_slices(self) -> Generator[tuple[int, SliceExtractor], None, None]:
        """
        Extract slices from the page.

        Returns:
            A generator yielding SliceExtractor objects for each slice.
        """

        slice_num = self.first_slice_num
        self._logger.debug("Getting slices for page %s", self.page_num)
        for dl_item, level in self.dl_document.iterate_items(page_no=self.page_num):
            if not isinstance(dl_item, (TextItem, TableItem, PictureItem)):
                continue
            slice_extractor = SliceExtractor(
                dl_document=self.dl_document,
                dl_item=dl_item,
                level=level,
                slice_num=slice_num
            )
            yield slice_num, slice_extractor
