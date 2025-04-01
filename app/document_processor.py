#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

import tempfile

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
    MODEL_NAME = "ds4sd/SmolDocling-256M-preview-mlx-bf16"

    def __init__(self):
        self.model, self.processor = load(self.MODEL_NAME)
        self.config = load_config(self.MODEL_NAME)
        self.formatted_prompt = apply_chat_template(
            self.processor,
            self.config,
            prompt="Convert this page to docling.",
            num_images=1
        )
        self.matrix = fitz.Matrix(3, 3)

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

    @staticmethod
    def _extract_slices(document: DoclingDocument) -> list[models.Slice]:
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
                        label=str(item.label.value),
                        content=item.text if isinstance(item, TextItem) else item.export_to_markdown(),
                        content_mime_type="text/plain" if isinstance(item, TextItem) else "text/markdown",
                        positions=[
                            models.SlicePosition(
                                page_no=prov.page_no,
                                top=round(prov.bbox.t, 2),
                                right=round(prov.bbox.r, 2),
                                bottom=round(prov.bbox.b, 2),
                                left=round(prov.bbox.l, 2),
                                coord_origin=models.SlicePosition.CoordOrigin(prov.bbox.coord_origin.name)
                            ) for prov in item.prov
                        ]
                    )
                )
                sequence += 1
        return slices
