#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

import tempfile
import time

import fitz
from PIL import Image
from app import models
from app.logging import logger
from docling_core.types.doc.document import DocTagsDocument, DoclingDocument
from docling_core.types.doc.document import TextItem, TableItem
from mlx_vlm import load
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config, stream_generate
from tqdm import tqdm


class DocumentProcessor:
    """
    A service to extract text content from a document using the SmolDocling model.

    https://huggingface.co/ds4sd/SmolDocling-256M-preview
    https://huggingface.co/ds4sd/SmolDocling-256M-preview-mlx-bf16
    """
    MODEL_NAME = "ds4sd/SmolDocling-256M-preview-mlx-bf16"
    ZOOM_LEVEL = 3

    def __init__(self):
        self.model, self.processor = load(self.MODEL_NAME)
        self.config = load_config(self.MODEL_NAME)
        self.formatted_prompt = apply_chat_template(
            self.processor,
            self.config,
            prompt="Convert this page to docling.",
            num_images=1
        )
        self.matrix = fitz.Matrix(self.ZOOM_LEVEL, self.ZOOM_LEVEL)

    @classmethod
    def download_model(cls):
        """
        Download the model from Hugging Face.
        """
        logger.info(f"Downloading model {cls.MODEL_NAME}...")
        start_time = time.time()
        load(cls.MODEL_NAME)
        logger.info(f"Model {cls.MODEL_NAME} downloaded successfully in {time.time() - start_time:.2f} seconds.")

    def process(self, pdf_path: str) -> list[models.Slice]:
        """
        Process a file and extract slices.

        Args:
            pdf_path: The path to the file.
            raises_on_error: Whether to raise an error if the extraction fails.

        Returns:
            A list of document slices.
        """
        logger.info(f"Extracting text from PDF document {pdf_path} using the {self.MODEL_NAME} model")
        document = self._convert_using_smol(pdf_path)

        slices = self._extract_slices(document)
        logger.info(f"Extracted {len(slices)} slices from file: {pdf_path}")
        return slices

    def _convert_using_smol(self, pdf_path: str) -> DoclingDocument:
        doctags = []
        images = []

        with fitz.open(pdf_path) as pdf_document:
            pages_count = len(pdf_document)
            with tqdm(total=pages_count, desc="Processing pages", unit="page") as pbar:
                for page_num, page in enumerate(pdf_document):
                    logger.debug(f"Processing page {page_num + 1} of {pages_count}")

                    # Convert the page to a pixmap
                    pixmap = page.get_pixmap(matrix=self.matrix, alpha=False)

                    with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as temp_image:
                        # Save the pixmap to a temporary file
                        pixmap.save(temp_image.name)

                        # Extract the doctag from the temporary image
                        images.append(Image.open(temp_image.name))
                        doctags.append(self._extract_doctags_from_image(temp_image.name))
                        pbar.update(1)

        # Populate document
        logger.info("Populating document...")
        doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(
            doctags=doctags,
            images=images
        )

        # create a docling document
        logger.info("Creating Docling document...")
        doc = DoclingDocument(name="SampleDocument")
        doc.load_from_doctags(doctags_doc)

        return doc

    def _extract_doctags_from_image(self, image_path: str) -> str:
        tokens = stream_generate(
            self.model,
            self.processor,
            self.formatted_prompt,
            image=[image_path],
            max_tokens=4096,
            verbose=False
        )

        output: str = ""
        for token in tokens:
            output += token.text
            if "</doctag>" in token.text:
                break

        return output

    def _extract_slices(self, document: DoclingDocument) -> list[models.Slice]:
        slices = []
        sequence = 0
        for item, level in document.iterate_items():
            if isinstance(item, (TextItem, TableItem)):  # Other types of items are ignored
                slices.append(
                    models.Slice(
                        level=level,
                        ref=item.self_ref,
                        sequence=sequence,
                        parent_ref=item.parent.cref,
                        label=item.label,
                        content=item.text if isinstance(item, TextItem) else item.export_to_markdown(),
                        content_mime_type="text/plain" if isinstance(item, TextItem) else "text/markdown",
                        positions=[
                            models.Slice.Position(
                                page_no=prov.page_no,
                                top=round(prov.bbox.t / self.ZOOM_LEVEL, 2),
                                right=round(prov.bbox.r / self.ZOOM_LEVEL, 2),
                                bottom=round(prov.bbox.b / self.ZOOM_LEVEL, 2),
                                left=round(prov.bbox.l / self.ZOOM_LEVEL, 2),
                                coord_origin=prov.bbox.coord_origin
                            ) for prov in item.prov
                        ]
                    )
                )
                sequence += 1
        return slices
