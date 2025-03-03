import os
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

class KnowledgeBaseError(Exception):
    """Exception for knowledge base errors."""
    pass

class KnowledgeBase:
    """Service for managing and searching knowledge base documents."""
    
    def __init__(self, vector_store=None):
        """Initialize the knowledge base with an optional vector store."""
        self.vector_store = vector_store or self._create_vector_store()
        
    def _create_vector_store(self):
        """Create a new vector store."""
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Create an empty FAISS index
        return FAISS.from_documents(
            [Document(page_content="Initialization document", metadata={"source": "init"})],
            embeddings
        )
    
    def scrape_website(self, url: str, max_pages: int = 10) -> List[Document]:
        """
        Scrape content from a website and add it to the knowledge base.
        
        Args:
            url: URL of the website to scrape
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of documents added to the knowledge base
        """
        try:
            # Load content from the URL
            loader = WebBaseLoader(url)
            documents = loader.load()
            
            # If we need to follow links and load more pages
            if max_pages > 1:
                # This is a simplified version; a real implementation would need
                # to extract links from the first page and follow them
                pass
            
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            split_docs = text_splitter.split_documents(documents)
            
            # Add metadata
            for doc in split_docs:
                doc.metadata.update({
                    "source": url,
                    "source_type": "website",
                    "date_added": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())
                })
            
            # Add to vector store
            self.vector_store.add_documents(split_docs)
            
            return split_docs
        except Exception as e:
            raise KnowledgeBaseError(f"Error scraping website {url}: {str(e)}")
    
    def learn_from_blog(self, blog_url: str, api_key: Optional[str] = None) -> List[Document]:
        """
        Learn from a blog by extracting articles and adding them to the knowledge base.
        
        Args:
            blog_url: URL of the blog
            api_key: Optional API key for blog API
            
        Returns:
            List of documents added to the knowledge base
        """
        try:
            # This would normally use a blog-specific API or RSS feed
            # Here's a simplified implementation that assumes blog_url has an API endpoint
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            # Get blog posts (this is a placeholder - actual implementation would vary)
            response = requests.get(f"{blog_url}/api/posts", headers=headers)
            response.raise_for_status()
            
            blog_posts = response.json()
            documents = []
            
            # Process each blog post
            for post in blog_posts:
                # Get full post content if needed
                if "content" not in post:
                    post_response = requests.get(f"{blog_url}/api/posts/{post['id']}", headers=headers)
                    post_response.raise_for_status()
                    post = post_response.json()
                
                # Create a document
                doc = Document(
                    page_content=post["content"],
                    metadata={
                        "title": post.get("title", ""),
                        "author": post.get("author", ""),
                        "published_date": post.get("published_date", ""),
                        "url": post.get("url", ""),
                        "source": blog_url,
                        "source_type": "blog",
                        "date_added": datetime.now().isoformat(),
                        "id": str(uuid.uuid4())
                    }
                )
                documents.append(doc)
            
            # Split into chunks for longer posts
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            split_docs = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(split_docs)
            
            return split_docs
        except Exception as e:
            raise KnowledgeBaseError(f"Error learning from blog {blog_url}: {str(e)}")
    
    def connect_external_db(self, connection_string: str, query: str, metadata_fields: List[str]) -> List[Document]:
        """
        Connect to an external database and add data to the knowledge base.
        
        Args:
            connection_string: Database connection string
            query: SQL query to get data
            metadata_fields: Fields to include in metadata
            
        Returns:
            List of documents added to the knowledge base
        """
        try:
            # This would normally use a database connector like SQLAlchemy
            # Here's a simplified implementation that assumes the connection string is a REST API endpoint
            
            # Get data from the external source
            response = requests.post(
                connection_string,
                json={"query": query, "metadata_fields": metadata_fields}
            )
            response.raise_for_status()
            
            data = response.json()
            documents = []
            
            # Process each data row
            for item in data:
                # Extract content and metadata
                if "content" not in item:
                    continue
                    
                content = item.pop("content")
                
                # Create metadata dict with only the specified fields
                metadata = {
                    "source": connection_string,
                    "source_type": "external_db",
                    "date_added": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())
                }
                
                # Add requested metadata fields
                for field in metadata_fields:
                    if field in item:
                        metadata[field] = item[field]
                
                # Create a document
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            return documents
        except Exception as e:
            raise KnowledgeBaseError(f"Error connecting to external database: {str(e)}")
    
    def add_verified_response(self, question: str, answer: str, metadata: Dict[str, Any]) -> Document:
        """
        Add a verified question-answer pair to the knowledge base.
        
        Args:
            question: The question
            answer: The verified answer
            metadata: Additional metadata
            
        Returns:
            Document added to the knowledge base
        """
        try:
            # Combine question and answer
            content = f"Question: {question}\nAnswer: {answer}"
            
            # Create metadata
            doc_metadata = {
                "question": question,
                "source_type": "verified_response",
                "date_added": datetime.now().isoformat(),
                "id": str(uuid.uuid4())
            }
            
            # Add user metadata
            for key, value in metadata.items():
                doc_metadata[key] = value
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=doc_metadata
            )
            
            # Add to vector store
            self.vector_store.add_documents([doc])
            
            return doc
        except Exception as e:
            raise KnowledgeBaseError(f"Error adding verified response: {str(e)}")
    
    def search_knowledge_base(self, query: str, filter_criteria: Optional[Dict[str, Any]] = None, limit: int = 5) -> List[Document]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            filter_criteria: Optional criteria to filter results
            limit: Maximum number of results
            
        Returns:
            List of relevant documents
        """
        try:
            # If filter is provided, use it
            if filter_criteria:
                docs = self.vector_store.similarity_search_with_filter(
                    query,
                    filter=filter_criteria,
                    k=limit
                )
            else:
                docs = self.vector_store.similarity_search(
                    query,
                    k=limit
                )
                
            return docs
        except Exception as e:
            raise KnowledgeBaseError(f"Error searching knowledge base: {str(e)}")
    
    def export_knowledge_base(self, output_file: str):
        """
        Export the knowledge base to a file.
        
        Args:
            output_file: Path to save the export
        """
        try:
            # Get all documents from the vector store
            # Note: FAISS doesn't have a built-in way to retrieve all documents
            # This is a simplified approach
            
            # Save the FAISS index
            self.vector_store.save_local(output_file)
            
            # Also save metadata as JSON
            docs = []  # This would be all documents in a real implementation
            
            with open(f"{output_file}_metadata.json", "w") as f:
                json.dump([{
                    "content": doc.page_content,
                    "metadata": doc.metadata
                } for doc in docs], f)
                
        except Exception as e:
            raise KnowledgeBaseError(f"Error exporting knowledge base: {str(e)}")
    
    def import_knowledge_base(self, input_file: str):
        """
        Import a knowledge base from a file.
        
        Args:
            input_file: Path to the import file
        """
        try:
            # Load FAISS index
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            self.vector_store = FAISS.load_local(input_file, embeddings)
            
            # Also load metadata if available
            if os.path.exists(f"{input_file}_metadata.json"):
                with open(f"{input_file}_metadata.json", "r") as f:
                    docs_data = json.load(f)
                    
                # Create documents from metadata (in a real implementation)
                # This might involve updating the vector store with the metadata
                pass
                
        except Exception as e:
            raise KnowledgeBaseError(f"Error importing knowledge base: {str(e)}")

# Singleton instance
_knowledge_base_instance = None

def get_knowledge_base():
    """Get the singleton knowledge base instance."""
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = KnowledgeBase()
    return _knowledge_base_instance
