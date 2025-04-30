# Document Processor API

A FastAPI application that extracts structured content from PDF documents. This API processes PDF files and extracts content in a structured format including text, tables, and images with their positions and hierarchy.

## Features

- Extract content from PDF documents
- OCR capability with multiple pipeline options (fast, full, hybrid)
- Page and slice screenshots with configurable format and quality
- Content hierarchy extraction with parent-child relationships
- Table data extraction
- Customizable processing options (page range, image format, quality, scale)

## Models

### Enums

- **OcrPipeline**: Options for OCR processing
    - `FAST`: Optimized for speed
    - `FULL`: Optimized for accuracy
    - `HYBRID`: Balance between speed and accuracy

- **ImageFormat**: Supported image formats for screenshots
    - `JPEG`
    - `PNG`
    - `WEBP`

### Data Models

- **Image**: Represents an image
    - `data`: Base64 encoded image data
    - `content_type`: MIME type of the image
    - `width`: Width of the image in pixels
    - `height`: Height of the image in pixels

- **Position**: Represents the position of a slice in a document
    - `page_num`: The page number of the slice
    - `top`: The top position of the slice
    - `right`: The right position of the slice
    - `bottom`: The bottom position of the slice
    - `left`: The left position of the slice
    - `coord_origin`: The coordinate origin of the slice

- **Slice**: Represents a slice of content extracted from a document
    - `slice_num`: The number of the slice in the document
    - `level`: The level of the slice in the document hierarchy
    - `ref`: The reference ID of the slice
    - `parent_ref`: The reference ID of the parent slice
    - `label`: The label of the slice
    - `content_text`: The content text of the slice
    - `caption_text`: The caption of the slice (for tables and pictures)
    - `table_data`: The table data associated with the slice (for tables)
    - `positions`: The positions of the slice in the document
    - `screenshot`: The screenshot of the slice

- **Page**: Represents a page in a document
    - `page_num`: The page number of the document
    - `width`: The width of the page
    - `height`: The height of the page
    - `screenshot`: The screenshot of the page
    - `slices`: The slices on the page

- **ProcessRequest**: Request model for document processing
    - `ocr_pipeline`: The OCR pipeline to use (default: HYBRID)
    - `first_page`: The first page number to process (default: 1)
    - `last_page`: The last page number to process (default: None = all pages)
    - `image_format`: The image format for screenshots (default: WEBP)
    - `image_quality`: The quality of the image, 0-100 (default: 80)
    - `image_scale`: The scale factor for the images (default: 2.0)

- **ProcessResponse**: Response model for document processing
    - `document`: The document name
    - `content_type`: The MIME type of the document
    - `size`: The size of the document in bytes
    - `pages`: The pages of the document

- **HealthResponse**: Response model for health check
    - `version`: The version of the service
    - `build_id`: The build ID of the service
    - `commit_sha`: The commit SHA of the service
    - `up_since`: The date and time when the service started

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the service.

**Response**:
```json
{
  "version": "1.0.0",
  "build_id": "12345",
  "commit_sha": "abcdef",
  "up_since": "2025-04-30 12:00:00"
}
```

### Process Document

```
POST /process
```

Process a PDF document and extract structured content.

**Request Form Parameters**:

| Parameter                | Type         | Default | Description                                    |
|--------------------------|--------------|---------|------------------------------------------------|
| file                     | File         | -       | The PDF document to process                     |
| ocr_pipeline             | OcrPipeline  | HYBRID  | The OCR pipeline to use                        |
| first_page               | int          | 1       | The first page number to process               |
| last_page                | int or null  | null    | The last page number to process                |
| extract_pages_screenshot | bool         | true    | Whether to extract page screenshots            |
| extract_slices_screenshot| bool         | true    | Whether to extract slice screenshots           |
| image_format             | ImageFormat  | WEBP    | The image format for screenshots               |
| image_quality            | int          | 80      | The quality of images (0-100)                  |
| image_scale              | float        | 2.0     | The scale factor for images                    |

**Response**:
A ProcessResponse object containing the structured content of the document.

## Installation

### Prerequisites

- Python 3.10+
- FastAPI
- PDF processing libraries
- OCR capabilities

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/document-processor-api.git
   cd document-processor-api
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application
   ```bash
   uvicorn app.api:api --reload
   ```

## Environment Variables

The application uses the following environment variables:

- `ENV`: Environment (development, production)
- `VERSION`: Application version
- `BUILD_ID`: Build identifier
- `COMMIT_SHA`: Git commit SHA

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

- Joan Fabrégat <j@fabreg.at>