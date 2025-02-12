import gradio as gr
from ai_core import AICore

class ChatInterface:
    def __init__(self, ai_core: AICore):
        self.ai = ai_core
        self._create_interface()

    def _create_interface(self):
        with gr.Blocks() as self.interface:
            gr.Markdown("## 🤖 Parviz Mind")
            self.chatbot = gr.Chatbot(label="💬 تاریخچه چت")
            self.query_input = gr.Textbox(label="❓ سوال خود را وارد کنید")
            self.submit_button = gr.Button("🚀 ارسال")

            self.submit_button.click(self.answer_question, inputs=self.query_input, outputs=self.chatbot)

    def answer_question(self, query):
        response = self.ai.answer_query(query)
        return response

    def launch(self):
        self.interface.launch()

if __name__ == "__main__":
    ai_core = AICore()
    chat_interface = ChatInterface(ai_core)
    chat_interface.launch()
