import os
import sys
from concurrent.futures import ThreadPoolExecutor

import gradio as gr
from PIL import Image
from tqdm import tqdm

import constants as c
import id_creator
import pdf_gen


# Extracts details from output image filenames into a dataframe
def get_id_card_details():
    id_cards_df = []
    # Skip non image files if any
    file_paths = sorted(
        [path for path in os.listdir(c.IMAGES_OUTPUT_PATH) if path.endswith(".png")]
    )
    for idx, fp in enumerate(file_paths, start=1):
        # Extract details from the filename
        parts = fp.replace("ID_Card_", "").replace(".png", "").split("_")
        
        # name _ mobile _ post
        if id_creator.format_phone_number(parts[3])[0]:
            # Name has middle name
            name = parts[0] + " " + parts[1] + " " + parts[2]
            mobile = parts[3]
            post = " ".join(parts[4:])
        else:
            # Name doesn't have middle name
            name = parts[0] + " " + parts[1]
            mobile = parts[2]
            post = " ".join(parts[3:])

        id_cards_df.append([idx, name, mobile, post, fp])

    return gr.update(maximum=len(id_cards_df)), id_cards_df


# Loads the face image from the specified ID card
def display_id_photo(filename: str):
    image_path = os.path.join(c.IMAGES_OUTPUT_PATH, filename)

    # Load image and crop the face section
    full_image = Image.open(image_path)
    face_image = full_image.crop(
        (
            c.PICTURE_POSITION[0],
            c.PICTURE_POSITION[1],
            c.PICTURE_POSITION[0] + c.PICTURE_SIZE[0],
            c.PICTURE_POSITION[1] + c.PICTURE_SIZE[1],
        )
    )

    return face_image


# Deletes the specified ID card file
def delete_id_card(sl_num: int, id_cards_df: list[list[int | str]]):
    # Extract the filename and remove the entry from the dataframe
    filename = id_cards_df[sl_num - 1][4]
    id_cards_df.pop(sl_num - 1)

    # Update the sl_num of the remaining entries
    for i in range(sl_num - 1, len(id_cards_df)):
        id_cards_df[i][0] -= 1

    file_path = os.path.join(c.IMAGES_OUTPUT_PATH, filename)

    # Delete the file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)
        return id_cards_df, f"Deleted {filename} successfully!"
    return id_cards_df, f"File {filename} does not exist."


def regenerate_all_id_cards():
    _, id_cards_df = get_id_card_details()

    def process_id_card(id_card: list[int | str]):
        image_path = os.path.join(c.IMAGES_OUTPUT_PATH, id_card[4])
        full_image = Image.open(image_path)
        face_image = full_image.crop(
            (
                c.PICTURE_POSITION[0],
                c.PICTURE_POSITION[1],
                c.PICTURE_POSITION[0] + c.PICTURE_SIZE[0],
                c.PICTURE_POSITION[1] + c.PICTURE_SIZE[1],
            )
        )

        id_creator.generate_id_card(
            face_image, 0.5, 1, True, id_card[1], id_card[2], id_card[3]
        )

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_id_card, id_card) for id_card in id_cards_df]
        # Wait for all tasks to complete
        for future in tqdm(futures, desc="Regenerating images", unit="image(s) "):
            future.result()

    return "All ID cards regenerated successfully!"


def get_filename_from_df(sl_num):
    return get_id_card_details()[1][sl_num - 1][4]


