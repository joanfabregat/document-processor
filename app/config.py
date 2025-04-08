#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env files
_config_dir = Path(__file__).resolve().parent.parent
if os.path.isfile(_config_dir / '.env'):
    load_dotenv(dotenv_path=_config_dir / '.env')
if os.path.isfile(_config_dir / '.env.local'):
    load_dotenv(dotenv_path=_config_dir / '.env.local', override=True)

# Define constants for the application
ENV: str = os.getenv("ENV", "development")
THREADS: int = int(os.getenv("THREADS", 4))
VERSION: str = os.getenv("VERSION")
BUILD_ID: str = os.getenv("BUILD_ID")
COMMIT_SHA: str = os.getenv("COMMIT_SHA")

# DL Converter config
OCR_CONFIDENCE_THRESHOLD = 0.1
OCR_BITMAP_AREA_THRESHOLD = 0.1
IMAGES_SCALE = 1.0
DL_GENERATE_IMAGES = True