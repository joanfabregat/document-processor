#  Copyright (c) 2025 Code Inc. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Visit <https://www.codeinc.co> for more information

from time import time

from docling.utils.model_downloader import download_models

from app.logging import logger

logger.info("Downloading models...")
start = time()
download_models(with_easyocr=True)
logger.info(f"Models downloaded successfully in {time() - start:.2f} seconds.")
