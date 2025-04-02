# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

from app import logger, models
from app.dl_converter import dl_converter
from docling_core.types.doc.document import TextItem, TableItem, DoclingDocument
import pandas as pd


class DocumentProcessor:
    """
    Class to process documents and extract slices.
    """

    def __init__(self, document: DoclingDocument, raises_on_error: bool = True, bbox_precision: int = None):
        """
        Initializes the DocumentProcessor with the given file path.

        Args:
            document (DoclingDocument): The document to process.
            raises_on_error (bool): Whether to raise an error on failure.
            bbox_precision (int): The precision for bounding box coordinates.
        """
        self.document = document
        self.raises_on_error = raises_on_error
        self.bbox_precision = bbox_precision if bbox_precision is not None else 1

    @classmethod
    def from_file(cls, file_path: str, raises_on_error: bool = True, bbox_precision: int = None):
        """
        Creates a DocumentProcessor instance from a file.

        Args:
            file_path (str): The path to the file to process.
            raises_on_error (bool): Whether to raise an error on failure.
            bbox_precision (int): The precision for bounding box coordinates.

        Returns:
            DocumentProcessor: An instance of DocumentProcessor.
        """
        logger.info(f"Converting file {file_path} to Docling document...")
        result = dl_converter.convert(file_path, raises_on_error=raises_on_error)
        if not result or not hasattr(result, 'document'):
            if raises_on_error:
                raise ValueError(f"Failed to extract text from {file_path}")
            logger.warning(f"No valid document content found in {file_path}")

        return cls(result.document, raises_on_error=raises_on_error, bbox_precision=bbox_precision)

    def process_pages(self) -> list[models.Page]:
        """
        Extracts the pages from the document.

        Returns:
            list[models.Page]: A list of Page objects representing the pages in the document.
        """
        logger.info(f"Extracting pages from Docling document")

        if not self.document:
            return []

        # List the document pages
        pages = []
        try:
            for page in self.document.pages.values():
                pages.append(
                    models.Page(
                        page_no=page.page_no,
                        width=page.size.width,
                        height=page.size.height
                    )
                )
            logger.info(f"Extracted {len(pages)} pages from Docling document")
        except Exception as e:
            if self.raises_on_error:
                raise ValueError(f"Failed to extract pages from Docling document: {e}")
            logger.warning(f"Failed to extract pages from Docling document: {e}")

        return pages

    def process_slices(self) -> list[models.Slice]:
        """
        Extracts slices from the document.

        Returns:
            list[models.Slice]: A list of Slice objects representing the slices in the document.
        """
        logger.info(f"Extracting slices from Docling document")

        if not self.document:
            return []

        slices = []
        try:
            for item, level in self.document.iterate_items():
                if isinstance(item, TableItem):
                    content = item.export_to_markdown(self.document)
                    df = item.export_to_dataframe()
                    raw_content = [df.columns.tolist()] + df.values.tolist()
                    content_mime_type = "text/markdown"
                elif isinstance(item, TextItem):
                    content = item.text
                    raw_content = item.orig
                    table_data = None
                    content_mime_type = "text/plain"
                else:
                    continue  # Other types of items are ignored

                slices.append(
                    models.Slice(
                        level=level,
                        ref=item.self_ref,
                        sequence=len(slices),
                        parent_ref=item.parent.cref if item.parent else None,
                        label=item.label,
                        content=content,
                        raw_content=raw_content,
                        content_mime_type=content_mime_type,
                        positions=[
                            models.Slice.Position(
                                page_no=prov.page_no,
                                top=round(prov.bbox.t, self.bbox_precision),
                                right=round(prov.bbox.r, self.bbox_precision),
                                bottom=round(prov.bbox.b, self.bbox_precision),
                                left=round(prov.bbox.l, self.bbox_precision),
                                coord_origin=prov.bbox.coord_origin
                            ) for prov in item.prov
                        ]
                    )
                )
            logger.info(f"Extracted {len(slices)} slices from Docling document")

        except Exception as e:
            if self.raises_on_error:
                raise ValueError(f"Failed to extract slices from Docling document: {e}")
            logger.warning(f"Failed to extract slices from Docling document: {e}")

        return slices
