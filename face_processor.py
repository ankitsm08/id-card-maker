import hashlib

import cv2
import numpy as np
from PIL import Image
from PIL.ImageFile import ImageFile

# Cache to store detected faces
face_cache = {}

# Preload the face detection model
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
)


# Calculate the hash of the image to use as a key in the cache
def calculate_image_hash(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Calculate the MD5 hash of the image data
    return hashlib.md5(image_data).hexdigest()


def crop_to_square(image: ImageFile) -> ImageFile:
    """Crop the image to a square by taking the center portion."""
    width, height = image.size
    if width == height:
        # Already square
        return image
    elif width > height:
        # Crop width
        left = (width - height) // 2
        right = left + height
        return image.crop((left, 0, right, height))
    else:
        # Crop height
        top = (height - width) // 2
        bottom = top + width
        return image.crop((0, top, width, bottom))


# Detect the face in the image and crop it so the face occupies the target_face_size in a square output
def crop_face_to_square(
    image: ImageFile, target_face_size: float, face_num: int
) -> tuple[ImageFile, str]:

    # Generate a unique hash for the image
    image_hash = calculate_image_hash(image.filename)

    # Convert PIL Image to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    faces = []

    # Check if faces for this image are already cached
    if image_hash in face_cache:
        faces = face_cache[image_hash]
    else:
        # Detect faces in the image
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 50)
        )

        face_cache[image_hash] = faces

    if len(faces) == 0:
        return None, "No face detected. Please try another image."

    elif len(faces) > 1:
        # Sort faces by x-coordinate
        faces = sorted(faces, key=lambda rect: rect[0])

    # Get the face coordinates of the first_num-th face from left to right
    x, y, w, h = faces[min(face_num, len(faces)) - 1]

    # Calculate new crop dimensions to make the face cover target_face_size % of image
    face_center_x, face_center_y = x + w // 2, y + h // 2

    # Crop size cannot exceed the image size
    desired_crop_size = int(max(w, h) / target_face_size)

    # Make the crop area square while ensuring it fits the image
    half_square_crop_size = min(desired_crop_size, *image_cv.shape[:2]) // 2

    # Calculate the crop coordinates
    left = max(face_center_x - half_square_crop_size, 0)
    top = max(face_center_y - half_square_crop_size, 0)
    right = min(face_center_x + half_square_crop_size, image_cv.shape[1])
    bottom = min(face_center_y + half_square_crop_size, image_cv.shape[0])

    # Crop the image
    cropped_img = image_cv[top:bottom, left:right]

    # Convert back to PIL format for Gradio compatibility
    img_pil = Image.fromarray(cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB))

    # Ensuring square output
    square_img_pil = crop_to_square(img_pil)

    return square_img_pil, "Face detected and cropped successfully."
