import cv2
import numpy as np
import logging
from typing import List
from ..models.input_models import CropImage

logger = logging.getLogger(__name__)


class ImageValidationResult:
    def __init__(self, is_valid: bool, reason: str | None = None):
        self.is_valid = is_valid
        self.reason = reason


class ImageValidationService:

    ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")
    MIN_WIDTH = 400
    MIN_HEIGHT = 400
    BLUR_THRESHOLD = 100.0   # tweak later

    @staticmethod
    def validate_images(images: List[CropImage]) -> ImageValidationResult:
        print(f"\n📷 IMAGE VALIDATION REPORT")
        print(f"┌{'─'*15}┬{'─'*10}┬{'─'*20}┐")
        print(f"│{'Check':^15}│{'Status':^10}│{'Details':^20}│")
        print(f"├{'─'*15}┼{'─'*10}┼{'─'*20}┤")
        
        if not images:
            print(f"│{'Images Count':^15}│{'FAIL':^10}│{'No images provided':^20}│")
            print(f"└{'─'*15}┴{'─'*10}┴{'─'*20}┘")
            return ImageValidationResult(False, "No images provided")

        print(f"│{'Images Count':^15}│{'PASS':^10}│{len(images)} images found{'':^7}│")

        if len(images) > 3:
            print(f"│{'Image Limit':^15}│{'FAIL':^10}│{'Too many images':^20}│")
            print(f"└{'─'*15}┴{'─'*10}┴{'─'*20}┘")
            return ImageValidationResult(False, "Too many images. Upload max 3.")

        print(f"│{'Image Limit':^15}│{'PASS':^10}│{'Within limit (≤3)':^20}│")

        for i, img in enumerate(images, 1):
            result = ImageValidationService._validate_single_image(img)
            if not result.is_valid:
                print(f"│{'Image {i}':^15}│{'FAIL':^10}│{result.reason[:20]:^20}│")
                print(f"└{'─'*15}┴{'─'*10}┴{'─'*20}┘")
                return result
            print(f"│{'Image {i}':^15}│{'PASS':^10}│{'Valid format/size':^20}│")

        print(f"└{'─'*15}┴{'─'*10}┴{'─'*20}┘")
        return ImageValidationResult(True)

    @staticmethod
    def _validate_single_image(image: CropImage) -> ImageValidationResult:
        if not image.image_url.lower().endswith(
            ImageValidationService.ALLOWED_EXTENSIONS
        ):
            return ImageValidationResult(False, "Unsupported image format")

        img = cv2.imread(image.image_url)

        if img is None:
            return ImageValidationResult(False, "Image file not readable")

        height, width = img.shape[:2]

        if width < ImageValidationService.MIN_WIDTH or height < ImageValidationService.MIN_HEIGHT:
            return ImageValidationResult(False, "Image resolution too low")

        if ImageValidationService._is_blurry(img):
            return ImageValidationResult(False, "Image is blurry")

        if ImageValidationService._poor_lighting(img):
            return ImageValidationResult(False, "Poor lighting detected")

        return ImageValidationResult(True)

    @staticmethod
    def _is_blurry(img) -> bool:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        logger.debug(f"Blur variance: {variance}")
        return variance < ImageValidationService.BLUR_THRESHOLD

    @staticmethod
    def _poor_lighting(img) -> bool:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_intensity = np.mean(gray)

        return mean_intensity < 40 or mean_intensity > 220
