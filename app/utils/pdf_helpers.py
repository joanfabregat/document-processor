#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

import re

import pymupdf

glyph_pattern = re.compile(r'(?i)glyph<(?:c=\d+,font=/[A-Z0-9]+\+[A-Za-z0-9-]+|\d+)>')


def count_pdf_pages(pdf_bytes: bytes) -> int:
    """
    Count the number of pages in a PDF document.

    Args:
        pdf_bytes: The content of the PDF document as bytes.

    Returns:
        The number of pages in the PDF document.
    """
    with pymupdf.open(stream=pdf_bytes) as pdf:
        return len(pdf)


def clean_pdf_glyphs(text: str) -> str:
    """
    Remove PDF tags from the text.

    Args:
        text: The text to clean.

    Returns:
        The cleaned text without PDF tags.
    """
    cleaned_text = glyph_pattern.sub(' ', text)  # Replace all matches with empty string
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Remove extra spaces
    cleaned_text = cleaned_text.strip()
    return cleaned_text
