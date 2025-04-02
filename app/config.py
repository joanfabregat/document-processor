# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import os

from docling.datamodel.pipeline_options import AcceleratorDevice, TableFormerMode

VERSION = os.getenv("VERSION") or "v0.1.0"
BUILD_ID = os.getenv("BUILD_ID") or "unknown"
COMMIT_SHA = os.getenv("COMMIT_SHA") or "unknown"

# Document processor
BBOX_PRECISION = 1

# Docling converter
DL_CONVERTER_ACCELERATOR = AcceleratorDevice.CPU
DL_CONVERTER_THREADS = 4
DL_CONVERTER_IMAGE_SCALE = 2.0
DL_CONVERTER_FORCE_FULL_PAGE_OCR = False
DL_CONVERTER_OCR_BITMAP_AREA_THRESHOLD = .25
DL_CONVERTER_OCR_ENABLED = True
DL_CONVERTER_DO_TABLE_STRUCTURE = True
DL_CONVERTER_DO_CELL_MATCHING = True
DL_CONVERTER_TABLE_FORMER_MODE = TableFormerMode.ACCURATE
