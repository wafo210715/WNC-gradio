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

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {user_id}:", new_message)

    # Record the conversation in a text file
    record_conversation(thread_id, user_id, message_body, new_message)

    return new_message


def record_conversation(thread_id, user_id, user_message, assistant_response):
    # Retrieve the full conversation history from the thread
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    conversation_history = []
    for msg in reversed(messages.data):
        role = msg.role
        content = msg.content[0].text.value
        timestamp = msg.created_at
        conversation_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.fromtimestamp(timestamp).isoformat(),
            }
        )

    # Create a record of the conversation
    conversation_record = {
        "thread_id": thread_id,
        "user_id": user_id,
        "conversation_history": conversation_history,
        "recorded_at": datetime.datetime.now().isoformat(),
    }

    # Write the conversation record to a text file
    with open("conversation_records.txt", "a") as f:
        f.write(json.dumps(conversation_record) + "\n")


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
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


def chat_interface(message, state):
    user_id = "gradio_user"  # We'll use a fixed user ID for simplicity
    response = generate_response(message, user_id)
    state.append((message, response))
    return state, state


# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown(
        """
        # AI Assistant Chat
        Welcome to the AI Assistant Chat interface!
        """
    )
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Type your message here")
    clear = gr.Button("Clear")

    msg.submit(chat_interface, [msg, chatbot], [chatbot, chatbot]).then(
        lambda: "", None, msg
    )
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()

# Comment out or remove the following lines:
# new_message = generate_response("What is urban rainwater harvesting?", "123")
# new_message = generate_response(
#     "What is indicator and pathogenic microorganisms concentrations found in untreated harvested rainwater?",
#     "123",
# )
# new_message = generate_response("What was my first question?", "123")


def record_conversation(thread_id, user_id, user_message, assistant_response):
    # Retrieve the full conversation history from the thread
    messages = client.beta.threads.messages.list(thread_id=thread_id)

    conversation_history = []
    for msg in reversed(messages.data):
        role = msg.role
        content = msg.content[0].text.value
        timestamp = msg.created_at
        conversation_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.fromtimestamp(timestamp).isoformat(),
            }
        )

    # Create a record of the conversation
    conversation_record = {
        "thread_id": thread_id,
        "user_id": user_id,
        "conversation_history": conversation_history,
        "recorded_at": datetime.datetime.now().isoformat(),
    }

    # Write the conversation record to a text file
    with open("conversation_records.txt", "a") as f:
        f.write(json.dumps(conversation_record) + "\n")
