# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

from docling_core.types import doc as docling_types
from pydantic import BaseModel, Field


class Image(BaseModel):
    data: str = Field(..., description="Base64 encoded image data")
    content_type: str = Field(..., description="MIME type of the image")
    width: int = Field(..., description="Width of the image in pixels")
    height: int = Field(..., description="Height of the image in pixels")


class Position(BaseModel):
    """Represents the position of a slice in a document."""
    page_no: int = Field(..., description="The page number of the slice")
    top: float = Field(..., description="The top position of the slice")
    right: float = Field(..., description="The right position of the slice")
    bottom: float = Field(..., description="The bottom position of the slice")
    left: float = Field(..., description="The left position of the slice")
    coord_origin: docling_types.CoordOrigin = Field(..., description="The coordinate origin of the slice")


class Slice(BaseModel):
    """Represents a slice of content extracted from a document."""

    slice_no: int = Field(..., description="The number of the slice in the document")
    level: int = Field(..., description="The level of the slice in the document hierarchy")
    ref: str = Field(..., description="The reference ID of the slice")
    parent_ref: str = Field(..., description="The reference ID of the parent slice")
    label: docling_types.DocItemLabel = Field(..., description="The label of the slice")
    content_text: str | None = Field(..., description="The content text of the slice")
    caption_text: str | None = Field(..., description="The caption of the slice (for tables and pictures)")
    table_data: list[list] | None = Field(..., description="The table data associated with the slice (for tables)")
    positions: list[Position] = Field(default_factory=list,
                                      description="The positions of the slice in the document")
    screenshot: Image | None = Field(None, description="The screenshot of the slice")


class Page(BaseModel):
    """Represents a page in a document."""
    page_no: int = Field(..., description="The page number of the document")
    width: float = Field(..., description="The width of the page")
    height: float = Field(..., description="The height of the page")
    screenshot: Image | None = Field(None, description="The height of the page")
    slices: list[Slice] = Field(default_factory=list, description="The slices on the page")


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""
    version: str = Field(..., description="The version of the service")
    build_id: str = Field(..., description="The build ID of the service")
    commit_sha: str = Field(..., description="The commit SHA of the service")
    up_since: str = Field(..., description="The date and time when the service started")


class ProcessRequest(BaseModel):
    first_page: int = Field(default=1, description="The first page number to process")
    last_page: int | None = Field(default=None, description="The last page number to process")
    include_page_screenshot: bool = Field(default=False, description="Whether to include a screenshot of the page")
    include_slice_screenshot: bool = Field(default=False, description="Whether to include a screenshot of the slice")
    image_format: str = Field(default="WEBP", description="The image format for the screenshots")
    image_quality: int = Field(default=80, description="The quality of the image (0-100)")
    image_scale: float = Field(default=2.0, description="The scale factor for the images")


class ProcessResponse(BaseModel):
    """Response model for the document processing endpoint."""
    document: str = Field(..., description="The document name")
    content_type: str = Field(..., description="The MIME type of the document")
    size: int = Field(..., description="The size of the document in bytes")
    pages: list[Page] = Field(..., description="The pages of the document")
