#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import docling.utils.model_downloader
import easyocr

from app import config, logger

##
# Download EasyOCR models
##
logger.info("Downloading EasyOCR models...")
reader = easyocr.Reader(
    lang_list=config.OCR_LANGUAGES,
    download_enabled=True
)

##
# Download Docling models
##
logger.info("Downloading Docling models...")
docling.utils.model_downloader.download_models(
    with_layout=True,
    with_tableformer=True,
    with_easyocr=True,
    with_code_formula=False,
    with_picture_classifier=False,
    with_smolvlm=False,
    with_granite_vision=False,
)
