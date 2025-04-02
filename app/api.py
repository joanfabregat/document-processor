#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

import datetime
import os
import shutil
import tempfile

from app import models, logger, config
from app.document_processor import DocumentProcessor
from fastapi import FastAPI, UploadFile, File, HTTPException

start_dt = datetime.datetime.now()

##
# Start FastAPI app
##
logger.info("Starting FastAPI app...")
api = FastAPI(
    title="Sophos inferencing API",
    version=config.VERSION,
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
async def process_document(file: UploadFile = File(..., description="The PDF document to process")):
    """
    Extract slices from a PDF document.

    Args:
        file: The PDF document to process.

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

    try:
        doc_proc = DocumentProcessor.from_file(temp_file.name, bbox_precision=config.BBOX_PRECISION)
        pages = doc_proc.process_pages()
        slices = doc_proc.process_slices()
        return models.ProcessResponse(
            document=file.filename,
            size=os.path.getsize(temp_file_path),
            content_type=file.content_type,
            pages=pages,
            slices=slices
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
