# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

from threading import Lock

from app import logger, config
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    AcceleratorOptions,
    TesseractCliOcrOptions,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption

_lock = Lock()

with _lock:
    logger.info("Loading Docling document converter...")

    # PDF pipeline options
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(
            num_threads=config.DL_CONVERTER_THREADS,
            device=config.DL_CONVERTER_ACCELERATOR
        ),
        do_ocr=config.DL_CONVERTER_OCR_ENABLED,
        ocr_options=TesseractCliOcrOptions(
            lang=["auto"],  # https://docling-project.github.io/docling/examples/tesseract_lang_detection/
            force_full_page_ocr=config.DL_CONVERTER_FORCE_FULL_PAGE_OCR,
            bitmap_area_threshold=config.DL_CONVERTER_OCR_BITMAP_AREA_THRESHOLD
        ),
        do_table_structure=config.DL_CONVERTER_DO_TABLE_STRUCTURE,
        images_scale=config.DL_CONVERTER_IMAGE_SCALE,
        table_structure_options=TableStructureOptions(
            do_cell_matching=config.DL_CONVERTER_DO_CELL_MATCHING,
            mode=config.DL_CONVERTER_TABLE_FORMER_MODE,
        )
    )

    # https://docling-project.github.io/docling/examples/run_with_accelerator/
    dl_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    logger.info("Docling document converter loaded successfully.")
