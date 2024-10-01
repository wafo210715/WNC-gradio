from openai import OpenAI
import shelve
import os
import time

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


# reply
def generate_response(message_body, user_id):
    # Check if there is already a thread_id for the wa_id
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

    # Run the assistant and get the new message, file IDs, and filenames
    new_message, file_ids, filenames = run_assistant(thread)
    print(f"To {user_id}:", new_message)

    print("\nExtracted file IDs and filenames:")
    for file_id, filename in zip(file_ids, filenames):
        print(f"File ID: {file_id}, Filename: {filename}")

    return new_message


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

    # Get the latest message
    message = messages.data[0]
    new_message = message.content[0].text.value

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

    return new_message, file_ids, filenames


# Assuming 'messages' is your SyncCursorPage[Message] object
# file_ids = extract_file_ids(messages)
# print("Extracted file IDs:")
# for file_id in file_ids:
#     print(file_id)


# new_message = generate_response("What is urban rainwater harvesting?", "123")

new_message = generate_response(
    "What is indicator and pathogenic microorganisms concentrations found in untreated harvested rainwater?",
    "456",
)

# new_message = generate_response("What was my first question?", "123")
