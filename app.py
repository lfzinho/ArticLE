import gradio as gr
import pandas as pd
from llm_model import LLMModel
from search_engine import SearchEngine

DATA_DIR = "./data/"
DATA_FILES = ["arxiv-metadata-oai-snapshot.json"]
SPLIT_SIZE_LIMIT = 100


search_engine = SearchEngine()
search_engine.feed_json(DATA_DIR, DATA_FILES, SPLIT_SIZE_LIMIT)
model = LLMModel()


def run_query(query, response_type):
    docs = search_engine.search(query)
    response = model.generate_response(query, docs, response_type)
    return response


with gr.Blocks() as app:
    gr.Image(
        'articLE.png', 
        width=200,
        show_label=False, 
        show_download_button=False
    )
    query = gr.Textbox(
        label="Question", 
        placeholder="What is the meaning of life?"
    )
    with gr.Row():
        response_type = gr.Dropdown(
            label="Response Type",
            choices=['Informative Summary', 'Explain the Reasoning', 'Just Show the Results'],
            value='Informative Summary',
            interactive=True
        )
        gen_button = gr.Button(value="Generate")
    result = gr.Markdown(
        value="# Result *(Informative Summary)*\nThe Meaning of life is..."
    )
    gen_button.click(run_query, [query, response_type], result)


app.launch()
