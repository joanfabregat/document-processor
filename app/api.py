# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import models, logger, config
from app.services.content_extraction import ContentExtractor

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

# CORS middleware
# noinspection PyTypeChecker
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


##
# Routes
##
@api.get("/", include_in_schema=False)
async def root():
    """
    Redirect to the OpenAPI documentation.
    """
    return RedirectResponse(url="/docs")


@api.get("/health")
async def health() -> models.HealthResponse:
    """
    Root endpoint.
    """
    return models.HealthResponse(
        version=config.VERSION,
        build_id=config.BUILD_ID,
        commit_sha=config.COMMIT_SHA,
        up_since=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
    )


@api.post("/process")
async def process_document(
        file: UploadFile = File(..., description="The PDF document to process"),
        params: models.ProcessRequest = Depends(),
) -> models.ProcessResponse:
    """
    Extract slices from a PDF document.

    Args:
        file: The PDF document to process.
        params: The parameters for processing the document.

    Returns:
        The list of slices extracted from the document.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are supported.",
        )

    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty file. Please upload a valid PDF document.",
        )

    try:
        # Extract the specified range of pages from the PDF document
        content_extractor = ContentExtractor(
            bytes_or_path=file_bytes,
            filename=file.filename,
            images_scale=params.image_scale,

        )

        pages = content_extractor.extract_pages_model(
            first_page=params.first_page,
            last_page=params.last_page,
            image_format=params.image_format,
            image_quality=params.image_quality,
        )

        # Extract the pages and slices
        return models.ProcessResponse(
            document=file.filename,
            size=file.size,
            content_type=file.content_type,
            pages=pages,
        )
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}") from e
