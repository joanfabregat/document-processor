#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from io import BytesIO

import PIL.Image

from app import logger, models
from app.utils.base64 import encode_to_base64


class ImageExtractor:
    """
    A class to extract image data from a PIL Image object.
    """

    def __init__(
            self,
            pil_image: PIL.Image.Image,

    ):
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

    def get_data(self, image_format: str = "WEBP", image_quality: int = 80) -> bytes:
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
            format=image_format,
            quality=image_quality
        )
        return webp_bytes.getvalue()

    def get_model(self, *, image_format: str = "WEBP", image_quality: int = 80) -> models.Image:
        """
        Returns the model of the image.

        Args:
            image_format: The format of the image (default: WEBP).
            image_quality: The quality of the image (1-100, default: 80).

        Returns:
            The image model with data extracted from the document.
        """
        return models.Image(
            data=encode_to_base64(self.get_data(image_format, image_quality)),
            width=self.get_width(),
            height=self.get_height(),
            content_type=f"image/{image_format.lower()}",
        )
