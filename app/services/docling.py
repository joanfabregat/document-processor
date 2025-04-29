#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

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

_logger = logger.getChild(__name__)

EASY_OCR_LANGUAGES = ["fr", "de", "es", "en"]


def get_dl_converter(
        full_ocr: bool = False,
        ocr_confidence_threshold: float = 0.01,
        ocr_bitmap_area_threshold: float = 0.1,
        images_scale: float = 2.0,
        dl_generate_images: bool = True,
) -> DocumentConverter:
    """
    Get the document converter with the specified options in a thread-safe manner.

    https://docling-project.github.io/docling/examples/run_with_accelerator/

    Args:
        full_ocr (bool): Whether to use full OCR or not.
        ocr_confidence_threshold (float): The confidence threshold for OCR.
        ocr_bitmap_area_threshold (float): The bitmap area threshold for OCR.
        images_scale (float): The scale factor for images.
        dl_generate_images (bool): Whether to generate images or not.

    Returns:
        DocumentConverter: The document converter.
    """
    if full_ocr:
        _logger.info("Loading Docling document converter with full OCR...")
    else:
        _logger.info("Loading Docling document converter with fast OCR...")

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
                        lang=EASY_OCR_LANGUAGES,
                        confidence_threshold=ocr_confidence_threshold,
                        bitmap_area_threshold=ocr_bitmap_area_threshold
                    ),
                    images_scale=images_scale,
                    generate_page_images=full_ocr or dl_generate_images,
                    generate_picture_images=dl_generate_images,
                    generate_table_images=dl_generate_images,
                    do_table_structure=True,
                    table_structure_options=TableStructureOptions(
                        do_cell_matching=True,
                        mode=TableFormerMode.ACCURATE,
                    )
                )
            )
        }
    )
    _logger.debug("Docling document converter loaded successfully.")
    return dl_converter
