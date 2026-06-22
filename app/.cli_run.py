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

import os

def start():
    searched_topics = start_stage_1()

    chosen_topic_index = start_stage_2(searched_topics)
    chosen_topic_text = searched_topics[chosen_topic_index]['topic']

    research_data = start_stage_3(chosen_topic_text)
    
    meme_text = start_stage_4(research_data, chosen_topic_text)

    meme_image_id = start_stage_5(research_data=research_data, meme_text=meme_text, chosen_topic=chosen_topic_text)

    image_path = start_stage_6(meme_image_id, chosen_topic_text)

    absolute_image_path = os.path.abspath(image_path)

    new_post = start_stage_7(chosen_topic_text, research_data, absolute_image_path)


    with open("r.md", "w") as file:
        file.write(f"""# choosen topic\n{chosen_topic_text}\n---\n# research data\n{research_data}\n---\n# meme text\n{meme_text}\n---\n# meme image\n![meme]({image_path})\n\n---\n# post_path\n{new_post}\n""")

        

start()