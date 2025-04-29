#  Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, subject to the conditions in the full MIT License.
#  The Software is provided "as is", without warranty of any kind.

import base64


def encode_to_base64(data: bytes) -> str:
    """
    Encode bytes to a base64 string.

    Args:
        data (bytes): The bytes to encode.

    Returns:
        str: The base64 encoded string.
    """
    # noinspection PyTypeChecker
    return base64.b64encode(data).decode('ascii')
