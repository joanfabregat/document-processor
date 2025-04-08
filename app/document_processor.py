# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import base64
import sys
from io import BytesIO
from threading import Lock

from docling_core.types.doc.document import TextItem, TableItem, NodeItem, DoclingDocument, PictureItem

from app import logger, models
from app.dl_converter import get_document_converter

_converter_lock = Lock()

with _converter_lock:
    fast_converter = get_document_converter(full_ocr=False)
    full_ocr_converter = get_document_converter(full_ocr=True)


def process_file(
        file_path: str,
        *,
        raises_on_error: bool = True,
        extract_images: bool = False,
        page_range: tuple[int, int] = (1, sys.maxsize),
) -> list[models.Page]:
    """
    Process a PDF file and extract pages and slices.

    Args:
        file_path (str): Path to the PDF file.
        raises_on_error (bool): Whether to raise an exception if an error occurs.
        extract_images (bool): Whether to extract images or not.
        page_range (tuple[int, int]): Page range to process.

    Returns:
        The list of pages with slices extracted from the document.
    """
    logger.debug(f"Processing file {file_path} with page range {page_range}")

    pages = []
    sequence = 0

    for page_no in range(page_range[0], page_range[1] + 1):
        logger.debug(f"Processing page {page_no}")

        # Convert the page to a Docling document
        result = fast_converter.convert(
            source=file_path,
            page_range=(page_no, page_no),
            raises_on_error=raises_on_error,
        )

        # Extract the slices from the document
        page = _extract_document_page(
            document=result.document,
            page_no=page_no,
            sequence=sequence,
            extract_images=extract_images,
            raises_on_error=raises_on_error,
        )

        # If the page has no slices, use the fallback DL converter
        if not page.slices:
            logger.debug(f"Page {page_no} has no slice, using full OCR converter")

            # Use the fallback DL converter to convert the page to a Docling document
            result = full_ocr_converter.convert(
                source=file_path,
                page_range=(page_no, page_no),
                raises_on_error=raises_on_error,
            )

            # Extract the slices from the document
            page = _extract_document_page(
                document=result.document,
                page_no=page_no,
                sequence=sequence,
                extract_images=extract_images,
                raises_on_error=raises_on_error,
            )

        sequence += len(page.slices)

        # Add the extracted slices
        pages.append(page)

    return pages


def _extract_document_page(
        document: DoclingDocument,
        page_no: int,
        *,
        sequence: int,
        extract_images: bool,
        raises_on_error: bool = True,
        bbox_precision: int = 2,
) -> models.Page | None:
    """
    Extracts slices from the document.

    Args:
        document (DoclingDocument): The document to extract slices from.
        page_no (int): The page number to extract slices from.
        sequence (int): The sequence number of the slice.
        extract_images (bool): Whether to extract images or not.
        raises_on_error (bool): Whether to raise an exception if an error occurs.
        bbox_precision (int): The precision of the bounding box coordinates.

    Returns:
        A list of Slice objects representing the slices in the document.
    """
    logger.info(f"Extracting slices from Docling document")

    page = document.pages[page_no]
    if not page:
        logger.warning(f"Page {page_no} not found in Docling document")
        if raises_on_error:
            raise ValueError(f"Page {page_no} not found in Docling document")
        return None

    return models.Page(
        page_no=page.page_no,
        width=page.size.width,
        height=page.size.height,
        slices=_extract_document_slices(
            document=document,
            extract_images=extract_images,
            raises_on_error=raises_on_error,
            sequence=sequence,
            bbox_precision=bbox_precision,
        )
    )


def _extract_document_slices(
        document: DoclingDocument,
        *,
        extract_images: bool,
        raises_on_error: bool = True,
        sequence: int = 0,
        bbox_precision: int = 2,
) -> list[models.Page.Slice] | None:
    """
    Extracts slices from the document.

    Args:
        document (DoclingDocument): The document to extract slices from.
        extract_images (bool): Whether to extract images or not.
        raises_on_error (bool): Whether to raise an exception if an error occurs.
        sequence (int): The sequence number of the slice.
        bbox_precision (int): The precision of the bounding box coordinates.

    Returns:
        A list of Slice objects representing the slices in the document.
    """
    slices = []
    try:
        for item, level in document.iterate_items():
            slice_ = _convert_node_item_to_slice(
                document=document,
                item=item,
                extract_images=extract_images,
                level=level,
                sequence=sequence + len(slices),
                bbox_precision=bbox_precision,
            )
            if slice_:
                slices.append(slice_)

        logger.info(f"Extracted {len(slices)} slices from Docling document")

    except Exception as e:
        if raises_on_error:
            raise ValueError(f"Failed to extract slices from Docling document: {e}")
        logger.warning(f"Failed to extract slices from Docling document: {e}")

    return slices


