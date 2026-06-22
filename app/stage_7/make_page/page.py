"""Persist a completed post entry to the content library JSON store."""

import json

def make_post_page(chosen_topic, research_data, image_path, poster):
    """Append a new post object to `data/post/post.json` and return it."""
    error = {'error': None}

    try:
        with open("data/post/post.json", "r") as file:
            current_posts = json.load(file)

        new_post = {
            "topic":chosen_topic,
            "description": research_data,
            "image_path": image_path,
            "poster": poster
        }

        current_posts.append(new_post)

        with open("data/post/post.json", "w") as file:
            current_posts = json.dump(current_posts, file)

        return new_post

    except Exception as e:
        error['error'] = e 
        return error
        