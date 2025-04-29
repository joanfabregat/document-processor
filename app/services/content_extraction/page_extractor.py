#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from typing import Generator

from docling_core.types.doc.document import TextItem, TableItem, DoclingDocument, PictureItem

from app import logger, models
from .image_extractor import ImageExtractor
from .slice_extractor import SliceExtractor


class PageExtractor:
    def __init__(self, dl_document: DoclingDocument, *, page_no: int = 0):
        if not page_no in dl_document.pages:
            raise ValueError(f"Page {page_no} not found in Docling document")
        self.dl_document = dl_document
        self.page_no = page_no
        self.page = dl_document.pages[page_no]
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

    def get_slices(self) -> Generator[tuple[int, SliceExtractor], None, None]:
        """
        Extract slices from the page.

        Returns:
            A generator yielding SliceExtractor objects for each slice.
        """

        slice_no = 1
        self._logger.debug("Getting slices for page %s", self.page_no)
        for dl_item, level in self.dl_document.iterate_items(page_no=self.page_no):
            if not isinstance(dl_item, (TextItem, TableItem, PictureItem)):
                continue
            slice_extractor = SliceExtractor(dl_document=self.dl_document, dl_item=dl_item, level=level)
            yield slice_no, slice_extractor

    def get_model(
            self,
            *,
            slice_no: int,
            include_page_screenshot: bool,
            include_slice_screenshot: bool,
            image_format: models.ImageFormat,
            image_quality: int
    ) -> models.Page:
        """
        Return the model of the page.

        Args:
            slice_no: The slice number to start from.
            include_page_screenshot: Whether to include the page screenshot.
            include_slice_screenshot: Whether to include the slice screenshot.
            image_format: The format of the image.
            image_quality: The quality of the image.

        Returns:
            The model of the page as a DoclingDocument object.
        """
        page = models.Page(
            page_no=self.page_no,
            width=self.get_width(),
            height=self.get_height(),
            screenshot=None,
        )

        # Extract the page screenshot if requested
        if include_page_screenshot and (screenshot := self.get_screenshot()):
            page.screenshot = screenshot.get_model(image_format=image_format, image_quality=image_quality)

        # Extract the slices from the page
        for _, slice_extractor in self.get_slices():
            slice_ = slice_extractor.get_model(
                slice_no=slice_no,
                include_slice_screenshot=include_slice_screenshot,
                image_format=image_format,
                image_quality=image_quality
            )
            page.slices.append(slice_)
            slice_no += 1

        return page
