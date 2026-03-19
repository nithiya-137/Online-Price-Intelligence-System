from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import io
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocesses uploaded image bytes for MobileNetV2.
    - Converts to RGB
    - Applies slight contrast + sharpening for better feature extraction
    - Letterbox-resizes to 224x224 preserving aspect ratio
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        if image.mode != "RGB":
            image = image.convert("RGB")

        # Slight contrast boost helps model distinguish product from background
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.15)

        # Sharpen slightly to help with edge detection features
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3))

        # Letterbox resize to 224x224 preserving aspect ratio
        target_size = (224, 224)
        image.thumbnail(target_size, Image.Resampling.LANCZOS)

        new_image = Image.new("RGB", target_size, (255, 255, 255))
        paste_pos = (
            (target_size[0] - image.size[0]) // 2,
            (target_size[1] - image.size[1]) // 2,
        )
        new_image.paste(image, paste_pos)

        img_array = img_to_array(new_image)
        img_array = np.expand_dims(img_array, axis=0)
        processed_image = preprocess_input(img_array)

        return processed_image
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")
