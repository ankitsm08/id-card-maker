from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFile import ImageFile

import constants as c
import face_processor


# Format the phone number into two groups of 5 digits
def format_phone_number(phone: str):
    pphone = phone.strip().replace(" ", "")

    if len(pphone) != 10 or not pphone.isdigit():
        return False, "Phone number must be exactly 10 digits."

    return True, f"{pphone[:5]} {pphone[5:]}"


# Validate name and post for basic correctness
def validate_text(name: str, post: str):
    pname = name.strip()
    ppost = post.strip()

    if not pname:
        return (False, "Name cannot be empty.")
    elif not 2 <= len(pname.split()) <= 3:
        return (
            False,
            "Name must be in the format '{First-Name} {Middle-Name*} {Last-Name}'.\n"
            " * [Middle-Name] is optional",
        )
    if not ppost:
        return (False, "Post cannot be empty.")

    return True, (pname.title(), ppost.title())


# Generate ID card with given image and applicant details
def generate_id_card(
    person_image: ImageFile,
    target_face_size: float,
    face_num: int,
    force_image: bool,
    name: str,
    phone: str,
    post: str,
):
    # Validate name and post
    valid_text, text_result = validate_text(name, post)
    if not valid_text:
        return None, text_result

    # Validate and format the phone number
    valid_phone, phone_result = format_phone_number(phone)
    if not valid_phone:
        return None, phone_result

    name, post = text_result
    formatted_phone = phone_result

    # Load the template
    template = Image.open(c.TEMPLATE_PATH)

    if force_image:
        person_img = (
            Image.open(person_image) if type(person_image) == str else person_image
        )
        person_img = face_processor.crop_to_square(person_img)
    else:
        # Open and process the person's image
        person_img = Image.open(person_image)

        person_img, msg = face_processor.crop_face_to_square(
            person_img, target_face_size, face_num
        )

        if person_img is None:
            return None, msg

    # Resize the image to fit the template
    person_img = person_img.resize(c.PICTURE_SIZE)

    # Paste the image onto the template
    template.paste(person_img, c.PICTURE_POSITION)

    draw = ImageDraw.Draw(template)
    font = ImageFont.truetype(c.FONT_PATH, c.FONT_SIZE)

    # Calculate required size and position for text
    max_headings_width = 0
    for heading in c.TEXT_HEADINGS:
        max_headings_width = max(
            max_headings_width, draw.textlength(heading, font=font)
        )

    colon_width = draw.textlength(":", font=font)

    max_input_width = max(
        draw.textlength(name, font=font),
        draw.textlength(formatted_phone, font=font),
        draw.textlength(post, font=font),
    )

    total_width = (
        max_headings_width
        + c.PADDING_HEADING
        + colon_width
        + c.PADDING_INPUT
        + max_input_width
    )

    # Check if the text fits in the template if started from set position
    text_position = c.TEXT_POSITION
    if total_width + c.TEXT_POSITION[0] > template.size[0]:
        text_position = ((template.size[0] - total_width) // 2, c.TEXT_POSITION[1])

    # Add name, phone, and post headings
    draw.text(
        text_position,
        "\n".join(c.TEXT_HEADINGS),
        fill="black",
        font=font,
        stroke_fill="white",
        stroke_width=8,
        spacing=16,
    )

    colon_position = (
        text_position[0] + max_headings_width + c.PADDING_HEADING,
        text_position[1],
    )

    # Add the colons
    draw.text(
        colon_position,
        "\n".join([":"] * len(c.TEXT_HEADINGS)),
        fill="black",
        font=font,
        stroke_fill="white",
        stroke_width=8,
        spacing=16,
    )

    input_position = (
        text_position[0]
        + max_headings_width
        + c.PADDING_HEADING
        + colon_width
        + c.PADDING_INPUT,
        text_position[1],
    )

    # Add name, phone, and post inputs
    draw.text(
        input_position,
        "\n".join([name, formatted_phone, post]),
        fill="black",
        font=font,
        stroke_fill="white",
        stroke_width=8,
        spacing=16,
    )

    # Save the final ID card with name, phone, and post in filename
    output_path = (
        f"{c.IMAGES_OUTPUT_PATH}ID_Card_{name.replace(' ', '_')}_"
        f"{formatted_phone.replace(' ', '')}_{post.replace(' ', '_')}.{c.IMAGE_EXTENSION}"
    )

    template.save(output_path)

    return output_path, "ID card generated successfully!"
