from openai import OpenAI
import shelve
import os
import time
import gradio as gr
import json
import datetime

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
def check_if_thread_exists(user_id):
    try:
        with shelve.open("threads_db") as threads_shelf:
            return threads_shelf.get(user_id, None)
    except (shelve.error, OSError) as e:
        print(f"Error accessing threads_db: {e}")
        return None


def store_thread(user_id, thread_id):
    try:
        with shelve.open("threads_db", writeback=True) as threads_shelf:
            threads_shelf[user_id] = thread_id
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

    # Record the conversation
    record_conversation(thread_id, user_id, message_body, response)

    return response


def record_conversation(thread_id, user_id, user_message, assistant_response):
    # Create a record of the conversation
    conversation_record = {
        "thread_id": thread_id,
        "user_id": user_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "recorded_at": datetime.datetime.now().isoformat(),
    }

    # Write the conversation record to a JSON file
    filename = "conversation_records.json"

    try:
        # Try to read existing records
        with open(filename, "r") as f:
            records = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty/invalid, start with an empty list
        records = []

    # Append the new record
    records.append(conversation_record)

    # Write all records back to the file
    with open(filename, "w") as f:
        json.dump(records, f, indent=2)


# Gradio interface function
def gradio_interface(message, user_id):
    return generate_response(message, user_id)


# Create Gradio interface
iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your message here..."),
        gr.Textbox(placeholder="Enter user ID (e.g., 123)"),
    ],
    outputs="text",
    # title="AI Assistant",
    description="Ask a question and get a response from the AI assistant.",
    examples=[["Hello, how are you?", "user123"]],
)

# List of image paths
image_paths = [
    "./03 Assistants/assets/Day event_Festivalof research.jpg",
    "./03 Assistants/assets/image2.jpg",
    "./03 Assistants/assets/image3.jpg",
    # Add more image paths as needed
]


def change_image(index, direction):
    new_index = (index + direction) % len(image_paths)
    return image_paths[new_index], new_index


with gr.Blocks() as demo:
    gr.Markdown("# Welcome to Chichester's Festival of Research")

    with gr.Row():
        with gr.Column(scale=1):
            prev_button = gr.Button("Previous")
        with gr.Column(scale=50):
            image = gr.Image(
                image_paths[0],
                label="Event Images",
                height=448,
                width=1463,
                show_download_button=False,
            )
        with gr.Column(scale=1):
            next_button = gr.Button("Next")

    index = gr.State(0)

    prev_button.click(
        change_image,
        inputs=[index, gr.Number(-1, visible=False)],
        outputs=[image, index],
    )
    next_button.click(
        change_image,
        inputs=[index, gr.Number(1, visible=False)],
        outputs=[image, index],
    )

    iface.render()

# Launch the Gradio interface
demo.launch()