def _convert_node_item_to_slice(
        document: DoclingDocument,
        item: NodeItem,
        *,
        extract_images: bool,
        level: int,
        sequence: int,
        bbox_precision: int = 2,
) -> models.Page.Slice | None:
    """
    Convert a node item extracted from the source document into a Slice object.

    Args:
        document (DoclingDocument): The document to extract the item from.
        item (NodeItem): The item to convert.
        extract_images (bool): Whether to extract images or not.
        level (int): The level of the item.
        sequence (int): The sequence number of the item.
        bbox_precision (int): The precision of the bounding box coordinates.

    Returns:
        models.Slice | None: The converted Slice object or None if not applicable.
    """
    # Ignore items that are not text or floating items
    if not isinstance(item, (TextItem, TableItem, PictureItem)):
        return None

    # Extract the content and mime type of the item
    content_mime_type, content = _extract_node_item_content(
        document=document,
        item=item,
    )

    # Extract image of the item if applicable
    png_image = None
    if extract_images and isinstance(item, (TableItem, PictureItem)):
        png_image = _extract_node_item_png_image(document, item)

    # Check if the content is valid
    if not content and not png_image:
        return None

    # Create slices
    return models.Page.Slice(
        level=level,
        ref=item.self_ref,
        sequence=sequence,
        parent_ref=item.parent.cref if item.parent else None,
        label=item.label,
        content=content,
        content_mime_type=content_mime_type,
        png_image=png_image,
        positions=[
            models.Page.Slice.Position(
                page_no=prov.page_no,
                top=round(prov.bbox.t, bbox_precision),
                right=round(prov.bbox.r, bbox_precision),
                bottom=round(prov.bbox.b, bbox_precision),
                left=round(prov.bbox.l, bbox_precision),
                coord_origin=prov.bbox.coord_origin
            ) for prov in item.prov
        ]
    )


def _extract_node_item_png_image(document: DoclingDocument, item: PictureItem | TableItem) -> str | None:
    """
    Get the PNG image of the item.

    Args:
        document (DoclingDocument): The document to extract the PNG image from.
        item (PictureItem|TableItem): The item to get the image from.

    Returns:
        str | None: The base64 encoded PNG image of the item or None if not available.
    """
    item_image = item.get_image(document)
    if item_image:
        byte_arr = BytesIO()
        item.get_image(document).save(byte_arr, format='PNG')
        # noinspection PyTypeChecker
        return base64.b64encode(byte_arr.getvalue()).decode('ascii')


def _extract_node_item_content(
        document: DoclingDocument,
        item: NodeItem,
) -> tuple[models.Page.Slice.ContentMimeType | None, str | list | None]:
    """
    Get the content and MIME type of the item.

    Args:
        document (DoclingDocument): The document to extract the content from.
        item (NodeItem): The item to get the content from.

    Returns:
        A tuple containing the MIME type and content of the item.
    """
    # Extract the table data of the table item
    if isinstance(item, TableItem):
        df = item.export_to_dataframe()
        table_data = [df.columns.tolist()] + df.values.tolist()
        if len(table_data) > 0 and len(table_data[0]) > 0:
            return models.Page.Slice.ContentMimeType.JSON, table_data

    # Extract the caption text of the floating item
    elif isinstance(item, PictureItem):
        slice_caption = item.caption_text(document)
        if slice_caption:
            return models.Page.Slice.ContentMimeType.TEXT, slice_caption

    # Extract the content and mime type for  text items
    elif isinstance(item, TextItem):
        return models.Page.Slice.ContentMimeType.TEXT, item.text

    return None, None
