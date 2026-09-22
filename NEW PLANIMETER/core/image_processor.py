"""
Image Processing Engine for New Planimeter
Handles image loading (Unicode/Windows safe), grayscale conversion, noise reduction,
contrast enhancement (CLAHE), adaptive thresholding, Canny edge detection,
morphological operations, and 4-point perspective homography correction.
"""

from typing import List, Tuple, Dict, Any, Optional
import os
import cv2
import numpy as np


class ImageProcessor:
    """
    OpenCV-based image processing and computer vision pipeline.
    """

    @staticmethod
    def load_image(filepath: str) -> np.ndarray:
        """
        Load image safely handling Unicode filepaths and multiple formats.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Image file does not exist: {filepath}")

        # Windows Unicode safe loading via np.fromfile
        with open(filepath, "rb") as f:
            bytes_data = bytearray(f.read())
            np_arr = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError(f"Failed to decode image file: {filepath}")

        return img

    @staticmethod
    def save_image(filepath: str, img: np.ndarray) -> bool:
        """
        Save image safely handling Unicode filepaths.
        """
        ext = os.path.splitext(filepath)[1]
        if not ext:
            ext = ".png"
            filepath += ext
        success, encoded = cv2.imencode(ext, img)
        if success:
            with open(filepath, "wb") as f:
                f.write(encoded.tobytes())
            return True
        return False

    @staticmethod
    def to_grayscale(img: np.ndarray) -> np.ndarray:
        if len(img.shape) == 2:
            return img.copy()
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def apply_noise_reduction(gray: np.ndarray, method: str = "gaussian",
                               ksize: int = 5, sigma: float = 1.5) -> np.ndarray:
        """
        Noise reduction filter: Gaussian blur or Bilateral filter (edge-preserving).
        """
        if ksize % 2 == 0:
            ksize += 1
        ksize = max(3, ksize)

        if method == "bilateral":
            return cv2.bilateralFilter(gray, d=ksize, sigmaColor=75, sigmaSpace=75)
        elif method == "median":
            return cv2.medianBlur(gray, ksize)
        else:  # gaussian
            return cv2.GaussianBlur(gray, (ksize, ksize), sigma)

    @staticmethod
    def enhance_contrast(gray: np.ndarray, method: str = "clahe",
                         clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
        """
        Contrast enhancement: CLAHE or standard Histogram Equalization.
        """
        if method == "clahe":
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
            return clahe.apply(gray)
        elif method == "equalize":
            return cv2.equalizeHist(gray)
        return gray.copy()

    @staticmethod
    def apply_threshold(gray: np.ndarray, method: str = "otsu",
                        thresh_val: int = 127, max_val: int = 255,
                        block_size: int = 11, c_val: int = 2,
                        invert: bool = True) -> np.ndarray:
        """
        Thresholding methods: Otsu, Adaptive Gaussian, Adaptive Mean, Binary.
        """
        if block_size % 2 == 0:
            block_size += 1
        block_size = max(3, block_size)

        inv_flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY

        if method == "otsu":
            _, binary = cv2.threshold(gray, 0, max_val, cv2.THRESH_OTSU | inv_flag)
            return binary
        elif method == "adaptive_gaussian":
            return cv2.adaptiveThreshold(gray, max_val, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         inv_flag, block_size, c_val)
        elif method == "adaptive_mean":
            return cv2.adaptiveThreshold(gray, max_val, cv2.ADAPTIVE_THRESH_MEAN_C,
                                         inv_flag, block_size, c_val)
        else:  # manual binary
            _, binary = cv2.threshold(gray, thresh_val, max_val, inv_flag)
            return binary

    @staticmethod
    def apply_canny(gray: np.ndarray, low_thresh: int = 50, high_thresh: int = 150,
                    aperture_size: int = 3) -> np.ndarray:
        """
        Canny edge detection.
        """
        if aperture_size not in [3, 5, 7]:
            aperture_size = 3
        return cv2.Canny(gray, low_thresh, high_thresh, apertureSize=aperture_size)

    @staticmethod
    def apply_morphology(binary: np.ndarray, op: str = "close",
                         kernel_size: int = 3, iterations: int = 1) -> np.ndarray:
        """
        Morphological operations: close, open, dilate, erode.
        """
        if kernel_size < 1:
            return binary.copy()
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

        if op == "close":
            return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        elif op == "open":
            return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=iterations)
        elif op == "dilate":
            return cv2.dilate(binary, kernel, iterations=iterations)
        elif op == "erode":
            return cv2.erode(binary, kernel, iterations=iterations)
        return binary.copy()

    @staticmethod
    def perspective_homography(img: np.ndarray, src_pts: List[Tuple[float, float]],
                               margin: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply 4-point perspective correction (homography) to convert angled photo
        to orthorectified top-down plan view.
        
        Args:
            img: Input BGR image.
            src_pts: 4 corner points [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]
                     ordered: top-left, top-right, bottom-right, bottom-left.
                     
        Returns:
            (warped_image, homography_matrix)
        """
        if len(src_pts) != 4:
            raise ValueError("Perspective homography requires exactly 4 reference points.")

        pts = np.array(src_pts, dtype=np.float32)

        # Order points: [top-left, top-right, bottom-right, bottom-left]
        # Sums: TL has smallest sum, BR has largest sum
        # Diffs: TR has smallest diff (x - y), BL has largest diff
        s = pts.sum(axis=1)
        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        tr = pts[np.argmin(diff)]
        bl = pts[np.argmax(diff)]

        ordered_src = np.array([tl, tr, br, bl], dtype=np.float32)

        # Compute output width & height
        width_top = np.linalg.norm(tr - tl)
        width_bot = np.linalg.norm(br - bl)
        max_width = int(max(width_top, width_bot))

        height_right = np.linalg.norm(br - tr)
        height_left = np.linalg.norm(bl - tl)
        max_height = int(max(height_right, height_left))

        max_width = max(max_width, 100)
        max_height = max(max_height, 100)

        dst_pts = np.array([
            [margin, margin],
            [max_width - 1 - margin, margin],
            [max_width - 1 - margin, max_height - 1 - margin],
            [margin, max_height - 1 - margin]
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(ordered_src, dst_pts)
        warped = cv2.warpPerspective(img, matrix, (max_width, max_height),
                                     flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

        return warped, matrix

    @classmethod
    def process_full_pipeline(cls, img: np.ndarray, params: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Execute full image preprocessing pipeline based on configuration parameters.
        Returns intermediate and final images for visualization and inspection.
        """
        gray = cls.to_grayscale(img)

        # Noise reduction
        blur_method = params.get("blur_method", "gaussian")
        blur_ksize = params.get("blur_ksize", 3)
        blurred = cls.apply_noise_reduction(gray, method=blur_method, ksize=blur_ksize)

        # Contrast enhancement
        enhance_method = params.get("enhance_method", "clahe")
        clip_limit = params.get("clip_limit", 2.0)
        enhanced = cls.enhance_contrast(blurred, method=enhance_method, clip_limit=clip_limit)

        # Thresholding
        thresh_method = params.get("thresh_method", "otsu")
        thresh_val = params.get("thresh_val", 127)
        block_size = params.get("block_size", 11)
        c_val = params.get("c_val", 2)
        invert = params.get("invert", True)
        binary = cls.apply_threshold(enhanced, method=thresh_method, thresh_val=thresh_val,
                                     block_size=block_size, c_val=c_val, invert=invert)

        # Canny edge detection
        use_canny = params.get("use_canny", False)
        canny_low = params.get("canny_low", 50)
        canny_high = params.get("canny_high", 150)
        canny = cls.apply_canny(enhanced, low_thresh=canny_low, high_thresh=canny_high)

        # Morphology
        morph_op = params.get("morph_op", "close")
        morph_ksize = params.get("morph_ksize", 3)
        morph_iter = params.get("morph_iter", 1)

        source_for_morph = canny if use_canny else binary
        morphed = cls.apply_morphology(source_for_morph, op=morph_op,
                                       kernel_size=morph_ksize, iterations=morph_iter)

        return {
            "grayscale": gray,
            "blurred": blurred,
            "enhanced": enhanced,
            "binary": binary,
            "canny": canny,
            "processed": morphed
        }
