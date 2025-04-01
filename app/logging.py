#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

import logging

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Add console handler if not already added
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level=logging.INFO)
    logger.addHandler(console_handler)
