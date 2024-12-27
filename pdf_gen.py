import os

from fpdf import FPDF
from PIL import Image
from tqdm import tqdm

import constants as c


def compress_image(image_path: str, dpi: int = 300, quality: int = 90) -> str:
    # Open image to PIL
    img = Image.open(image_path).convert("RGB")

    # Use JPEG compression
    compressed_image_filename = os.path.basename(image_path).replace(".png", ".jpg")
    compressed_image_path = os.path.join(c.COMPRESSED_DIR, compressed_image_filename)

    # Save to directory
    img.save(compressed_image_path, "JPEG", quality=quality, dpi=(dpi, dpi))

    return compressed_image_path


def render_pdf():
    # Get all original image files
    image_file_paths = sorted(
        [f for f in os.listdir(c.IMAGES_DIR) if f.endswith(f".{c.IMAGE_EXTENSION}")]
    )

    # Create PDF with blank page
    pdf = FPDF(
        orientation="portrait", unit=c.UNIT, format=(c.SHEET_RATIO[0], c.SHEET_RATIO[1])
    )
    pdf.add_page()

    # Current row(i) and column(j) in the current page
    i, j = 0, 0

    for image_path in tqdm(image_file_paths, desc="Adding images", unit="image(s) "):
        
        # Compress image before embedding in pdf
        compressed_image_path = compress_image(os.path.join(c.IMAGES_DIR, image_path))

        if i == c.IMAGE_FREQUENCY[0]:
            # at the end of a row
            j += 1
            if j == c.IMAGE_FREQUENCY[1]:
                # at the end of a page
                i, j = 0, 0
                pdf.add_page()
            else:
                i = 0

        # Top-left corner position in sheet
        x_offset = c.IMAGE_RATIO[0] * i + c.IMAGE_SPACING[0] * (i + 1)
        y_offset = c.IMAGE_RATIO[1] * j + c.IMAGE_SPACING[1] * (j + 1)

        # Embed the image
        pdf.image(
            compressed_image_path,
            x=x_offset,
            y=y_offset,
            w=c.IMAGE_RATIO[0],
            h=c.IMAGE_RATIO[1],
        )

        i += 1

    # Save PDF
    pdf.output(c.OUTPUT_PDF)

    return "PDF Created Successfully!"


if __name__ == "__main__":
    render_pdf()
