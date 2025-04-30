#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from docling_core.types.doc import DocItemLabel, CoordOrigin
from docling_core.types.doc.document import TextItem, TableItem, NodeItem, DoclingDocument, PictureItem

from app import logger, models
from app.utils.pdf_helpers import clean_pdf_glyphs
from .image_extractor import ImageExtractor


class SliceExtractor:
    def __init__(
            self,
            dl_document: DoclingDocument,
            dl_item: NodeItem,
            *,
            level: int,
            bbox_precision: int = 2
    ):
        self.dl_document = dl_document
        self.dl_item = dl_item
        self.level = level
        self.bbox_precision = bbox_precision
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
        text = clean_pdf_glyphs(text)
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
        text = clean_pdf_glyphs(text)
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
                    clean_col = clean_pdf_glyphs(col)
                    if clean_col != col:
                        # noinspection PyTypeChecker
                        table_data[i][j] = clean_col

        return table_data

    def get_positions(self) -> list[dict[str, float | int | CoordOrigin]]:
        """
        Returns the positions of the item.

        Returns:
            The positions of the item as a list of Position objects.
        """
        self._logger.debug("Extracting positions for %s", self.dl_item.self_ref)
        return [
            {
                'page_no': prov.page_no,
                'top': round(prov.bbox.t, self.bbox_precision),
                'right': round(prov.bbox.r, self.bbox_precision),
                'bottom': round(prov.bbox.b, self.bbox_precision),
                'left': round(prov.bbox.l, self.bbox_precision),
                'coord_origin': prov.bbox.coord_origin
            } for prov in self.dl_item.prov
        ]

    def get_screenshot(self) -> ImageExtractor | None:
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

    def get_model(
            self,
            *,
            slice_no: int,
            image_format: models.ImageFormat | None,
            image_quality: int
    ) -> models.Slice:
        """
        Extract the slice model from the slice extractor.

        Args:
            slice_no: The slice number to start from.
            image_format: The format of the image (default: WEBP).
            image_quality: The quality of the image (1-100, default: 80).

        Returns:
            The slice model with data extracted from the document.
        """
        # Extract the slice data
        slice_ = models.Slice(
            slice_no=slice_no,
            level=self.level,
            ref=self.get_ref(),
            parent_ref=self.get_parent_ref(),
            label=self.get_label(),
            content_text=self.get_content_text(),
            caption_text=self.get_caption_text(),
            table_data=self.get_table_data(),
            positions=[],
            screenshot=None,
        )

        # Extract the slice screenshot if requested
        if image_format is not None and (screenshot := self.get_screenshot()):
            slice_.screenshot = screenshot.get_model(image_format=image_format, image_quality=image_quality)

        # Extract the positions of the slice
        for position in self.get_positions():
            slice_.positions.append(
                models.Position(
                    page_no=position['page_no'],
                    top=position['top'],
                    right=position['right'],
                    bottom=position['bottom'],
                    left=position['left'],
                    coord_origin=position['coord_origin'],
                )
            )

        return slice_
