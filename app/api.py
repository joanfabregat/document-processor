# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import datetime
import os
import shutil
import sys
import tempfile

import pymupdf
from fastapi import FastAPI, UploadFile, File, HTTPException

from app import models, logger, config
from app.document_processor import process_file

start_dt = datetime.datetime.now()

##
# Start FastAPI app
##
logger.info("Starting FastAPI app...")
api = FastAPI(
    title="Document Processor API",
    description="An API to extract slices from PDF documents.",
    version=config.VERSION,
    debug=config.ENV == "development",
)


##
# Routes
##
@api.get("/health", response_model=models.HealthResponse)
async def health():
    """
    Root endpoint.
    """
    return models.HealthResponse(
        version=config.VERSION,
        build_id=config.BUILD_ID,
        commit_sha=config.COMMIT_SHA,
        up_since=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
    )


@api.post("/process", response_model=models.ProcessResponse)
async def process_document(
        file: UploadFile = File(..., description="The PDF document to process"),
        include_images: bool = False,
        first_page: int = 1,
        last_page: int = None,
):
    """
    Extract slices from a PDF document.

    Args:
        file: The PDF document to process.
        include_images: Whether to include images in the response.
        first_page: The first page to process.
        last_page: The last page to process.

    Returns:
        The list of slices extracted from the document.
    """
    # Error if the file is not a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are supported.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix="pdf") as temp_file:
        # noinspection PyTypeChecker
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name

    with pymupdf.open(temp_file_path) as pdf:
        pages_count = len(pdf)

    if last_page is None:
        last_page = sys.maxsize

    page_range = (max(1, first_page), min(pages_count, last_page))

    try:
        pages = process_file(
            temp_file_path,
            extract_images=include_images,
            raises_on_error=False,
            page_range=page_range,
        )

        return models.ProcessResponse(
            document=file.filename,
            size=os.path.getsize(temp_file_path),
            content_type=file.content_type,
            first_page=page_range[0],
            last_page=page_range[1],
            total_pages=pages_count,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise e
        # raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}") from e

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
