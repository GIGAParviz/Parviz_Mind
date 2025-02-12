import os
import re
from pypdf import PdfReader
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database import DatabaseManager

class AICore:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="heydariAI/persian-embeddings")
        self.vector_store = Chroma(embedding_function=self.embeddings)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.chat_history = []
        self.price_per_token = 0.00001
        self.api_key = "your_groq_api_key"  # Replace with your actual key
        self.model = ChatGroq(api_key=self.api_key, model_name="deepseek-r1-distill-llama-70b")
        self.db = DatabaseManager()

    def process_file(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".pdf":
            reader = PdfReader(file_path)
            file_text = "\n".join(page.extract_text() for page in reader.pages)
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                file_text = f.read()
        else:
            raise ValueError("Unsupported file format")
        
        file_docs = [Document(page_content=file_text)]
        file_splits = self.text_splitter.split_documents(file_docs)
        self.vector_store.add_documents(file_splits)
        return file_text

    def summarize_chat(self):
        chat_text = "\n".join([f"پرسش: {q}\nپاسخ: {a}" for q, a in self.chat_history])
        summary_prompt = f"یک خلاصه کوتاه از مکالمه زیر ارائه کن:\n\n{chat_text}\n\nخلاصه:"
        summary_response = self.model.invoke(summary_prompt)
        return summary_response.content

    def answer_query(self, query):
        response = self.model.invoke(f"سوال: {query}\nپاسخ:")
        return response.content
