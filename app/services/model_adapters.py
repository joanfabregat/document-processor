#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import base64

from app import models
from .content_extractor import PageExtractor, ImageExtractor, SliceExtractor, SlicePositionExtractor


class PageModelAdapter:
    """
    Adapter for the page model.
    """

    def __init__(
            self,
            *,
            extract_screenshot: bool = True,
            slice_model_adapter: 'SliceModelAdapter' = None,
            image_model_adapter: 'ImageModelAdapter' = None,
    ):
        """
        Initialize the PageModelAdapter.

        Args:
            extract_screenshot: Whether to extract the screenshot of the page.
            slice_model_adapter: The adapter for the slice model.
            image_model_adapter: The adapter for the image model.
        """
        self.extract_screenshot = extract_screenshot
        self.slice_model_adapter = slice_model_adapter or SliceModelAdapter()
        self.image_model_adapter = image_model_adapter or ImageModelAdapter()

    def get_model(self, extractor: PageExtractor) -> models.Page:
        """
        Return the model of the page.

        Args:
            extractor: The page extractor object.

        Returns:
            The model of the page as a DoclingDocument object.
        """
        page = models.Page(
            page_num=extractor.page_num,
            width=extractor.get_width(),
            height=extractor.get_height(),
            screenshot=None,
        )

        # Extract the page screenshot if requested
        if self.extract_screenshot is not None and (screenshot := extractor.get_screenshot()):
            page.screenshot = self.image_model_adapter.get_model(screenshot)

        # Extract the slices from the page
        for _, slice_extractor in extractor.get_slices():
            slice_ = self.slice_model_adapter.get_model(slice_extractor)
            page.slices.append(slice_)

        return page


class SliceModelAdapter:
    """
    Adapter for the slice model.
    """

    def __init__(
            self,
            *,
            extract_screenshot: bool = False,
            position_model_adapter: 'SlicePositionModelAdapter' = None,
            image_model_adapter: 'ImageModelAdapter' = None,
    ):
        """
        Initialize the SliceModelAdapter.

        Args:
            extract_screenshot: Whether to extract the screenshot of the slice.
            position_model_adapter: The adapter for the slice position model.
            image_model_adapter: The adapter for the image model.
        """
        self.extract_screenshot = extract_screenshot
        self.position_model_adapter = position_model_adapter or SlicePositionModelAdapter()
        self.extract_model_adapter = image_model_adapter or ImageModelAdapter()

    def get_model(self, extractor: SliceExtractor) -> models.Slice:
        """
        Extract the slice model from the slice extractor.

        Returns:
            The slice model with data extracted from the document.
        """
        # Extract the slice data
        slice_ = models.Slice(
            slice_num=extractor.slice_num,
            level=extractor.level,
            ref=extractor.get_ref(),
            parent_ref=extractor.get_parent_ref(),
            label=extractor.get_label(),
            content_text=extractor.get_content_text(),
            caption_text=extractor.get_caption_text(),
            table_data=extractor.get_table_data(),
            positions=[],
            screenshot=None,
        )

        # Extract the slice screenshot if requested
        if self.extract_screenshot is not None and (screenshot := extractor.get_screenshot()):
            slice_.screenshot = self.extract_model_adapter.get_model(screenshot)

        # Extract the positions of the slice
        for position_extractor in extractor.get_positions():
            slice_.positions.append(
                self.position_model_adapter.get_model(position_extractor)
            )

        return slice_


class SlicePositionModelAdapter:
    """
    Adapter for the slice position model.
    """

    def __init__(self, bbox_precision: int = 2):
        """
        Initialize the SlicePositionModelAdapter.

        Args:
            bbox_precision: The precision of the bounding box coordinates.
        """
        self.bbox_precision = bbox_precision

    def get_model(self, extractor: SlicePositionExtractor) -> models.Position:
        """
        Returns the model of the slice position.

        Args:
            extractor: The slice position extractor object.

        Returns:
            The slice position model with data extracted from the document.
        """
        return models.Position(
            page_num=extractor.get_page_num(),
            top=extractor.get_top(self.bbox_precision),
            right=extractor.get_right(self.bbox_precision),
            bottom=extractor.get_bottom(self.bbox_precision),
            left=extractor.get_left(self.bbox_precision),
            coord_origin=extractor.get_coord_origin(),
        )


class ImageModelAdapter:
    """
    Adapter for the image model.
    """

    def __init__(
            self,
            *,
            image_format: models.ImageFormat = models.ImageFormat.WEBP,
            image_quality: int = 80
    ):
        """
        Initialize the ImageModelAdapter.

        Args:
            image_format: The format of the image.
            image_quality: The quality of the image.
        """
        self.image_format = image_format
        self.image_quality = image_quality

    def get_model(self, extractor: ImageExtractor) -> models.Image:
        """
        Returns the model of the image.

        Args:
            extractor: The image extractor object.

        Returns:
            The image model with data extracted from the document.
        """
        return models.Image(
            data=self._encode_to_base64(extractor.get_data()),
            width=extractor.get_width(),
            height=extractor.get_height(),
            content_type=f"image/{self.image_format.value}",
        )

    @staticmethod
    def _encode_to_base64(data: bytes) -> str:
        """
        Encode bytes to a base64 string.

        Args:
            data (bytes): The bytes to encode.

        Returns:
            str: The base64 encoded string.
        """
        # noinspection PyTypeChecker
        return base64.b64encode(data).decode('ascii')
