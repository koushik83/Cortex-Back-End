from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimpleCompanyBot:
    def __init__(self):
        # Initialize the vectorizer
        self.vectorizer = TfidfVectorizer()
        # In-memory storage
        self.company_data: Dict[str, Dict] = {}
        self.chat_history: Dict[str, List] = {}

    def add_company_data(self, company_id: str, texts: List[str]) -> bool:
        """Add or update company knowledge base"""
        try:
            # Create TF-IDF vectors for texts
            vectors = self.vectorizer.fit_transform(texts)
            
            self.company_data[company_id] = {
                'texts': texts,
                'vectors': vectors,
                'last_updated': datetime.now()
            }
            return True
        except Exception as e:
            print(f"Error adding company data: {str(e)}")
            return False

    def get_response(self, company_id: str, message: str) -> Tuple[str, float]:
        """Get chatbot response for a message"""
        if company_id not in self.company_data:
            return "Company not found.", 0.0

        try:
            # Transform user message to vector
            message_vector = self.vectorizer.transform([message])
            
            # Calculate similarities with all company texts
            similarities = cosine_similarity(
                message_vector, 
                self.company_data[company_id]['vectors']
            ).flatten()
            
            # Get best match
            best_idx = np.argmax(similarities)
            confidence = similarities[best_idx]
            response = self.company_data[company_id]['texts'][best_idx]

            # Store in chat history
            self._add_to_history(company_id, message, response, float(confidence))
            
            return response, float(confidence)
        
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I encountered an error processing your message.", 0.0

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
            "history": history[-50:]  # Return last 50 interactions
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
bot_instance = SimpleCompanyBot()

# Export functions for easier access
def process_message(company_id: str, message: str) -> Tuple[str, float]:
    return bot_instance.get_response(company_id, message)

def add_company_knowledge(company_id: str, texts: List[str]) -> bool:
    return bot_instance.add_company_data(company_id, texts)

def get_analytics(company_id: str) -> Dict:
    return bot_instance.get_company_analytics(company_id)