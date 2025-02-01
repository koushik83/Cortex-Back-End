# this is working version bot.py codebase
from typing import Dict, List, Tuple, Any
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import openai
from dotenv import load_dotenv
import os
from collections import Counter

# Load environment variables
load_dotenv()

class EnhancedCompanyBot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.company_data: Dict[str, Dict] = {}
        self.chat_history: Dict[str, List] = {}
        self.key_terms: Dict[str, List] = {}

    def _extract_key_terms(self, chunks: List[str]) -> Dict[str, List[str]]:
        """Extract key terms and their variations from document chunks"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            sample_text = " ".join(chunks[:5])  # Use first few chunks as sample
            
            prompt = """Analyze this text and create a dictionary of key terms and their variations.
            Focus on important business terms, policies, and common concepts.
            Format: {"formal_term": ["variation1", "variation2"]}"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract key terms and variations from business documents"},
                    {"role": "user", "content": f"{prompt}\n\nText: {sample_text}"}
                ],
                temperature=0.3
            )
            
            # Parse response into dictionary
            terms = eval(response.choices[0].message.content)
            return terms
        except Exception as e:
            print(f"Error extracting key terms: {str(e)}")
            return {}

    def _enhance_query(self, raw_query: str, company_id: str) -> str:
        """Enhance the raw query using key terms and OpenAI"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Enhance this query using formal terms from the document.
            Key terms dictionary: {self.company_data[company_id].get('key_terms', {})}
            Original query: {raw_query}
            Return an enhanced, properly spelled, formal version of the query."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Enhance and formalize search queries"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            enhanced_query = response.choices[0].message.content.strip()
            print(f"Enhanced query: {enhanced_query}")
            return enhanced_query
        except Exception as e:
            print(f"Query enhancement error: {str(e)}")
            return raw_query

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

    def _get_openai_summary(self, context: str, question: str) -> str:
        """Get a concise answer from OpenAI based on context"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Based on the following context, provide a brief and direct answer (2-3 lines max) to the question. 
            If the context doesn't contain relevant information, say so.

            Context: {context}
            Question: {question}

            Provide a brief, direct answer:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides brief, direct answers based on the given context. Keep answers to 2-3 lines maximum."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            return f"Error with OpenAI API: {str(e)}"

    def add_company_data(self, company_id: str, texts: List[str]) -> bool:
        """Process and store company documents"""
        try:
            # Process documents into chunks
            all_chunks = []
            for text in texts:
                chunks = self._chunk_text(text)
                all_chunks.extend(chunks)
            
            # Extract key terms from chunks
            key_terms = self._extract_key_terms(all_chunks)
            
            # Generate embeddings
            vectors = self.vectorizer.fit_transform(all_chunks)
            
            # Store all processed data
            self.company_data[company_id] = {
                'texts': all_chunks,
                'vectors': vectors,
                'key_terms': key_terms,
                'last_updated': datetime.now()
            }
            return True
        except Exception as e:
            print(f"Error adding company data: {str(e)}")
            return False

    def get_response(self, company_id: str, message: str) -> Tuple[str, float, str]:
        """Get chatbot response for a message"""
        if company_id not in self.company_data:
            return "Company not found.", 0.0, ""

        try:
            # Enhance the query using key terms
            enhanced_message = self._enhance_query(message, company_id)
            
            # Transform enhanced message to vector
            message_vector = self.vectorizer.transform([enhanced_message])
            
            # Calculate similarities with all chunks
            similarities = cosine_similarity(
                message_vector, 
                self.company_data[company_id]['vectors']
            ).flatten()
            
            # Get top 2 most relevant chunks
            top_indices = np.argsort(similarities)[-2:][::-1]
            
            # If best similarity is too low, return generic response
            if similarities[top_indices[0]] < 0.1:
                return "I couldn't find relevant information to answer your question.", 0.0, ""
            
            # Combine relevant chunks into context
            relevant_chunks = [self.company_data[company_id]['texts'][i] 
                             for i in top_indices if similarities[i] > 0.1]
            context = " ".join(relevant_chunks)
            
            # Get summarized response from OpenAI
            response = self._get_openai_summary(context, enhanced_message)
            confidence = float(similarities[top_indices[0]])
            
            # Store in chat history
            self._add_to_history(company_id, message, response, confidence)
            
            return response, confidence, context
        
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I encountered an error processing your message.", 0.0, ""

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
def process_message(company_id: str, message: str) -> Tuple[str, float, str]:
    return bot_instance.get_response(company_id, message)

def add_company_knowledge(company_id: str, texts: List[str]) -> bool:
    return bot_instance.add_company_data(company_id, texts)

def get_analytics(company_id: str) -> Dict:
    return bot_instance.get_company_analytics(company_id)