from openai import OpenAI

client = OpenAI()
vs_id = "vs_Lt6boo0iCp1EB4dBemWMywub"
assistant_id = "asst_AztugG7hyt2Rm5RuF5Dp7S5V"

assistant = client.beta.assistants.retrieve(assistant_id)
vector_store = client.beta.vector_stores.retrieve(vs_id)

assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# Create a thread and attach the file to the message
# what are the indicator and pathogenic microorganisms concentrations found in untreated harvested rainwater.
# what is urban rainwater harversting?
thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "what are the indicator and pathogenic microorganisms concentrations found in untreated harvested rainwater.",
        }
    ]
)

run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)


# run in stream
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI

client = OpenAI()


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    @override
    def on_message_done(self, message) -> None:
        # print a citation to the file searched
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(
                annotation.text, f"[{index}]"
            )
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")

        print(message_content.value)
        print("\n".join(citations))


# Then, we use the stream SDK helper
# with the EventHandler class to create the Run
# and stream the response.

with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="answer questions in 50 words.",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()
