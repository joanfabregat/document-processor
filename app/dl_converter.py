# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    AcceleratorOptions,
    EasyOcrOptions,
    TableStructureOptions,
    TableFormerMode,
    AcceleratorDevice
)
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption

from app import logger, config


def get_document_converter(full_ocr: bool = False) -> DocumentConverter:
    """
    Get the document converter with the specified options in a thread-safe manner.

    https://docling-project.github.io/docling/examples/run_with_accelerator/

    Args:
        full_ocr (bool): Whether to use full OCR or not.

    Returns:
        DocumentConverter: The document converter.
    """
    logger.info(f"Loading Docling document converter with {'full OCR' if full_ocr else 'fast OCR'}...")
    dl_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=PdfPipelineOptions(
                    accelerator_options=AcceleratorOptions(
                        num_threads=config.THREADS,
                        device=AcceleratorDevice.AUTO
                    ),
                    do_ocr=True,
                    # ocr_options=TesseractOcrOptions(
                    #     # https://docling-project.github.io/docling/examples/tesseract_lang_detection/
                    #     # lang=["auto"],
                    #     lang=["fra", "eng", "deu", "spa"],
                    #     force_full_page_ocr=full_ocr,
                    #     bitmap_area_threshold=.25
                    # ),
                    ocr_options=EasyOcrOptions(
                        force_full_page_ocr=full_ocr,
                        confidence_threshold=config.OCR_CONFIDENCE_THRESHOLD,
                        bitmap_area_threshold=config.OCR_BITMAP_AREA_THRESHOLD
                    ),
                    images_scale=config.IMAGES_SCALE,
                    generate_page_images=full_ocr or config.DL_GENERATE_IMAGES,
                    generate_picture_images=config.DL_GENERATE_IMAGES,
                    generate_table_images=config.DL_GENERATE_IMAGES,
                    do_table_structure=True,
                    table_structure_options=TableStructureOptions(
                        do_cell_matching=True,
                        mode=TableFormerMode.ACCURATE,
                    )
                )
            )
        }
    )
    logger.debug("Docling document converter loaded successfully.")
    return dl_converter
