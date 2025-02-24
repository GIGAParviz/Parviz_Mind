# **ParvizMind**  
**An Advanced AI with Multi-Step Reasoning and Document Management**

---

## **📌 Project Overview**  
**ParvizMind** is an intelligent chatbot developed using Large Language Models (LLMs) and advanced Natural Language Processing (NLP) techniques. This project offers the following features:  
- **Smart Responses**: Accurate and context-aware answers based on user queries and uploaded documents.  
- **Document Management**: Supports PDF and TXT files for information extraction and document-based responses.  
- **Conversation Summarization**: Automatically generates summaries of conversations for quick review.  
- **Advanced Settings**: Customize tone, creativity, response length, and other parameters for a personalized user experience.  
- **Conversation Database**: Stores chat history and summaries in an SQLite database.  

---

## **🌟 Key Features**  
- **Support for Large Language Models (LLMs)**: Utilizes models like **DeepSeek**, **Llama 3**, and **Gemma**.  
- **Document Processing**: Extracts text from PDF and TXT files and uses them as references for responses.  
- **Semantic Search**: Uses **ChromaDB** for semantic search and retrieval of relevant information.  
- **Automatic Summarization**: Generates summaries of conversations and stores them in a database.  
- **Cost Calculation**: Calculates the cost of using LLMs based on token count.  

---

## **🛠️ Technologies Used**  
- **Programming Languages**: Python  
- **Frameworks and Libraries**:  
  - **LangChain**: For managing language models and processing chains.  
  - **Gradio**: For creating a web-based user interface.  
  - **ChromaDB**: For vector storage and document retrieval.  
  - **PyPDF**: For extracting text from PDF files.  
  - **SQLite**: For storing chat history and summaries.  
- **Language Models**:  
  - **DeepSeek**, **Llama 3**, **Gemma** (via **ChatGroq**).  
  - **HeydariAI/Persian-Embeddings**: For generating Persian text embeddings.  

---

## **🚀 How to Run the Project**  

### **Prerequisites**  
- Python 3.8 or higher  
- Install required libraries  

### **Installation and Setup**  
1. **Clone the Repository**:  
   ```bash
   git clone https://github.com/your-username/Parviz_Mind.git
   cd Parviz_Mind
   ```

2. **Install Required Libraries**:  
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Project**:  
   ```bash
   cd Parviz_Mind/chatbot
   python app.py
   ```

4. **Access the User Interface**:  
   After running the project, navigate to `http://localhost:7860`.

---

## **🎯 Use Cases**  
- **Automated Support**: Use as a support chatbot to answer frequently asked questions.  
- **Document Analysis**: Extract and analyze information from PDF and TXT files.  
- **Summarization**: Automatically generate summaries of conversations and documents.  
- **Academic Research**: Use for analyzing scientific texts and generating content.  

---

## **📂 Project Structure**  
```
parviz-mind/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── ai_core.py
│   ├── routes.py
├── static/
│   └── swagger.json
├── templates/
│   └── index.html
├── uploads/  (ignored in .gitignore)
├── requirements.txt
├── .gitignore
├── README.md
├── run.py
```

## **📞 Contact the Developer**  
If you have any questions or would like to contribute to the project, feel free to reach out:  
📧 **a.m.parviz02@gmail.com**  
📱 **Telegram**: [@am_parviz](https://t.me/am_parviz)  

---

## **📜 License**  
This project is licensed under the **MIT License**. For more information, see the [LICENSE](LICENSE) file.  

---

**Thank you for using ParvizMind!** 🚀  

--- 

This version includes your Telegram address and the updated chatbot name. Let me know if you need further adjustments! 😊
