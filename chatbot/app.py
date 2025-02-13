import gradio as gr
from ai_core import AICore

class ChatInterface:
    def __init__(self, ai_core: AICore):
        self.ai = ai_core
        self._create_interface()
    def _create_interface(self):
        with gr.Blocks() as self.interface:
            gr.Markdown("## 🤖 Parviz Mind")
            gr.Markdown("**یک فایل (PDF یا TXT) آپلود کنید و سوال خود را بپرسید.**")
            self.chatbot = gr.Chatbot(label="💬 تاریخچه چت")
            self.query_input = gr.Textbox(label="❓ سوال خود را وارد کنید")
            self.summarize_checkbox = gr.Checkbox(label="📌 خلاصه‌ساز را فعال کن")
            self.submit_button = gr.Button("🚀 ارسال")
            self.del_button = gr.Button("🗑 پاک کردن حافظه")
            self.file_input = gr.File(label="📂 آپلود فایل", file_types=[".pdf", ".txt"])
            with gr.Accordion("خلاصه چت", open=False):
                with gr.Row():
                    self.summary_output = gr.Textbox(label="📌 خلاصه مکالمه", interactive=False)
            with gr.Accordion("تنظیمات پیشرفته", open=False):
                with gr.Row():
                    self.model_dropdown = gr.Dropdown(label="🔍 انتخاب مدل", choices=self.ai.models, value=self.ai.default_model)
                    self.tone_dropdown = gr.Dropdown(label="🎭 لحن پاسخ", choices=["رسمی", "محاوره‌ای", "علمی", "طنزآمیز"], value="رسمی")
                    self.language_dropdown = gr.Dropdown(label="🌐 زبان چت بات", choices=["فارسی", "انگلیسی", "عربی"], value="فارسی")
                    self.token_count = gr.Textbox(label="🔢 تعداد توکن‌ها", interactive=False)
                    self.token_price = gr.Textbox(label="💰 هزینه تخمینی", interactive=False)
                with gr.Row():
                    self.creativity_slider = gr.Slider(label="🎨 خلاقیت (Temperature)", minimum=0.0, maximum=1.0, step=0.1, value=0.7)
                    self.response_length_dropdown = gr.Dropdown(label="📏 طول پاسخ", choices=["کوتاه", "بلند"], value="بلند")
                self.keywords_input = gr.Textbox(label="🔑 کلمات کلیدی (اختیاری)")
                self.welcome_message_input = gr.Textbox(label="👋 پیام خوش آمدگویی (اختیاری)")
                self.exclusion_words_input = gr.Textbox(label="🚫 کلمات استثنا (اختیاری)")
            self.del_button.click(
                self.clear_chat,
                inputs=[],
                outputs=[self.chatbot, self.summary_output, self.token_count, self.token_price]
            )
            self.submit_button.click(
                self.process_chat,
                inputs=[
                    self.query_input, self.file_input, self.summarize_checkbox,
                    self.tone_dropdown, self.model_dropdown, self.creativity_slider,
                    self.keywords_input, self.language_dropdown, self.response_length_dropdown,
                    self.welcome_message_input, self.exclusion_words_input
                ],
                outputs=[self.chatbot, self.summary_output, self.token_count, self.token_price]
            )
            self.query_input.submit(
                self.process_chat,
                inputs=[
                    self.query_input, self.file_input, self.summarize_checkbox,
                    self.tone_dropdown, self.model_dropdown, self.creativity_slider,
                    self.keywords_input, self.language_dropdown, self.response_length_dropdown,
                    self.welcome_message_input, self.exclusion_words_input
                ],
                outputs=[self.chatbot, self.summary_output, self.token_count, self.token_price]
            )
    def process_chat(self, query, file_obj, summarize, tone, model_name, creativity,
                     keywords, language, response_length, welcome_message, exclusion_words):
        response, summary, total_tokens, price = self.ai.answer_query(
            query, file_obj, summarize, tone, model_name, creativity,
            keywords, language, response_length, welcome_message, exclusion_words
        )
        return self.ai.chat_history, summary, total_tokens, price
    def clear_chat(self):
        self.ai.clear_history()
        return self.ai.chat_history, "", 0, "0 دلار"
    def launch(self):
        self.interface.launch(share=True)

if __name__ == "__main__":
    ai_core = AICore()
    chat_app = ChatInterface(ai_core)
    chat_app.launch()
