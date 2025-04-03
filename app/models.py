# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

from docling_core.types import doc as docling_types
from pydantic import BaseModel, Field


class Page(BaseModel):
    """Represents a page in a document."""
    page_no: int = Field(..., description="The page number of the document")
    width: float = Field(..., description="The width of the page")
    height: float = Field(..., description="The height of the page")


class Slice(BaseModel):
    """Represents a slice of content extracted from a document."""

    class Position(BaseModel):
        """Represents the position of a slice in a document."""
        page_no: int = Field(..., description="The page number of the slice")
        top: float = Field(..., description="The top position of the slice")
        right: float = Field(..., description="The right position of the slice")
        bottom: float = Field(..., description="The bottom position of the slice")
        left: float = Field(..., description="The left position of the slice")
        coord_origin: docling_types.CoordOrigin = Field(..., description="The coordinate origin of the slice")

    level: int = Field(..., description="The level of the slice in the document hierarchy")
    ref: str = Field(..., description="The reference ID of the slice")
    sequence: int = Field(..., description="The sequence number of the slice in the document")
    parent_ref: str = Field(..., description="The reference ID of the parent slice")
    label: docling_types.DocItemLabel = Field(..., description="The label of the slice")
    content: str = Field(..., description="The content of the slice")
    content_mime_type: str = Field(..., description="The MIME type of the content")
    table_data: list | None = Field(..., description="The table data of the slice (if applicable)")
    positions: list[Position] = Field(default_factory=list, description="The positions of the slice in the document")


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""
    version: str = Field(..., description="The version of the service")
    build_id: str = Field(..., description="The build ID of the service")
    commit_sha: str = Field(..., description="The commit SHA of the service")
    up_since: str = Field(..., description="The date and time when the service started")


class ProcessResponse(BaseModel):
    """Response model for the document processing endpoint."""
    document: str = Field(..., description="The document name")
    size: int = Field(..., description="The size of the document in bytes")
    content_type: str = Field(..., description="The MIME type of the document")
    pages: list[Page] = Field(..., description="The pages of the document")
    slices: list[Slice] = Field(..., description="The slices extracted from the document")
