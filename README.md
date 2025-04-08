# Document Processor

[![Build and Push to GHCR and Docker Hub](https://github.com/joanfabregat/document-processor/actions/workflows/build-and-deploy.yaml/badge.svg)](https://github.com/joanfabregat/document-processor/actions/workflows/build-and-deploy.yaml)

## Overview

Document Processor is a FastAPI-based service that processes documents and extracts structured content as "slices". The API takes document files (primarily PDFs) as input and returns a structured representation of the document content, preserving the document hierarchy, positioning, and formatting.

## Features

- Document processing with text extraction
- Hierarchical document structure preservation
- Precise positioning information for each content slice
- Optional image extraction
- Page range selection for processing
- Table data extraction in multiple formats (Markdown and structured data)
- Support for captions in tables and images

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

Processes a PDF document file and extracts its content as structured slices.

**Request Parameters:**
- `file`: The PDF document to process (required)
- `include_images`: Whether to include images in the response (default: false)
- `first_page`: The first page to process (default: 1)
- `last_page`: The last page to process (default: all pages)

**Response:**
Returns a structured representation of the document, including:
- Document metadata (name, size, content type)
- Page count information (total pages, first and last page processed)
- List of pages, each containing:
  - Page metadata (page number, width, height)
  - List of slices on the page

**Response Example:**

```json
{
  "document": "example.pdf",
  "content_type": "application/pdf",
  "size": 123456,
  "total_pages": 10,
  "first_page": 1,
  "last_page": 10,
  "pages": [
    {
      "page_no": 1,
      "width": 595.0,
      "height": 842.0,
      "slices": [
        {
          "level": 1,
          "ref": "ref123",
          "sequence": 0,
          "parent_ref": "parent_ref",
          "label": "HEADING",
          "content_text": "Document Title",
          "caption_text": null,
          "content_markdown": null,
          "table_data": null,
          "png_image": null,
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
          "label": "TABLE",
          "content_text": null,
          "caption_text": "Table 1: Sample Data",
          "content_markdown": "| Header 1 | Header 2 |\n|---------|----------|\n| Data 1 | Data 2 |",
          "table_data": [["Header 1", "Header 2"], ["Data 1", "Data 2"]],
          "png_image": "base64encodedimage...",
          "positions": [
            {
              "page_no": 1,
              "top": 150.0,
              "right": 500.0,
              "bottom": 200.0,
              "left": 50.0,
              "coord_origin": "TOPLEFT"
            }
          ]
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
- PyMuPDF
- Docling Core (for document processing)

### Document Processing Pipeline

The API uses a document processing pipeline that includes:
- PDF parsing with PyMuPDF
- Content extraction and organization into slices
- Optional image extraction
- Positional information tracking
- Table data extraction in multiple formats

### Data Models

#### Page
Represents a page in the document:
- `page_no`: Page number
- `width`: Width of the page
- `height`: Height of the page
- `slices`: List of slices on the page

#### Slice
Represents a piece of content extracted from the document:
- `level`: Hierarchical level in the document
- `ref`: Reference ID
- `sequence`: Sequential order in the document
- `parent_ref`: Reference to parent element
- `label`: Content label/type (e.g., HEADING, PARAGRAPH, TABLE, PICTURE)
- `content_text`: The text content of the slice
- `caption_text`: The caption of the slice (for tables and pictures)
- `content_markdown`: The Markdown content of the slice (for tables)
- `table_data`: The table data associated with the slice (for tables)
- `png_image`: Optional base64 encoded PNG image (for tables and pictures)
- `positions`: List of position information

#### SlicePosition
Represents the position of a slice on a document page:
- `page_no`: Page number
- `top`, `right`, `bottom`, `left`: Bounding box coordinates
- `coord_origin`: Coordinate origin (TOPLEFT or other)

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

## Limitations

- Currently only supports PDF documents
- Large files may require additional processing time

## License

The Document Processor is licensed under the MIT License. See the [LICENSE](https://github.com/joanfabregat/document-processor/blob/main/LICENCE) file for details.