# * Gradio Interface
with gr.Blocks(title="ID Card Station") as demo:
    with gr.Tabs() as tabs:

        with gr.TabItem("Generate ID Card", id=0):
            gr.Markdown("# ID Card Generator 📇")

            with gr.Row():
                with gr.Column():
                    # Input for person's photo
                    person_image = gr.Image(
                        type="filepath",
                        label="Upload Photo with Face",
                        height=300,
                        show_fullscreen_button=False,
                    )

                    # Input fields for face detection
                    with gr.Row():
                        target_face_size = gr.Slider(
                            label="Target Face Size",
                            minimum=0.3,
                            maximum=0.7,
                            value=0.5,
                            step=0.05,
                        )
                        face_num = gr.Radio(
                            label="Face Number (higher = inaccurate)",
                            choices=[1, 2, 3],
                            value=1,
                        )
                        force_image = gr.Checkbox(
                            label="Force Image",
                            value=False,
                        )

                    # Input fields for details
                    name = gr.Textbox(label="Full Name", lines=1)
                    phone = gr.Textbox(
                        label="Phone Number (10 digits)", placeholder="# " * 10, lines=1
                    )
                    post = gr.Textbox(label="Post", value="Member", lines=1)

                    # Generate button
                    generate_button = gr.Button(
                        value="Generate ID Card",
                        variant="primary",
                        size="lg",
                    )

                # Output and status alerts
                with gr.Column():
                    result_image = gr.Image(
                        label="Generated ID Card",
                        height=600,
                        show_fullscreen_button=False,
                    )
                    alert = gr.Textbox(
                        placeholder="Current Status or Errors will be shown here.",
                        label="Status / Errors",
                        interactive=False,
                    )

                # Function to the id generator with initial checks
                def handle_generate(
                    person_image: gr.Image,
                    target_face_size: float,
                    face_num: int,
                    force_image: bool,
                    name: str,
                    phone: str,
                    post: str,
                ):

                    if person_image is None:
                        return None, "Please upload the person's photo."
                    elif name is None or phone is None or post is None:
                        return None, "Please fill in all the required fields."

                    output, message = id_creator.generate_id_card(
                        person_image,
                        target_face_size,
                        face_num,
                        force_image,
                        name,
                        phone,
                        post,
                    )
                    if output:
                        return output, message
                    else:
                        return None, message

                # Connect the function to the interface
                generate_button.click(
                    fn=handle_generate,
                    inputs=[
                        person_image,
                        target_face_size,
                        face_num,
                        force_image,
                        name,
                        phone,
                        post,
                    ],
                    outputs=[result_image, alert],
                )

        with gr.TabItem("ID Card List", id=1):
            with gr.Row():
                list_view = gr.DataFrame(
                    headers=["Sl No", "Name", "Mobile", "Post", "Filename"],
                    interactive=False,
                )

            # List View Section
            with gr.Row():
                with gr.Column():
                    refresh_button = gr.Button(
                        value="Refresh List", variant="secondary"
                    )
                    see_photo_button = gr.Button(value="See Photo", variant="secondary")
                with gr.Column():
                    id_num_selected = gr.Number(
                        label="Select ID of Entry to View / Delete / Edit",
                        value=1,
                        minimum=1,
                        maximum=len(get_id_card_details()[1]),
                        interactive=True,
                    )

            # Delete/Edit Buttons
            with gr.Row():
                with gr.Column():
                    photo_preview = gr.Image(
                        height=400, show_fullscreen_button=False, interactive=False
                    )
                with gr.Column():
                    edit_button = gr.Button(
                        value="Edit Selected as New", variant="primary"
                    )
                    delete_button = gr.Button(
                        value="Delete Selected from Saved", variant="stop"
                    )
                    alert2 = gr.Textbox(
                        placeholder="Current Status or Errors will be shown here.",
                        label="Status / Errors",
                        interactive=False,
                    )

            # Bind Functions
            refresh_button.click(
                fn=lambda: get_id_card_details(), outputs=[id_num_selected, list_view]
            )
            delete_button.click(
                fn=lambda sl_num: delete_id_card(sl_num, get_id_card_details()[1]),
                inputs=id_num_selected,
                outputs=[list_view, alert2],
            )
            see_photo_button.click(
                fn=lambda sl_num: display_id_photo(get_filename_from_df(sl_num)),
                inputs=id_num_selected,
                outputs=photo_preview,
            )

            def edit(sl_num):
                id_cards_df = get_id_card_details()[1]
                return (
                    *id_cards_df[sl_num - 1][1:4],
                    display_id_photo(get_filename_from_df(sl_num)),
                    gr.Tabs(selected=0),
                )

            edit_button.click(
                fn=edit,
                inputs=id_num_selected,
                outputs=[name, phone, post, person_image, tabs],
            )

        with gr.TabItem("ID Card PDF Printer", id=2):
            with gr.Column():
                regenerate_all_button = gr.Button(
                    value="Regenerate All ID Cards", variant="secondary"
                )
                print_button = gr.Button(
                    value="Print ID Cards to PDF", variant="primary"
                )
                status = gr.Textbox(
                    label="Status", value="Ready to Print", interactive=False, lines=1
                )
                download_btn = gr.DownloadButton(
                    label="Download PDF",
                    value=None,
                    variant="secondary",
                )

            regenerate_all_button.click(fn=regenerate_all_id_cards, outputs=status)
            download_btn.click(
                fn=lambda: gr.update(value=None, variant="secondary"),
                inputs=[],
                outputs=[download_btn],
            )

            print_button.click(
                fn=lambda: (
                    pdf_gen.render_pdf(),
                    gr.update(value=c.OUTPUT_PDF, variant="primary"),
                ),
                outputs=[status, download_btn],
            )


if __name__ == "__main__":
    print(" Ctrl+Click the URL: http://localhost:7860")
    
    _, local_url, _ = demo.launch(share=False, inbrowser=True, quiet=True, server_port=7860)

    print(" [!] Webserver is terminated.")

    sys.exit(0)
