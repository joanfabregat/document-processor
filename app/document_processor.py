#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from threading import Lock

from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    AcceleratorOptions,
    AcceleratorDevice,
    EasyOcrOptions,
    TesseractCliOcrOptions,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling_core.types.doc.document import TextItem, TableItem

from app.logging import logger
from app import models

_lock = Lock()

with _lock:
    logger.info("Loading Docling document converter...")

    # PDF pipeline options
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(
            num_threads=4,
            device=AcceleratorDevice.AUTO
        ),
        do_ocr=True,
        # https://docling-project.github.io/docling/examples/tesseract_lang_detection/
        # ocr_options=TesseractCliOcrOptions(lang=["auto"], force_full_page_ocr=True),
        ocr_options=EasyOcrOptions(force_full_page_ocr=True, download_enabled=True),
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            do_cell_matching=True,
        )
    )

    # https://docling-project.github.io/docling/examples/run_with_accelerator/
    dl_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    logger.info("Docling document converter loaded successfully.")


def process_file(file_path: str, raises_on_error: bool = True) -> list[models.Slice]:
    """
    Process a file and extract slices.

    Args:
        file_path: The path to the file.
        raises_on_error: Whether to raise an error if the extraction fails.

    Returns:
        A list of document slices.
    """
    logger.info(f"Extracting text from file {file_path}")
    result = dl_converter.convert(file_path, raises_on_error=raises_on_error)
    slices = []
    sequence = 0
    for item, level in result.document.iterate_items():
        if isinstance(item, (TextItem, TableItem)):  # Other types of items are ignored
            slices.append(
                models.Slice(
                    level=level,
                    ref=item.self_ref,
                    sequence=sequence,
                    parent_ref=item.parent.cref,
                    label=str(item.label.value),
                    content=item.text if isinstance(item, TextItem) else item.export_to_markdown(),
                    content_mime_type="text/plain" if isinstance(item, TextItem) else "text/markdown",
                    positions=[
                        models.SlicePosition(
                            page_no=prov.page_no,
                            top=round(prov.bbox.t, 2),
                            right=round(prov.bbox.r, 2),
                            bottom=round(prov.bbox.b, 2),
                            left=round(prov.bbox.l, 2),
                            coord_origin=models.SlicePosition.CoordOrigin(prov.bbox.coord_origin.name)
                        ) for prov in item.prov
                    ]
                )
            )
            sequence += 1
    logger.info(f"Extracted {len(slices)} slices from file: {file_path}")
    return slices
