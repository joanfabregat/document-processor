#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from docling_core.types import doc as docling_types
from pydantic import BaseModel, Field


class Slice(BaseModel):
    class Position(BaseModel):
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
    positions: list[Position] = Field(default_factory=list, description="The positions of the slice in the document")


class HealthResponse(BaseModel):
    version: str = Field(..., description="The version of the service")
    build_id: str = Field(..., description="The build ID of the service")
    commit_sha: str = Field(..., description="The commit SHA of the service")
    up_since: str = Field(..., description="The date and time when the service started")


class ProcessResponse(BaseModel):
    document: str = Field(..., description="The document name")
    size: int = Field(..., description="The size of the document in bytes")
    content_type: str = Field(..., description="The MIME type of the document")
    slices: list[Slice] = Field(..., description="The slices extracted from the document")
