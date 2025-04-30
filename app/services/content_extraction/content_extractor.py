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

from app import logger, models
from app.services.dl_converter import get_dl_converter, DocumentConverter
from app.utils.pdf_helpers import count_pdf_pages
from .page_extractor import PageExtractor


class ContentExtractor:
    """
    Class to extract content from a PDF document.
    """

    def __init__(
            self,
            bytes_or_path: bytes | str | Path,
            *,
            ocr_pipeline: models.OcrPipeline = models.OcrPipeline.HYBRID,
            filename: str = "file.pdf",
            images_scale: float = 3.0
    ):
        """
        Initialize the PDF content extractor.

        Args:
            bytes_or_path: The PDF file as bytes.
            filename: The name of the PDF file.
        """
        self._logger = logger.getChild(__name__)
        self.bytes_or_path = bytes_or_path
        self.ocr_pipeline = ocr_pipeline
        self.filename = filename
        self.images_scale = images_scale
        self._dl_converters = self._load_dl_converters()

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
        for converter in self._dl_converters:
            # Convert the page to a Docling document
            try:
                result = converter.convert(
                    source=self._get_dl_source(),
                    page_range=(page_no, page_no),
                    raises_on_error=False,
                )
            except Exception as e:
                self._logger.error("Failed to convert page %s: %s", page_no, e)
                continue

            if not result.document:
                self._logger.warning("Failed to convert page %s to Docling document", page_no)
                continue

            # Extract the page using the converter
            page = PageExtractor(result.document, page_no=page_no)

            # Returns the page is it has text slices or is the last converter
            if page.has_text_slices() or converter == self._dl_converters[-1]:
                return page

        return None

    def extract_pages_model(
            self,
            *,
            first_page: int = 1,
            last_page: int = None,
            image_format: models.ImageFormat | None,
            image_quality: int
    ) -> list[models.Page]:
        """
        Return a list of pages extracted from the document.

        Args:
            first_page: The first page to extract.
            last_page: The last page to extract. If None, all pages are extracted.
            image_format: The format of the image.
            image_quality: The quality of the image.

        Returns:
            A list of pages extracted from the document.
        """
        pages = []
        slice_no = 1
        for _, page_extractor in self.extract_pages(first_page, last_page):
            if page_extractor:
                page = page_extractor.get_model(
                    slice_no=slice_no,
                    image_format=image_format,
                    image_quality=image_quality
                )
                pages.append(page)
                slice_no += len(page.slices)
        return pages

    def _get_dl_source(self):
        """
        Get the source for the document converter.
        """
        # If the source is bytes, create a BytesIO stream
        if isinstance(self.bytes_or_path, bytes):
            # noinspection PyTypeChecker
            return DocumentStream(name=self.filename, stream=BytesIO(self.bytes_or_path))

        # If the source is a path, use it directly
        return self.bytes_or_path

    def _load_dl_converters(self) -> list[DocumentConverter]:
        """
        Get the document converter with the specified options in a thread-safe manner.
        """
        converters = []
        if self.ocr_pipeline in (models.OcrPipeline.HYBRID, models.OcrPipeline.FAST):
            converters.append(
                get_dl_converter(full_ocr=False, images_scale=self.images_scale)
            )
        if self.ocr_pipeline in (models.OcrPipeline.HYBRID, models.OcrPipeline.FULL):
            converters.append(
                get_dl_converter(full_ocr=True, images_scale=self.images_scale)
            )
        return converters
