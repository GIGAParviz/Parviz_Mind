import re
from enum import Enum
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass

class ChunkingStrategy(Enum):
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FIXED_LENGTH = "fixed_length"
    SMART = "smart"

@dataclass
class ResponseChunk:
    content: str
    sequence: int
    total_chunks: int
    metadata: Dict

class ResponseManager:
    """Manager for handling response chunking and streaming."""
    
    def __init__(self):
        """Initialize the response manager."""
        self.default_chunk_size = 100  # Default chunk size in tokens
    
    def estimate_response_length(self, prompt: str, model_name: str,
                               creativity: float = 0.7) -> int:
        """
        Estimate the expected length of a response.
        
        Args:
            prompt: The input prompt
            model_name: The model being used
            creativity: Creativity level (0.0 to 1.0)
            
        Returns:
            int: Estimated response length in tokens
        """
        # Simple heuristic: response length is proportional to prompt length and creativity
        prompt_length = len(prompt.split())
        
        # Base multiplier depends on the model
        model_multipliers = {
            "llama2": 1.5,
            "llama3": 2.0,
            "gemma": 1.8,
            "claude2": 2.5,
            "groq-llama3": 2.0
        }
        
        multiplier = model_multipliers.get(model_name, 2.0)
        
        # Creativity affects length - higher creativity tends to produce longer responses
        creativity_factor = 1.0 + (creativity * 0.5)
        
        # Calculate estimated length
        estimated_length = int(prompt_length * multiplier * creativity_factor)
        
        # Apply reasonable bounds
        min_length = 50
        max_length = 1000
        
        return max(min_length, min(estimated_length, max_length))
    
    def chunk_response(self, response: str, strategy: ChunkingStrategy = ChunkingStrategy.SMART,
                      chunk_size: Optional[int] = None) -> List[ResponseChunk]:
        """
        Split a response into chunks based on the specified strategy.
        
        Args:
            response: The response text to chunk
            strategy: Chunking strategy to use
            chunk_size: Optional custom chunk size
            
        Returns:
            List[ResponseChunk]: List of response chunks
        """
        if not response:
            return []
            
        # Use default chunk size if not specified
        if chunk_size is None:
            chunk_size = self.default_chunk_size
        
        # Choose chunking method based on strategy
        if strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentences(response)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(response)
        elif strategy == ChunkingStrategy.FIXED_LENGTH:
            chunks = self._chunk_fixed_length(response)
        else:  # SMART or default
            chunks = self._chunk_smart(response)
        
        # Create ResponseChunk objects
        result = []
        total_chunks = len(chunks)
        
        for i, content in enumerate(chunks):
            chunk = ResponseChunk(
                content=content,
                sequence=i + 1,
                total_chunks=total_chunks,
                metadata={
                    "is_first": i == 0,
                    "is_last": i == total_chunks - 1,
                    "progress": (i + 1) / total_chunks
                }
            )
            result.append(chunk)
        
        return result
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """
        Split text into chunks by sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of sentence chunks
        """
        # Simple sentence splitting regex
        # This is a simplified approach - a more robust implementation would use NLP
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would make the chunk too long, start a new chunk
            if current_chunk and len(current_chunk) + len(sentence) > 200:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text into chunks by paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of paragraph chunks
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _chunk_fixed_length(self, text: str) -> List[str]:
        """
        Split text into fixed-length chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of fixed-length chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.default_chunk_size):
            chunk = " ".join(words[i:i + self.default_chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_smart(self, text: str) -> List[str]:
        """
        Split text using a smart strategy that preserves context.
        
        Args:
            text: Text to split
            
        Returns:
            List[str]: List of smart chunks
        """
        # First try to split by paragraphs
        paragraphs = self._chunk_by_paragraphs(text)
        
        # If paragraphs are too long, split them further by sentences
        chunks = []
        for paragraph in paragraphs:
            if len(paragraph.split()) > self.default_chunk_size * 2:
                # This paragraph is too long, split it by sentences
                sentences = self._chunk_by_sentences(paragraph)
                chunks.extend(sentences)
            else:
                chunks.append(paragraph)
        
        return chunks
    
    def stream_response(self, chunks: List[ResponseChunk]) -> Generator[ResponseChunk, None, None]:
        """
        Stream response chunks with appropriate timing.
        
        Args:
            chunks: List of response chunks
            
        Yields:
            ResponseChunk: Each chunk in sequence
        """
        import time
        
        for chunk in chunks:
            # Add a small delay between chunks to simulate typing
            # The delay is proportional to the chunk length
            delay = min(0.5, len(chunk.content) * 0.01)
            time.sleep(delay)
            
            yield chunk
    
    def format_chunk_metadata(self, chunk: ResponseChunk) -> Dict:
        """
        Format chunk metadata for API response.
        
        Args:
            chunk: The response chunk
            
        Returns:
            Dict: Formatted metadata
        """
        return {
            "sequence": chunk.sequence,
            "total_chunks": chunk.total_chunks,
            "progress": chunk.metadata["progress"],
            "is_first": chunk.metadata["is_first"],
            "is_last": chunk.metadata["is_last"]
        }
    
    def merge_chunks(self, chunks: List[ResponseChunk]) -> str:
        """Merge chunks back into a single response."""
        return " ".join(chunk.content for chunk in chunks)
    
    def validate_chunk_sequence(self, chunks: List[ResponseChunk]) -> bool:
        """
        Validate that chunks form a complete sequence.
        
        Args:
            chunks: List of response chunks
            
        Returns:
            bool: True if sequence is valid
        """
        if not chunks:
            return True
            
        # Check that all sequence numbers are present
        sequences = [chunk.sequence for chunk in chunks]
        expected_sequences = list(range(1, chunks[0].total_chunks + 1))
        
        return sorted(sequences) == expected_sequences
    
    def get_chunk_summary(self, chunk: ResponseChunk) -> str:
        """
        Get a summary of a chunk for logging.
        
        Args:
            chunk: The response chunk
            
        Returns:
            str: Summary of the chunk
        """
        content_preview = chunk.content[:30] + "..." if len(chunk.content) > 30 else chunk.content
        return f"Chunk {chunk.sequence}/{chunk.total_chunks}: {content_preview}"
