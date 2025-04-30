# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import models, logger, config
from app.services.content_extractor import ContentExtractor
from app.services.model_adapters import PageModelAdapter, SliceModelAdapter, ImageModelAdapter

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
    Health check endpoint.
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
        ocr_pipeline: models.OcrPipeline = Form(default=models.OcrPipeline.HYBRID,
                                                description="The OCR pipeline to use"),
        first_page: int = Form(default=1, description="The first page number to process"),
        last_page: int | None = Form(default=None, description="The last page number to process"),
        extract_pages_screenshot: bool = Form(default=True,
                                              description="Whether to extract the screenshot of the pages"),
        extract_slices_screenshot: bool = Form(default=True,
                                               description="Whether to extract the screenshot of the slices"),
        image_format: models.ImageFormat = Form(default=models.ImageFormat.WEBP,
                                                description="The image format for the screenshots"),
        image_quality: int = Form(default=80, description="The quality of the image (0-100)"),
        image_scale: float = Form(default=2.0, description="The scale factor for the images"),
) -> models.ProcessResponse:
    """
    Extract slices from a PDF document.
    """
    # Check if the file is a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are supported.",
        )

    # Read the file content
    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty file. Please upload a valid PDF document.",
        )

    try:
        # Initialize the content extractor
        content_extractor = ContentExtractor(
            ocr_pipeline=ocr_pipeline,
            bytes_or_path=file_bytes,
            filename=file.filename,
            images_scale=image_scale,
        )

        # Initialize the model adapters
        image_model_adapter = ImageModelAdapter(
            image_format=image_format,
            image_quality=image_quality
        )
        slice_model_adapter = SliceModelAdapter(
            image_model_adapter=image_model_adapter,
            extract_screenshot=extract_slices_screenshot
        )
        page_model_adapter = PageModelAdapter(
            slice_model_adapter=slice_model_adapter,
            image_model_adapter=image_model_adapter,
            extract_screenshot=extract_pages_screenshot
        )

        # Extract the specified range of pages from the PDF document
        pages = []
        for _, page in content_extractor.extract_pages(first_page, last_page):
            if page:
                page_model = page_model_adapter.get_model(page)
                pages.append(page_model)

        return models.ProcessResponse(
            document=file.filename,
            size=file.size,
            content_type=file.content_type,
            pages=pages,
        )
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}") from e
