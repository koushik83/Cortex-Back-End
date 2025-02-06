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
        sentences = re.split(r'(?<=[.!?]) +', text)
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
            prompt = f"""Identify the core technical/business topic from this interaction:
            Query: {query}
            Context: {context}
            Return a 3-5 word topic descriptor focusing on key entities and actions."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract technical conversation topics"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=25,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Topic extraction error: {str(e)}")
            return query.split()[0] if query else "general"

    def _enhance_query(self, query: str) -> str:
        """Universal query normalization with conversation awareness"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            prompt = f"""Improve this query for technical document search:
            1. Correct spelling/grammar
            2. Expand domain-specific abbreviations
            3. Add relevant context from: {self.current_conversation['current_topic']}
            4. Maintain original intent
            
            Original: {query}
            Improved:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a query optimization engine"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            enhanced = response.choices[0].message.content.strip()
            return enhanced if enhanced else query
        except Exception as e:
            print(f"Query enhancement error: {e}")
            return query

    def _is_follow_up_question(self, message: str) -> bool:
        """Detect if a question is a follow-up to the previous one"""
        follow_up_indicators = [
            'it', 'that', 'this', 'they', 'those', 'these',
            'following up', 'regarding', 'about that'
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
            
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            prompt = f"""Previous Topic: {self.current_conversation['current_topic']}
            Last Query: {self.current_conversation['last_query']}
            Follow-up: {message}
            
            Create a standalone question that explicitly includes needed context."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Convert follow-ups to context-aware queries"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Context enhancement error: {str(e)}")
            return message

    def _get_openai_summary(self, context: str, question: str) -> str:
        """Get a precise, numbers-focused answer from OpenAI"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Answer STRICTLY using the context. Follow these rules:
            1. Cite EXACT numbers/dates/percentages when available
            2. For policies: List ALL conditions and steps
            3. Use bullet points for multi-part answers
            4. If unsure, say "According to documentation: [EXCERPT]"
            5. Never invent numbers
            
            Context: {context}
            Question: {question}
            Answer:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precision-focused technical assistant"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            return f"Error processing request: {str(e)}"

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
            # Universal query enhancement
            enhanced_query = self._enhance_query(message)
            
            # Contextual follow-up handling
            if self._is_follow_up_question(enhanced_query):
                final_query = self._enhance_with_context(enhanced_query)
            else:
                final_query = enhanced_query
            
            # Transform query to vector
            message_vector = self.vectorizer.transform([final_query])
            
            # Calculate similarities
            similarities = cosine_similarity(
                message_vector, 
                self.company_data[company_id]['vectors']
            ).flatten()
            
            # Get top 2 relevant chunks
            top_indices = np.argsort(similarities)[-2:][::-1]
            
            # Threshold check
            if similarities[top_indices[0]] < 0.12:
                return "I need more specific information to answer that.", 0.0, "", ""
            
            # Combine relevant context
            relevant_chunks = [self.company_data[company_id]['texts'][i] 
                             for i in top_indices if similarities[i] > 0.12]
            context = " ".join(relevant_chunks)
            
            # Get source attribution
            source = f"Source: {self.company_data[company_id]['sources'][top_indices[0]]}"
            
            # Generate precise answer
            response = self._get_openai_summary(context, final_query)
            confidence = float(similarities[top_indices[0]])
            
            # Update conversation state
            self._update_conversation_context(final_query, context, response)
            self._add_to_history(company_id, message, response, confidence)
            
            return response, confidence, context, source
        
        except Exception as e:
            print(f"Response generation error: {str(e)}")
            return "I encountered an error processing your request.", 0.0, "", ""

    def _update_conversation_context(self, query: str, context: str, response: str):
        """Update conversation tracking"""
        self.current_conversation = {
            'last_query': query,
            'last_context': context,
            'last_response': response,
            'current_topic': self._extract_topic(query, context)
        }

    def get_company_analytics(self, company_id: str) -> Dict:
        """Get interaction analytics"""
        if company_id not in self.chat_history:
            return {
                "total_interactions": 0,
                "average_confidence": 0.0,
                "common_topics": []
            }

        history = self.chat_history[company_id]
        total = len(history)
        avg_confidence = sum(chat['confidence'] for chat in history) / total if total > 0 else 0
        
        # Extract common topics from last 50 interactions
        topics = [chat['response'].get('topic', 'general') for chat in history[-50:]]
        common_topics = Counter(topics).most_common(3)

        return {
            "total_interactions": total,
            "average_confidence": round(avg_confidence, 2),
            "common_topics": common_topics
        }

    def _add_to_history(self, company_id: str, message: str, response: str, confidence: float):
        """Record interaction history"""
        if company_id not in self.chat_history:
            self.chat_history[company_id] = []
            
        self.chat_history[company_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response,
            'confidence': confidence,
            'topic': self.current_conversation['current_topic']
        })

# Singleton instance
bot_instance = EnhancedCompanyBot()

# Public API
def process_message(company_id: str, message: str) -> Tuple[str, float, str, str]:
    return bot_instance.get_response(company_id, message)

def add_company_knowledge(company_id: str, texts: List[str], sources: List[str]) -> bool:
    return bot_instance.add_company_data(company_id, texts, sources)

def get_analytics(company_id: str) -> Dict:
    return bot_instance.get_company_analytics(company_id)