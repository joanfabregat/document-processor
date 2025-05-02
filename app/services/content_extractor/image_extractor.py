#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

from io import BytesIO

import PIL.Image

from app import logger, models


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
