#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

from io import BytesIO
from pathlib import Path
from typing import Generator

from docling.datamodel.base_models import DocumentStream
from docling_core.types.doc.document import DoclingDocument

from app import logger, models
from app.services.docling import get_dl_converter
from app.utils.pdf_helpers import count_pdf_pages
from .page_extractor import PageExtractor


class ContentExtractor:
    """
    Class to extract content from a PDF document.
    """

    def __init__(self, bytes_or_path: bytes | str | Path, filename: str = "file.pdf", images_scale: float = 3.0):
        """
        Initialize the PDF content extractor.

        Args:
            bytes_or_path: The PDF file as bytes.
            filename: The name of the PDF file.
        """
        self.bytes_or_path = bytes_or_path
        self.filename = filename
        self._logger = logger.getChild(__name__)
        self._fast_converter = get_dl_converter(full_ocr=False, images_scale=images_scale)
        self._full_ocr_converter = get_dl_converter(full_ocr=True, images_scale=images_scale)

    def extract_pages(
            self,
            first_page: int = 1,
            last_page: int = None
    ) -> Generator[tuple[int, PageExtractor | None], None, None]:
        """
        Process a PDF file and extract pages and slices. Unprocessable pages are skipped.

        Args:
            first_page: The first page to extract.
            last_page: The last page to extract. If None, all pages are extracted.

        Yields:
            A tuple containing the page number and the page with slices extracted from the document.
        """
        if not last_page:
            last_page = count_pdf_pages(self.bytes_or_path)

        self._logger.debug(f"Processing page range %s to %s", first_page, last_page)

        # noinspection PyTypeChecker
        for page_no in range(first_page, last_page + 1):
            page = self.extract_page(page_no=page_no)
            yield page_no, page

    def extract_page(self, page_no: int) -> PageExtractor | None:
        """
        Process a PDF file and extract a page and slices.

        Args:
            page_no: The page number to extract.

        Returns:
            The page with slices extracted from the document.
        """
        # Extract the page using the fast converter
        self._logger.debug("Processing page %s with the fast converter", page_no)
        document = self._convert_page_to_dl_doc(page_no=page_no)
        if document:
            page = PageExtractor(document, page_no=page_no)
            if page.has_text_slices():
                return page

        # If the page has no slices, use the fallback to the full OCR converter
        self._logger.debug("Page %s has no slice, using full OCR converter", page_no)
        document = self._convert_page_to_dl_doc(page_no=page_no, use_full_ocr_converter=True)
        if document:
            page = PageExtractor(document, page_no=page_no)
            return page

        return None

    def _convert_page_to_dl_doc(self, page_no: int, use_full_ocr_converter: bool = False) -> DoclingDocument | None:
        """
        Convert a PDF page to a Docling document.

        Args:
            page_no: The page number to convert.
            use_full_ocr_converter: Whether to use the full OCR converter or not.

        Returns:
            The converted Docling document or None if not available.
        """
        converter = self._full_ocr_converter if use_full_ocr_converter else self._fast_converter
        try:
            if isinstance(self.bytes_or_path, bytes):
                # noinspection PyTypeChecker
                source = DocumentStream(name=self.filename, stream=BytesIO(self.bytes_or_path))
            else:
                source = self.bytes_or_path

            result = converter.convert(
                source=source,
                page_range=(page_no, page_no),
                raises_on_error=False,
            )
        except Exception as e:
            self._logger.error("Failed to convert page %s: %s", page_no, e)
            return None
        if not result.document:
            self._logger.warning("Failed to convert page %s to Docling document", page_no)
            return None
        return result.document

    def extract_pages_model(
            self,
            *,
            first_page: int = 1,
            last_page: int = None,
            include_page_screenshot: bool,
            include_slice_screenshot: bool,
            image_format: str,
            image_quality: int
    ) -> list[models.Page]:
        """
        Return a list of pages extracted from the document.

        Args:
            first_page: The first page to extract.
            last_page: The last page to extract. If None, all pages are extracted.
            include_page_screenshot: Whether to include the page screenshot.
            include_slice_screenshot: Whether to include the slice screenshot.
            image_format: The format of the image (default: WEBP).
            image_quality: The quality of the image (1-100, default: 80).

        Returns:
            A list of pages extracted from the document.
        """
        pages = []
        slice_no = 1
        for _, page_extractor in self.extract_pages(first_page, last_page):
            if page_extractor:
                page = page_extractor.get_model(
                    slice_no=slice_no,
                    include_page_screenshot=include_page_screenshot,
                    include_slice_screenshot=include_slice_screenshot,
                    image_format=image_format,
                    image_quality=image_quality
                )
                pages.append(page)
                slice_no += len(page.slices)
        return pages
