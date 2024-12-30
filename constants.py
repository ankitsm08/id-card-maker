import os

#* Constants for template

PICTURE_POSITION = (525, 790)  # Top-left corner of the picture
PICTURE_SIZE = (440, 440)  # Width and height of the picture in pixels

TEMPLATE_PATH = "example-template-id-card.png"  # Path to the template file
TEXT_POSITION = (220, 1265)  # Top-left starting position of text
#! TEXT_POSITION[0] is overridden if the text cant be fitted in the template
FONT_SIZE = 72  # Font size for text
FONT_PATH = "example-Exo-ExtraBold.otf"  # Path to the font file

TEXT_HEADINGS = ["Name", "Mobile", "Post"]  # Headings text
PADDING_HEADING = 25  # Padding between heading block
PADDING_INPUT = 45  # Padding between colon block and input (details) block

IMAGES_OUTPUT_PATH = "outputs/"


#* Constants for PDF generation

IMAGE_RATIO = (3.75, 5)  # Width and height of the image in UNIT
IMAGE_EXTENSION = os.path.splitext(TEMPLATE_PATH)[1]  # Extension of the original output image files

SHEET_RATIO = (12, 18)  # Width and height of the sheet in UNIT

IMAGE_FREQUENCY = (
    int(SHEET_RATIO[0] / IMAGE_RATIO[0]),
    int(SHEET_RATIO[1] / IMAGE_RATIO[1]),
)  # Number of images in each row and column

UNIT = "in"

IMAGE_SPACING = (
    (SHEET_RATIO[0] - IMAGE_FREQUENCY[0] * IMAGE_RATIO[0])
    / (IMAGE_FREQUENCY[0] + 1),
    (SHEET_RATIO[1] - IMAGE_FREQUENCY[1] * IMAGE_RATIO[1])
    / (IMAGE_FREQUENCY[1] + 1),
)  # Spacing between images keeping it equal everywhere

IMAGES_DIR = IMAGES_OUTPUT_PATH
OUTPUT_PDF = "output.pdf"

COMPRESSED_DIR = "compressed/"


# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create directories if they don't exist
for path in [IMAGES_DIR, COMPRESSED_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)
