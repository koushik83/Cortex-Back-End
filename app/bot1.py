from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class EnhancedCompanyBot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.company_data: Dict[str, Dict] = {}
        self.chat_history: Dict[str, List] = {}
        self.current_conversation = {
            'last_query': None,
            'last_context': None,
            'current_topic': None,
            'last_response': None
        }

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into smaller chunks at sentence boundaries"""
        sentences = re.split('[.!?]+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_length + len(sentence) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(sentence)
            current_length += len(sentence)
            
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def _extract_topic(self, query: str, context: str) -> str:
        """Extract the main topic from query and context"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            prompt = f"""Extract the main topic being discussed.
            Query: {query}
            Context: {context}
            Return a brief topic descriptor."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract main topics from conversations"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Topic extraction error: {str(e)}")
            return query

    def _is_follow_up_question(self, message: str) -> bool:
        """Detect if a question is a follow-up to the previous one"""
        follow_up_indicators = [
            'it', 'that', 'this', 'they', 'those', 'these',
            'what about', 'how about', 'what is', 'tell me more'
        ]
        message_lower = message.lower()
        return (
            any(indicator in message_lower for indicator in follow_up_indicators) and
            self.current_conversation['last_query'] is not None
        )

    def _enhance_with_context(self, message: str) -> str:
        """Enhance a follow-up question with context from the previous interaction"""
        if not self.current_conversation['current_topic']:
            return message
            
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        prompt = f"""Previous topic: {self.current_conversation['current_topic']}
        Previous query: {self.current_conversation['last_query']}
        Follow-up question: {message}
        
        Create a self-contained version of the follow-up question incorporating the context."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Convert follow-up questions into self-contained queries"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Query enhancement error: {str(e)}")
            return message

    def _get_openai_summary(self, context: str, question: str) -> str:
        """Get a concise answer from OpenAI based on context"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Given the context below, provide a specific, factual answer with exact details from the document.
            If discussing policies or procedures, include key specifics like numbers, durations, or requirements.
            If information isn't found in the context, explicitly state that.
            
            
            Context: {context}
            Question: {question}

            Provide a clear, direct answer based on the context:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise and helpful assistant. Provide specific information from the given context. Avoid general statements when specific details are available."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            return f"Error with OpenAI API: {str(e)}"

    def add_company_data(self, company_id: str, texts: List[str], sources: List[str]) -> bool:
        """Process and store company documents with source tracking"""
        try:
            all_chunks = []
            chunk_sources = []
            
            for text, source in zip(texts, sources):
                chunks = self._chunk_text(text)
                all_chunks.extend(chunks)
                chunk_sources.extend([source] * len(chunks))
            
            vectors = self.vectorizer.fit_transform(all_chunks)
            
            self.company_data[company_id] = {
                'texts': all_chunks,
                'vectors': vectors,
                'sources': chunk_sources,
                'last_updated': datetime.now()
            }
            return True
        except Exception as e:
            print(f"Error adding company data: {str(e)}")
            return False

    def get_response(self, company_id: str, message: str) -> Tuple[str, float, str, str]:
        """Get chatbot response for a message"""
        if company_id not in self.company_data:
            return "Company not found.", 0.0, "", ""

        try:
            # Check if this is a follow-up question
            if self._is_follow_up_question(message):
                enhanced_message = self._enhance_with_context(message)
                print(f"Enhanced query: {enhanced_message}")
            else:
                enhanced_message = message
            
            # Transform enhanced message to vector
            message_vector = self.vectorizer.transform([enhanced_message])
            
            # Calculate similarities
            similarities = cosine_similarity(
                message_vector, 
                self.company_data[company_id]['vectors']
            ).flatten()
            
            # Get top 2 most relevant chunks
            top_indices = np.argsort(similarities)[-2:][::-1]
            
            # If best similarity is too low, return generic response
            if similarities[top_indices[0]] < 0.1:
                return "I couldn't find relevant information to answer your question.", 0.0, "", ""
            
            # Combine relevant chunks into context
            relevant_chunks = [self.company_data[company_id]['texts'][i] 
                             for i in top_indices if similarities[i] > 0.1]
            context = " ".join(relevant_chunks)
            
            # Get source for the best match
            source = f"Source Document: {self.company_data[company_id]['sources'][top_indices[0]]}"
            
            # Get summarized response from OpenAI
            response = self._get_openai_summary(context, enhanced_message)
            confidence = float(similarities[top_indices[0]])
            
            # Update conversation context
            self._update_conversation_context(message, context, response)
            
            return response, confidence, context, source
        
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I encountered an error processing your message.", 0.0, "", ""

    def _update_conversation_context(self, query: str, context: str, response: str):
        """Update the current conversation context"""
        self.current_conversation = {
            'last_query': query,
            'last_context': context,
            'last_response': response,
            'current_topic': self._extract_topic(query, context)
        }

    def get_company_analytics(self, company_id: str) -> Dict:
        """Get analytics for company interactions"""
        if company_id not in self.chat_history:
            return {
                "total_interactions": 0,
                "average_confidence": 0.0,
                "history": []
            }

        history = self.chat_history[company_id]
        total = len(history)
        avg_confidence = sum(chat['confidence'] for chat in history) / total if total > 0 else 0

        return {
            "total_interactions": total,
            "average_confidence": avg_confidence,
            "history": history[-50:]
        }

    def _add_to_history(self, company_id: str, message: str, response: str, confidence: float):
        """Add interaction to chat history"""
        if company_id not in self.chat_history:
            self.chat_history[company_id] = []
            
        self.chat_history[company_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response,
            'confidence': confidence
        })

# Create a singleton instance
bot_instance = EnhancedCompanyBot()

# Export functions for easier access
def process_message(company_id: str, message: str) -> Tuple[str, float, str, str]:
    return bot_instance.get_response(company_id, message)

def add_company_knowledge(company_id: str, texts: List[str], sources: List[str]) -> bool:
    return bot_instance.add_company_data(company_id, texts, sources)

def get_analytics(company_id: str) -> Dict:
    return bot_instance.get_company_analytics(company_id)