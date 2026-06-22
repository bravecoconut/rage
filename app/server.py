# app/run.py

'''
it handles all the stages work flows
'''
from stage_1.stage_1_man import start_stage_1
from stage_2.stage_2_man import start_stage_2
from stage_3.stage_3_man import start_stage_3
from stage_4.stage_4_man import start_stage_4
from stage_5.stage_5_man import start_stage_5
from stage_6.stage_6_man import start_stage_6
from stage_7.stage_7_man import start_stage_7

import json

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response,
    stream_with_context,
    redirect,
    url_for,
    send_from_directory
)
from flask_cors import CORS

import os


def _is_stage_error(result):
    return result is None or (isinstance(result, dict) and result.get('error'))


def _error_status_payload(result, fallback_message):
    if result is None:
        return {"error_status": fallback_message}
    if isinstance(result, dict) and result.get('error'):
        err = result['error']
        return {"error_status": str(err) if not isinstance(err, str) else err}
    return {"error_status": fallback_message}


def _yield_stage_error(result, fallback_message):
    payload = _error_status_payload(result, fallback_message)
    data_string = f"data: {json.dumps(payload)}\n\n"
    yield data_string.encode("utf-8")
    yield b""  # flush trigger


app = Flask(__name__)
CORS(app)


@app.route("/noname")
def noname():                          # ✅ this is missing
    return render_template("index.html")


@app.route("/")
def root():
    return redirect(url_for('noname'))


@app.route("/start", methods=["POST"])
def start():

    def generate():
        payload = None

        payload = {"starting_status": {"stage_1": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        searched_topics = start_stage_1()

        if _is_stage_error(searched_topics) or searched_topics == []:
            yield from _yield_stage_error(
                searched_topics,
                "Failed to fetch topics",
            )
            print("error from stage1")
            return


        payload = {"starting_status": {"stage_2": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        chosen_topic_index = start_stage_2(searched_topics)

        if _is_stage_error(chosen_topic_index):
            yield from _yield_stage_error(
                chosen_topic_index,
                "Failed to choose topic",
            )
            print("error from stage2")
            return

        chosen_topic_text = searched_topics[chosen_topic_index]['topic']
        chosen_topic_text = chosen_topic_text.replace('"', "'")


        payload = {"starting_status": {"stage_3": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        research_data = start_stage_3(chosen_topic_text)

        if _is_stage_error(research_data):
            yield from _yield_stage_error(
                research_data,
                "Failed to research topic",
            )
            print("error from stage3")
            return
        
        payload = {"starting_status": {"stage_4": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        meme_text = start_stage_4(research_data, chosen_topic_text)

        if _is_stage_error(meme_text):
            yield from _yield_stage_error(
                meme_text,
                "Failed to generate meme text",
            )
            print("error from stage4")
            return

        payload = {"starting_status": {"stage_5": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        meme_image_id = start_stage_5(research_data, meme_text, chosen_topic_text)

        if _is_stage_error(meme_image_id):
            yield from _yield_stage_error(
                meme_image_id,
                "Failed to generate meme image",
            )
            print("error from stage5")
            return

        payload = {"starting_status": {"stage_6": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        image_id = start_stage_6(meme_image_id, chosen_topic_text)

        if _is_stage_error(image_id):
            yield from _yield_stage_error(
                image_id,
                "Failed to edit meme image",
            )
            print("error from stage6")
            return

        payload = {"starting_status": {"stage_7": True}}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 
        new_post = start_stage_7(chosen_topic_text, research_data, image_id, meme_image_id)

        if _is_stage_error(new_post):
            yield from _yield_stage_error(
                new_post,
                "Failed to create post",
            )
            print("error from stage7")
            return
        
        payload = {"new_post": json.loads(new_post) if isinstance(new_post, str) else new_post}
        data_string = f"data: {json.dumps(payload)}\n\n"
        yield data_string.encode("utf-8") 

        with open("r.md", "w") as file:
            file.write(f"""# choosen topic\n{chosen_topic_text}\n---\n# research data\n{research_data}\n---\n# meme text\n{meme_text}\n---\n# meme image\n![meme]({image_id})\n\n""")
        
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/get_all_posts", methods=["POST"])
def get_all_posts():
    with open("data/post/post.json") as file:
        return Response(file.read(), mimetype="application/json")
    

@app.route("/results_images/<filename>")
def results_images(filename):
    folder = os.path.abspath("data/results_images")
    print(f"Looking in: {folder}")  # check this in terminal
    return send_from_directory(folder, filename)

@app.route("/poster_images/<filename>")
def poster_images(filename):
    folder = os.path.abspath("data/images")
    print(f"Looking in: {folder}")  # check this in terminal
    return send_from_directory(folder, filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
