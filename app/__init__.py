# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import logging
from . import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config.ENV == "development" else logging.INFO)
logger.propagate = False

if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(level=logger.level)
    logger.addHandler(_console_handler)
