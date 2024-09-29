from openai import OpenAI
import shelve

client = OpenAI()


def check_if_thread_exists(user_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(user_id, None)


def get_chat_history(user_id):
    thread_id = check_if_thread_exists(user_id)
    if thread_id is None:
        return f"No chat history found for user {user_id}."

    messages = client.beta.threads.messages.list(thread_id=thread_id)

    chat_history = [f"Chat history for user {user_id}:"]
    for message in reversed(messages.data):
        role = message.role
        content = message.content[0].text.value
        chat_history.append(f"{role.capitalize()}: {content}")

    return "\n\n".join(chat_history)


def write_all_histories_to_file(output_file):
    with shelve.open("threads_db") as threads_shelf:
        with open(output_file, "w", encoding="utf-8") as f:
            for user_id in threads_shelf.keys():
                history = get_chat_history(user_id)
                f.write(history)
                f.write("\n\n" + "=" * 50 + "\n\n")  # Separator between user histories


if __name__ == "__main__":
    output_file = "chat_histories.txt"
    write_all_histories_to_file(output_file)
    print(f"All chat histories have been written to {output_file}")
