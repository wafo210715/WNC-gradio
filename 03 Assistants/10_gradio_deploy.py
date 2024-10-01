from openai import OpenAI
import shelve
import os
import time
import gradio as gr

client = OpenAI()


vs_id = "vs_Lt6boo0iCp1EB4dBemWMywub"
assistant_id = "asst_AztugG7hyt2Rm5RuF5Dp7S5V"


# retireve assistant and vector store and patch them together
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
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(user_id, None)


def store_thread(user_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[user_id] = thread_id


# run assistant
def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assistant_id)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    # Print out the messages object for inspection
    print("Messages object:")
    print(messages)

    # Get the latest message
    message = messages.data[0]

    # Extract text value and specific annotation details
    new_message = {"text": message.content[0].text.value, "annotations": []}

    for annotation in message.content[0].text.annotations:
        if hasattr(annotation, "file_citation"):
            new_message["annotations"].append(
                {
                    "file_id": annotation.file_citation.file_id,
                    "text": annotation.text,
                }
            )

    # Extract file IDs
    file_ids = set()
    for message in messages.data:
        if message.content and isinstance(message.content, list):
            for content_block in message.content:
                if hasattr(content_block, "text") and hasattr(
                    content_block.text, "annotations"
                ):
                    for annotation in content_block.text.annotations:
                        if hasattr(annotation, "file_citation") and hasattr(
                            annotation.file_citation, "file_id"
                        ):
                            file_ids.add(annotation.file_citation.file_id)
    file_ids = list(file_ids)

    # New code to retrieve filenames
    filenames = []
    for file_id in file_ids:
        file_info = client.files.retrieve(file_id)
        filenames.append(file_info.filename)

    return (
        new_message,
        file_ids,
        filenames,
        messages,
    )  # Add messages to the return values


# reply
def generate_response(message_body, user_id):
    # Check if there is already a thread_id for the user_id
    thread_id = check_if_thread_exists(user_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for user_id {user_id}")
        thread = client.beta.threads.create()
        store_thread(user_id, thread.id)
        thread_id = thread.id
    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for user_id {user_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add the user's message to the thread
    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=message_body
    )

    # Run the assistant and get the new message, file IDs, filenames, and messages
    new_message, file_ids, filenames, messages = run_assistant(thread)

    # Create a dictionary to map file_ids to filenames
    file_id_to_name = dict(zip(file_ids, filenames))

    # Format the response as a string
    response = f"Response: {new_message['text']}\n\n"
    if new_message["annotations"]:
        response += "Citations:\n"
        for annotation in new_message["annotations"]:
            file_id = annotation["file_id"]
            filename = file_id_to_name.get(file_id, "Unknown file")
            response += f"- {annotation['text']}: {filename} (ID: {file_id})\n"

    return response


# Assuming 'messages' is your SyncCursorPage[Message] object
# file_ids = extract_file_ids(messages)
# print("Extracted file IDs:")
# for file_id in file_ids:
#     print(file_id)


# new_message = generate_response("What is urban rainwater harvesting?", "123")


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
    title="AI Assistant",
    description="Ask a question and get a response from the AI assistant.",
)

# Launch the Gradio interface
iface.launch()

# Remove or comment out the test calls at the end of your script
# new_message = generate_response("What is urban rainwater harvesting?", "123")
# new_message = generate_response("What is indicator and pathogenic microorganisms concentrations found in untreated harvested rainwater?", "111")
# new_message = generate_response("What was my first question?", "123")
