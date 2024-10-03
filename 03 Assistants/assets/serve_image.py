import gradio as gr
from flask import Flask, send_from_directory
import threading

app = Flask(__name__)

# Route to serve the image
@app.route('/assets/Governance_Right.jpg')
def serve_image():
    return send_from_directory('C:\\llm\\openai-python-tutorial\\03 Assistants\\assets', 'Governance_Right.jpg')

css = """
body {
    background-image: url('http://127.0.0.1:5000/assets/Governance_Right.jpg');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center center;
    min-height: 1400px;
}
"""

def greet(name):
    return f"Hello {name}!"

def run_flask():
    app.run(port=5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    with gr.Blocks(css=css) as demo:
        name_input = gr.Textbox(label="Enter your name")
        greet_button = gr.Button("Greet")
        output = gr.Textbox(label="Greeting")
        greet_button.click(fn=greet, inputs=name_input, outputs=output)

    demo.launch(server_name="0.0.0.0", server_port=8080, share=True)
