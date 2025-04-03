# Document Processor

[![Build and Push to GHCR and Docker Hub](https://github.com/joanfabregat/document-processor/actions/workflows/build-and-deploy.yaml/badge.svg)](https://github.com/joanfabregat/document-processor/actions/workflows/build-and-deploy.yaml)

## Overview

Document Processor is a FastAPI-based service that processes documents and extracts structured content as "slices". The API takes document files (primarily PDFs) as input and returns a structured representation of the document content, preserving the document hierarchy, positioning, and formatting.

## Features

- Document processing with text extraction
- OCR (Optical Character Recognition) for scanned documents
- Table structure recognition and extraction
- Hierarchical document structure preservation
- Precise positioning information for each content slice

## API Endpoints

### Health Check

```
GET /health
```

Returns information about the service status, including version, build ID, commit SHA, and uptime.

**Response Example:**

```json
{
  "version": "1.0.0",
  "build_id": "20250401-1",
  "commit_sha": "a1b2c3d4e5f6",
  "up_since": "2025-04-01 08:00:00"
}
```

### Process Document

```
POST /process
```

Processes a document file and extracts its content as structured slices.

**Request:**
- Content-Type: multipart/form-data
- Body: file (The document file to process)

**Response:**
Returns a list of document slices, each containing:
- Level in document hierarchy
- Reference ID
- Sequence number
- Parent reference ID
- Label
- Content
- Content MIME type (text/plain or text/markdown)
- Table data
- Positions (coordinates of the content on document pages)

**Response Example:**

```json
{
  "slices": [
    {
      "level": 1,
      "ref": "ref123",
      "sequence": 0,
      "parent_ref": "parent_ref",
      "label": "Title",
      "content": "Document Title",
      "content_mime_type": "text/plain",
      "table_data": null,
      "positions": [
        {
          "page_no": 1,
          "top": 100.0,
          "right": 500.0,
          "bottom": 120.0,
          "left": 50.0,
          "coord_origin": "TOPLEFT"
        }
      ]
    },
    {
      "level": 2,
      "ref": "ref124",
      "sequence": 1,
      "parent_ref": "ref123",
      "label": "Paragraph",
      "content": "Content of the paragraph...",
      "content_mime_type": "text/plain",
      "positions": [
        {
          "page_no": 1,
          "top": 150.0,
          "right": 550.0,
          "bottom": 200.0,
          "left": 50.0,
          "coord_origin": "TOPLEFT"
        }
      ]
    }
  ]
}
```

## Technical Details

### Dependencies

- Python 3.8+
- FastAPI
- Pydantic
- Docling (proprietary document processing library)

### Document Processing Pipeline

The API uses a document processing pipeline that includes:
- PDF parsing
- OCR for image-based content
- Table structure recognition
- Text extraction
- Hierarchical document structure analysis

### Data Models

#### Slice
Represents a piece of content extracted from the document:
- `level`: Hierarchical level in the document
- `ref`: Reference ID
- `sequence`: Sequential order in the document
- `parent_ref`: Reference to parent element
- `label`: Content label/type
- `content`: Actual text content
- `content_mime_type`: MIME type of the content (text/plain or text/markdown)
- `table_data`: Optional table data (if applicable)
- `positions`: List of position information

#### SlicePosition
Represents the position of a slice on a document page:
- `page_no`: Page number
- `top`, `right`, `bottom`, `left`: Bounding box coordinates
- `coord_origin`: Coordinate origin (TOPLEFT or BOTTOMLEFT)

## Setup and Deployment

### Running the API

You can run the API using Docker or directly with Uvicorn.

```bash
# Docker 
docker run --rm -p 8000:8000 joanfabregat/document-processor:latest

# Development
uvicorn app.api:api --reload

# Production
uvicorn app.api:api --host 0.0.0.0 --port 8000
```

## License

The Document Processor is licensed under the MIT License. See the [LICENSE](https://github.com/joanfabregat/document-processor/blob/main/LICENCE) file for details.