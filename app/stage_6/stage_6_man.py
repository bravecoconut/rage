# app/stage_6/stage_6_man.py

"""Stage 6 orchestrator — composes the final post image with caption overlay."""

from app.stage_6.edit_image.edit import add_meme_text


def start_stage_6(image_id, text):
    """Run Stage 6: render caption text onto the generated background image."""
    print("stage 6")

    image_path = add_meme_text(image_id=image_id, text=text)

    return image_path

    

