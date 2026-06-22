# app/stage_7/stage_7_man.py

"""Stage 7 orchestrator — publishes the finished post to the content library."""

from app.stage_7.make_page.page import make_post_page


def start_stage_7(chosen_topic, research_data, image_path, poster):
    """Run Stage 7: assemble and persist the post record for the web UI."""
    print("stage 7")

    new_post = make_post_page(chosen_topic, research_data, image_path, poster)

    return new_post

    

