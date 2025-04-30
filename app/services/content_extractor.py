#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import re
from io import BytesIO
from pathlib import Path
from typing import Generator

import PIL.Image
import pymupdf
from docling.datamodel.base_models import DocumentStream
from docling_core.types.doc import DocItemLabel, CoordOrigin
from docling_core.types.doc.document import DocItem, ProvenanceItem
from docling_core.types.doc.document import TextItem, TableItem, DoclingDocument, PictureItem

from app import logger, models
from app.services.dl_converter import get_dl_converter, DocumentConverter


class PageExtractor:
    """
    PageExtractor is responsible for extracting information from a page in a Docling document.
    """

    def __init__(self, dl_document: DoclingDocument, *, page_no: int = 0, first_slice_no: int = 1):
        """
        Initializes the PageExtractor with a Docling document and page number.

        Args:
            dl_document: The Docling document to extract from.
            page_no: The page number to extract from (1-indexed).
            first_slice_no: The number of the first extracted slice.
        """
        if not page_no in dl_document.pages:
            raise ValueError(f"Page {page_no} not found in Docling document")
        self.dl_document = dl_document
        self.page_no = page_no
        self.page = dl_document.pages[page_no]
        self.first_slice_no = first_slice_no
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

    def get_screenshot(self) -> 'ImageExtractor' or None:
        """
        Returns the screenshot of the page.

        Returns:
            The screenshot as an ImageExtractor object or None if not applicable.
        """
        self._logger.debug("Getting screenshot for page %s", self.page_no)
        if not self.page.image or not self.page.image.pil_image:
            return None
        return ImageExtractor(self.page.image.pil_image)

    def has_text_slices(self) -> bool:
        """
        Verifies if the page contains any text slices.

        Returns:
            bool: True if the page contains text slices, False otherwise.
        """
        for dl_item, level in self.dl_document.iterate_items(page_no=self.page_no):
            if not isinstance(dl_item, (TextItem, TableItem, PictureItem)):
                continue
            if isinstance(dl_item, TextItem) and dl_item.text:
                return True
        return False

    def get_slices(self) -> Generator[tuple[int, 'SliceExtractor'], None, None]:
        """
        Extract slices from the page.

        Returns:
            A generator yielding SliceExtractor objects for each slice.
        """

        slice_no = self.first_slice_no
        self._logger.debug("Getting slices for page %s", self.page_no)
        for dl_item, level in self.dl_document.iterate_items(page_no=self.page_no):
            if not isinstance(dl_item, (TextItem, TableItem, PictureItem)):
                continue
            slice_extractor = SliceExtractor(dl_document=self.dl_document, dl_item=dl_item, level=level,
                                             slice_no=slice_no)
            yield slice_no, slice_extractor


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
            ocr_pipeline: The OCR pipeline to use.
            filename: The name of the PDF file.
            images_scale: The scale factor for images.
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
            last_page = self._count_pdf_pages(self.bytes_or_path)

        self._logger.debug(f"Processing page range %s to %s", first_page, last_page)

        # noinspection PyTypeChecker
        for page_no in range(first_page, last_page + 1):
            page = self.extract_page(page_no=page_no)
            yield page_no, page

    def extract_page(self, page_no: int, first_slice_no: int = 1) -> PageExtractor | None:
        """
        Process a PDF file and extract a page and slices.

        Args:
            page_no: The page number to extract.
            first_slice_no: Number of the first extracted slice.

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
            page = PageExtractor(result.document, page_no=page_no, first_slice_no=first_slice_no)

            # Returns the page is it has text slices or is the last converter
            if page.has_text_slices() or converter == self._dl_converters[-1]:
                return page

        return None

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

    @staticmethod
    def _count_pdf_pages(bytes_or_path: bytes | str | Path) -> int:
        """
        Count the number of pages in a PDF document.

        Args:
            bytes_or_path: The content of the PDF document as bytes or the path to the PDF file.

        Returns:
            The number of pages in the PDF document.
        """
        if isinstance(bytes_or_path, (str, Path)):
            handler = pymupdf.open(filename=bytes_or_path)
        else:
            handler = pymupdf.open(stream=bytes_or_path)

        with handler as pdf:
            return len(pdf)


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
            slice_no: int = 0,
            level: int
    ):
        """
        Initializes the SliceExtractor with a Docling document and item.

        Args:
            dl_document: The Docling document to extract from.
            dl_item: The item to extract from.
            slice_no: The number of the slice.
            level: The level of the item in the document.
        """
        self.dl_document = dl_document
        self.dl_item = dl_item
        self.slice_no = slice_no
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

    def get_positions(self) -> list['SlicePositionExtractor']:
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

    def get_screenshot(self) -> 'ImageExtractor' or None:
        """
        Returns the screenshot of the item.

        Returns:
            The screenshot as an ImageExtractor object or None if not applicable.
        """
        self._logger.debug("Extracting screenshot for %s", self.dl_item.self_ref)
        if not isinstance(self.dl_item, (PictureItem, TableItem)):
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

    def get_page_no(self) -> int:
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


class ImageExtractor:
    """
    A class to extract image data from a PIL Image object.
    """

    def __init__(self, pil_image: PIL.Image.Image):
        """
        Initializes the ImageExtractor with a PIL Image object.

        Args:
            pil_image: The PIL Image object to extract data from.
        """
        self.pil_image = pil_image
        self._logger = logger.getChild(__name__)

    def get_width(self) -> int:
        """
        Returns the width of the image.
        """
        return self.pil_image.width

    def get_height(self) -> int:
        """
        Returns the height of the image.
        """
        return self.pil_image.height

    def get_data(
            self,
            image_format: models.ImageFormat = models.ImageFormat.WEBP,
            image_quality: int = 80
    ) -> bytes:
        """
        Returns the image data in the specified format and quality.

        Args:
            image_format: The format of the image (default: WEBP).
            image_quality: The quality of the image (1-100, default: 80).

        Returns:
            The image data as bytes.
        """
        self._logger.debug("Getting image data")
        webp_bytes = BytesIO()
        self.pil_image.save(
            webp_bytes,
            format=image_format.value.upper(),
            quality=image_quality
        )
        return webp_bytes.getvalue()
