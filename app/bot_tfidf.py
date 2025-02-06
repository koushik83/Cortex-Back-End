from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import re
import openai
from dotenv import load_dotenv
import os
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import torch
from collections import Counter

# Load environment variables
load_dotenv()

class EnhancedCompanyBot:
    def __init__(self):
        # Initialize models and vectorizers
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        
        # Storage for company data
        self.company_data: Dict[str, Dict] = {}
        self.chat_history: Dict[str, List] = {}
        self.current_conversation = {
            'last_query': None,
            'last_context': None,
            'current_topic': None,
            'last_response': None
        }
        
        # Search parameters
        self.hybrid_weight = 0.7  # Weight for semantic search vs BM25
        self.top_k = 3  # Number of results to retrieve
        
        # Error tracking
        self.error_log: List[Dict] = []

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

    def _create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=True)
            return embeddings.cpu().numpy()
        except Exception as e:
            self._log_error("Embedding creation error", str(e))
            raise

    def add_company_data(self, company_id: str, texts: List[str], sources: List[str]) -> bool:
        """Process and store company documents"""
        try:
            # Process texts into chunks
            all_chunks = []
            chunk_sources = []
            
            for text, source in zip(texts, sources):
                chunks = self._chunk_text(text)
                all_chunks.extend(chunks)
                chunk_sources.extend([source] * len(chunks))
            
            # Create embeddings and TF-IDF vectors
            embeddings = self._create_embeddings(all_chunks)
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_chunks)
            
            # Create BM25 index
            tokenized_chunks = [chunk.lower().split() for chunk in all_chunks]
            bm25 = BM25Okapi(tokenized_chunks)
            
            # Store all data
            self.company_data[company_id] = {
                'texts': all_chunks,
                'sources': chunk_sources,
                'embeddings': embeddings,
                'tfidf_matrix': tfidf_matrix,
                'bm25': bm25,
                'last_updated': datetime.now()
            }
            
            return True
        except Exception as e:
            self._log_error("Company data addition error", str(e))
            return False

    def _hybrid_search(self, query: str, company_id: str) -> List[Tuple[int, float]]:
        """Perform hybrid search combining semantic and BM25"""
        try:
            company = self.company_data[company_id]
            
            # Semantic search
            query_embedding = self._create_embeddings([query])[0]
            semantic_similarities = cosine_similarity(
                query_embedding.reshape(1, -1), 
                company['embeddings']
            )[0]
            
            # TF-IDF search
            tfidf_query = self.tfidf_vectorizer.transform([query])
            tfidf_similarities = cosine_similarity(tfidf_query, company['tfidf_matrix'])[0]
            
            # BM25 search
            tokenized_query = query.lower().split()
            bm25_scores = company['bm25'].get_scores(tokenized_query)
            
            # Normalize scores
            semantic_scores = (semantic_similarities + 1) / 2  # Convert to 0-1 range
            if max(bm25_scores) > 0:
                bm25_scores = bm25_scores / max(bm25_scores)
            
            # Combine scores (semantic + BM25)
            combined_scores = []
            for i in range(len(company['texts'])):
                combined_score = (self.hybrid_weight * semantic_scores[i] + 
                                (1 - self.hybrid_weight) * bm25_scores[i])
                combined_scores.append((i, combined_score))
            
            # Sort by combined score
            return sorted(combined_scores, key=lambda x: x[1], reverse=True)[:self.top_k]
            
        except Exception as e:
            self._log_error("Hybrid search error", str(e))
            raise

    def get_response(self, company_id: str, message: str) -> Tuple[str, float, str, str]:
        """Get chatbot response using hybrid search"""
        if company_id not in self.company_data:
            return "Company not found.", 0.0, "", ""

        try:
            # Enhance query if it's a follow-up
            if self._is_follow_up_question(message):
                enhanced_message = self._enhance_with_context(message)
            else:
                enhanced_message = message
            
            # Perform hybrid search
            search_results = self._hybrid_search(enhanced_message, company_id)
            
            if not search_results or search_results[0][1] < 0.1:
                return "I couldn't find relevant information to answer your question.", 0.0, "", ""
            
            # Get relevant chunks and source
            relevant_indices = [idx for idx, score in search_results if score > 0.1]
            relevant_chunks = [self.company_data[company_id]['texts'][i] for i in relevant_indices]
            context = " ".join(relevant_chunks)
            source = f"Source: {self.company_data[company_id]['sources'][relevant_indices[0]]}"
            
            # Generate response using OpenAI
            response = self._get_openai_summary(context, enhanced_message)
            confidence = float(search_results[0][1])
            
            # Update conversation context
            self._update_conversation_context(enhanced_message, context, response)
            self._add_to_history(company_id, message, response, confidence)
            
            return response, confidence, context, source
            
        except Exception as e:
            self._log_error("Response generation error", str(e))
            return "I encountered an error processing your request.", 0.0, "", ""

    def _get_openai_summary(self, context: str, question: str) -> str:
        """Get a precise answer from OpenAI"""
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
            self._log_error("OpenAI summary error", str(e))
            return f"Error processing request: {str(e)}"

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
        """Enhance a follow-up question with context"""
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
            self._log_error("Context enhancement error", str(e))
            return message

    def _extract_topic(self, query: str, context: str) -> str:
        """Extract the main topic from query and context"""
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            prompt = f"""Identify the core technical/business topic from this interaction:
            Query: {query}
            Context: {context}
            Return a 3-5 word topic descriptor."""
            
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
            self._log_error("Topic extraction error", str(e))
            return query.split()[0] if query else "general"

    def _update_conversation_context(self, query: str, context: str, response: str):
        """Update conversation tracking"""
        self.current_conversation = {
            'last_query': query,
            'last_context': context,
            'last_response': response,
            'current_topic': self._extract_topic(query, context)
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

    def _log_error(self, error_type: str, error_message: str):
        """Log errors for monitoring"""
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message
        })

    def get_error_stats(self) -> Dict:
        """Get error statistics for monitoring"""
        if not self.error_log:
            return {"total_errors": 0, "error_types": {}}
            
        error_types = Counter(error['type'] for error in self.error_log)
        return {
            "total_errors": len(self.error_log),
            "error_types": dict(error_types.most_common())
        }

    def get_analytics(self, company_id: str) -> Dict:
        """Get analytics for company interactions"""
        if company_id not in self.chat_history:
            return {
                "total_interactions": 0,
                "average_confidence": 0.0,
                "recent_topics": [],
                "error_rate": 0.0
            }

        history = self.chat_history[company_id]
        total = len(history)
        avg_confidence = sum(chat['confidence'] for chat in history) / total if total > 0 else 0
        
        # Get recent topics
        recent_topics = [chat['topic'] for chat in history[-10:]]
        topic_counts = Counter(recent_topics).most_common()

        return {
            "total_interactions": total,
            "average_confidence": round(avg_confidence, 2),
            "recent_topics": topic_counts,
            "error_rate": len(self.error_log) / total if total > 0 else 0
        }

# Create singleton instance
bot_instance = EnhancedCompanyBot()

# Export public API functions
def process_message(company_id: str, message: str) -> Tuple[str, float, str, str]:
    return bot_instance.get_response(company_id, message)

def add_company_knowledge(company_id: str, texts: List[str], sources: List[str]) -> bool:
    return bot_instance.add_company_data(company_id, texts, sources)

def get_analytics(company_id: str) -> Dict:
    return bot_instance.get_analytics(company_id)

def get_error_stats() -> Dict:
    return bot_instance.get_error_stats()