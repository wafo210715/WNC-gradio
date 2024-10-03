from openai import OpenAI
import shelve
import os
import time
import gradio as gr
from flask import Flask, send_from_directory
import threading

client = OpenAI()

vs_id = "vs_Lt6boo0iCp1EB4dBemWMywub"
assistant_id = "asst_AztugG7hyt2Rm5RuF5Dp7S5V"


def patch(assistant_id, vs_id):
    assistant = client.beta.assistants.retrieve(assistant_id)
    vector_store = client.beta.vector_stores.retrieve(vs_id)

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    return assistant


assistant = patch(assistant_id, vs_id)


# thread id documentation
def generate_user_id():
    if not hasattr(generate_user_id, "current_id"):
        generate_user_id.current_id = 99
    generate_user_id.current_id += 1
    return str(generate_user_id.current_id)

# New function to get the current user ID or generate a new one if it doesn't exist
def get_or_generate_user_id():
    if not hasattr(generate_user_id, "current_id"):
        return generate_user_id()
    return str(generate_user_id.current_id)

def check_if_thread_exists(user_id):
    try:
        with shelve.open("threads_db") as threads_shelf:
            return threads_shelf.get(str(user_id), None)
    except (shelve.error, OSError) as e:
        print(f"Error accessing threads_db: {e}")
        return None


def store_thread(user_id, thread_id):
    try:
        with shelve.open("threads_db", writeback=True) as threads_shelf:
            threads_shelf[str(user_id)] = thread_id
    except (shelve.error, OSError) as e:
        print(f"Error storing thread in threads_db: {e}")


def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assistant_id)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    messages = client.beta.threads.messages.list(thread_id=thread.id)

    message_data = messages.data[0]

    annotated_content = {"text": message_data.content[0].text.value, "annotations": []}

    for annotation in message_data.content[0].text.annotations:
        if hasattr(annotation, "file_citation"):
            annotated_content["annotations"].append(
                {
                    "file_id": annotation.file_citation.file_id,
                    "text": annotation.text,
                }
            )

    file_ids = set()
    for message_data in messages.data:
        if message_data.content and isinstance(message_data.content, list):
            for content_block in message_data.content:
                if hasattr(content_block, "text") and hasattr(
                    content_block.text, "annotations"
                ):
                    for annotation in content_block.text.annotations:
                        if hasattr(annotation, "file_citation") and hasattr(
                            annotation.file_citation, "file_id"
                        ):
                            file_ids.add(annotation.file_citation.file_id)
    file_ids = list(file_ids)

    filenames = []
    for file_id in file_ids:
        file_info = client.files.retrieve(file_id)
        filenames.append(file_info.filename)

    return (annotated_content, file_ids, filenames)


def generate_response(message_body, user_id):
    thread_id = check_if_thread_exists(user_id)
    if thread_id is None:
        print(f"Creating new thread for user_id {user_id}")
        thread = client.beta.threads.create()
        store_thread(user_id, thread.id)
        thread_id = thread.id

    else:
        print(f"Retrieving existing thread for user_id {user_id}")
        thread = client.beta.threads.retrieve(thread_id)

    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=message_body
    )

    annotated_content, file_ids, filenames = run_assistant(thread)

    file_id_to_name = dict(zip(file_ids, filenames))

    response = f"Response: {annotated_content['text']}\n\n"
    if annotated_content["annotations"]:
        response += "Citations:\n"
        for annotation in annotated_content["annotations"]:
            file_id = annotation["file_id"]
            filename = file_id_to_name.get(file_id, "Unknown file")
            response += f"- {annotation['text']}: {filename} (ID: {file_id})\n"

    return response


# Gradio interface function
def gradio_interface(message):
    user_id = get_or_generate_user_id()
    return generate_response(message, user_id)


# Replace the gr.Interface with gr.Blocks
with gr.Blocks(css="""
    .gradio-container {
        background-image: url('https://live.staticflickr.com/65535/54039115167_1ef0b63664_o.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center center;
    }
    #component-0 {
        background-color: transparent;
        min-height: 100vh;
    }
    .left-column, .middle-column, .right-column {
        background-color: rgba(255, 255, 255, 0.0);
        border-radius: 10px;
        padding: 20px;
        box-sizing: border-box;
    }
    .left-column {
        display: flex !important;
        flex-direction: column !important;
    }
    .left-column > * {
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    .middle-column {
        background-color: transparent !important;
    }
    .right-column {
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        height: 100vh !important;
    }
    .output-box {
        margin-top: auto;
    }
""") as demo:
    with gr.Row():
        with gr.Column(scale=45, elem_classes="left-column"):
            gr.Markdown("# Chichester's Festival of Research")
            gr.Markdown("Ask a question and get a response from the AI assistant.")
            user_id_button = gr.Button("Generate User ID")
            message_input = gr.Textbox(container=False, lines=4, placeholder="Enter your message here...")
            submit_button = gr.Button("Submit")
        
        with gr.Column(scale=80, elem_classes="middle-column"):
            # This column stays empty and transparent
            pass
        
        with gr.Column(scale=40, elem_classes="right-column"):
            gr.Markdown("## See the answer to your question below!")
            output = gr.Textbox(container=False, lines=30, elem_classes="output-box", placeholder="See Results here...")

    user_id_button.click(fn=lambda: f"Generated User ID: {generate_user_id()}", inputs=[], outputs=[output])
    submit_button.click(fn=gradio_interface, inputs=[message_input], outputs=[output])

# Launch the Gradio interface
demo.launch()


