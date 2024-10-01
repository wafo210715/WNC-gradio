from openai import OpenAI
import shelve
import os
import time
import gradio as gr
import json
import csv
from datetime import datetime

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

    # Record the conversation (without feedback for now)
    record_conversation_and_feedback(thread_id, user_id, message_body, response)

    return response, thread_id  # Return thread_id as well


def record_conversation_and_feedback(
    thread_id, user_id, user_message, assistant_response, feedback=None
):
    filename = "conversation_records.csv"

    # Create the CSV file with headers if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "Thread ID",
                    "User ID",
                    "User Message",
                    "Assistant Response",
                    "Feedback",
                ]
            )

    # Append the new record
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.now().isoformat(),
                thread_id,
                user_id,
                user_message,
                assistant_response,
                feedback,
            ]
        )


# Gradio interface function
def gradio_interface(message, user_id):
    response, thread_id = generate_response(message, user_id)
    return response, thread_id


# List of image paths
image_paths = [
    "./03 Assistants/assets/Day event_Festivalof research.jpg",
    "./03 Assistants/assets/Governance_Right.jpg",
    "./03 Assistants/assets/Layout64.jpg",
    "./03 Assistants/assets/Waste WaterTreatment.png",
    "./03 Assistants/assets/wastewater catchment.png",
    "./03 Assistants/assets/water quality.png",
    "./03 Assistants/assets/wwtw.png",
    # Add more image paths as needed
]


def change_image(index, direction):
    new_index = (int(index) + direction) % len(image_paths)
    return image_paths[new_index], new_index


def save_feedback(message, response, feedback):
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "response": response,
        "feedback": feedback,
    }
    os.makedirs("feedback", exist_ok=True)
    with open(
        f"feedback/feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w"
    ) as f:
        json.dump(feedback_data, f, indent=2)
    return "Feedback saved. Thank you!"


# Create Gradio interface
with gr.Blocks(
    css="""
    body { display: flex; flex-direction: column; min-height: 100vh; }
    #content { flex-grow: 1; }
    #image-container { 
        position: relative; 
        width: 100%; 
        max-width: 1000px; 
        margin: 20px auto 0; 
    }
    #image-display {
        width: 100%;
        height: auto;
        display: block;
    }
    .side-button { 
        position: absolute; 
        top: 50%; 
        transform: translateY(-50%);
        z-index: 1;
        background: rgba(255,255,255,0.7);  /* 70% opaque white */
        border: none;
        padding: 10px;
        font-size: 20px;
        cursor: pointer;
    }
    .prev-button { left: 10px; }
    .next-button { right: 10px; }
    .side-button:hover {
        background: rgba(255,255,255,0.9);  /* 90% opaque white on hover */
    }
"""
) as demo:
    with gr.Column(elem_id="content"):
        gr.Markdown("# Welcome to Chichester's Festival of Research")

        # Instead of iface.render(), include the components directly:
        message = gr.Textbox(lines=2, placeholder="Enter your message here...")
        user_id = gr.Textbox(placeholder="Enter user ID (e.g., 123)")
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="AI Response", lines=10)

        # Add feedback options
        feedback = gr.Radio(
            [
                "Correct and Helpful",
                "Learned Something New",
                "Needs Improvement",
                "Inappropriate",
            ],
            label="Provide Feedback",
        )
        feedback_btn = gr.Button("Submit Feedback")
        feedback_result = gr.Textbox(label="Feedback Result")

        # Connect the submit button to your gradio_interface function
        submit_btn.click(
            gradio_interface, inputs=[message, user_id], outputs=[output, gr.State()]
        )

        # Connect feedback submission
        feedback_btn.click(
            lambda m, r, t, u, f: record_conversation_and_feedback(t, u, m, r, f)
            or "Feedback saved. Thank you!",
            inputs=[message, output, gr.State(), user_id, feedback],
            outputs=feedback_result,
        )

        # Add some spacing
        gr.Markdown("<br><br>")

    # Image gallery at the bottom
    with gr.Row(elem_id="image-container"):
        prev_button = gr.Button("◀", elem_classes="side-button prev-button")
        image = gr.Image(
            image_paths[0],
            elem_id="image-display",
            label="Event Images",
            show_label=False,
            show_download_button=False,
        )
        next_button = gr.Button("▶", elem_classes="side-button next-button")

    # Image navigation logic
    index = gr.State(0)

    prev_button.click(
        lambda x: change_image(x, -1), inputs=[index], outputs=[image, index]
    )
    next_button.click(
        lambda x: change_image(x, 1), inputs=[index], outputs=[image, index]
    )

# Launch the Gradio interface
demo.launch()
