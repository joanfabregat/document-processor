#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

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
