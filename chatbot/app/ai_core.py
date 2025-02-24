import os
import re
from pypdf import PdfReader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
os.environ['hf_token'] = "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"

class AICore:
    def __init__(self, db_manager, model_name):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = Chroma(embedding_function=self.embeddings)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.chat_history = []
        self.price_per_token = 0.00001
        self.api_key = "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"
        self.model = ChatGroq(api_key=self.api_key, model_name=model_name)
        self.db = db_manager

    def _init_model(self, model_name):
        if self.model.model_name != model_name:
            from langchain_groq import ChatGroq
            self.model = ChatGroq(api_key=self.api_key, model_name=model_name)

    def summarize_chat(self):
        chat_text = "\n".join([f"پرسش: {q}\nپاسخ: {a}" for q, a in self.chat_history])
        summary_prompt = f"یک خلاصه کوتاه از مکالمه زیر ارائه کن:\n\n{chat_text}\n\nخلاصه:"
        summary_response = self.model.invoke(summary_prompt)
        return summary_response.content

    def process_file(self, file_obj):
        if not file_obj:
            return None
        file_path = file_obj.name if hasattr(file_obj, "name") else file_obj
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".pdf":
            reader = PdfReader(file_path)
            file_text = "\n".join(page.extract_text() for page in reader.pages)
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                file_text = f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        file_docs = [Document(page_content=file_text, metadata={"source": "uploaded_file"})]
        file_splits = self.text_splitter.split_documents(file_docs)
        self.vector_store.add_documents(file_splits)
        return file_text

    def count_tokens(self, text):
        return len(text.split())

    def calculate_price(self, input_text, output_text):
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        total_price = total_tokens * self.price_per_token
        return total_tokens, f"{total_price:.6f} هزار تومان"

    def remove_think_sections(self, response_text):
        return re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    def filter_to_persian(self, text):
        return re.sub(r'[^\u0600-\u06FF\s\.,؛؟!٪،0-9]', '', text)

    def answer_query(self, user_id, query, file_obj, summarize, tone, model_name, creativity,
                     keywords, language, response_length, welcome_message, exclusion_words, main_prompt, chatbot_name):
        self._init_model(model_name)
        if not chatbot_name or chatbot_name.strip() == "":
            chatbot_name = "Solving Center ChatBot"
        if file_obj:
            self.process_file(file_obj)
        search_query = f"{keywords} {query}" if keywords else query
        retrieved_docs = self.vector_store.similarity_search(search_query, k=3)
        knowledge = "\n\n".join(doc.page_content for doc in retrieved_docs)
        tone_prompts = {
            "رسمی": "پاسخ را با لحنی رسمی و مودبانه ارائه کن.",
            "محاوره‌ای": "پاسخ را به صورت دوستانه ارائه کن.",
            "علمی": "پاسخ را با استدلال‌های منطقی ارائه کن.",
            "طنزآمیز": "پاسخ را با لحنی طنزآمیز ارائه کن.",
        }
        tone_instruction = tone_prompts.get(tone, f"پاسخ را به زبان {language} ارائه کن.")
        language_instruction = (f"پاسخ را فقط به زبان {language} ارائه کن و از زبان دیگری استفاده نکن مگر آنکه بخواهی کد بنویسی "
                                f"که در آن صورت فقط از زبان انگلیسی استفاده کن مگر اینکه کاربر از تو درخواست کند از زبان دیگری استفاده بکنی و از زبان چینی استفاده نکن.") if language else ""
        if response_length == "کوتاه":
            length_instruction = "پاسخ را به صورت مختصر ارائه کن."
        elif response_length == "بلند":
            length_instruction = "پاسخ را به صورت مفصل و جامع ارائه کن."
        else:
            length_instruction = ""
        exclusion_instruction = f"از کلمات زیر در پاسخ استفاده نکن: {exclusion_words}" if exclusion_words else ""
        the_prompt = f"شما {chatbot_name} یک دستیار هوش مصنوعی هستید :{main_prompt}" if main_prompt else f"شما {chatbot_name} هستید، یک دستیار هوش مصنوعی ساخته شده توسط امیرمهدی پرویز دانشجو دانشگاه صنعتی کرمانشاه "
        prompt = f"{the_prompt}{tone_instruction} {language_instruction} {length_instruction} {exclusion_instruction}\n\n"
        if welcome_message and not self.chat_history:
            prompt = f"{welcome_message}\n\n" + prompt
        if self.chat_history:
            conversation_history = "\n".join([f"پرسش: {q}\nپاسخ: {a}" for q, a in self.chat_history])
            prompt = f"{conversation_history}\n\n" + prompt
        prompt += f"اطلاعات مرتبط:\n{knowledge}\n\nسوال: {query}\nپاسخ:"
        response = self.model.invoke(prompt, temperature=creativity)
        cleaned_response = self.remove_think_sections(response.content)
        if language == 'فارسی':
            cleaned_response = self.filter_to_persian(cleaned_response)
            self.chat_history.append((query, cleaned_response))
        total_tokens, price = self.calculate_price(prompt, cleaned_response)
        full_history = "\n".join([f"پرسش: {q}\nپاسخ: {a}" for q, a in self.chat_history])
        summary_text = self.summarize_chat() if summarize else "خلاصه‌سازی غیرفعال است."
        if summarize and summary_text != "خلاصه‌سازی غیرفعال است.":
            self.db.save_summary({
                'summary': summary_text,
                'model': model_name,
                'tokens': total_tokens,
                'user_id': user_id,
                'chat_history': full_history
            })
        return cleaned_response, summary_text, total_tokens, price
  
    def clear_history(self):
        self.chat_history = []
        return self.chat_history
