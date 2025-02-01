from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
import pickle
from pathlib import Path

class DataStore:
    def __init__(self):
        # Create data directories if they don't exist
        self.base_dir = Path("data")
        self.companies_dir = self.base_dir / "companies"
        self.embeddings_dir = self.base_dir / "embeddings"
        self.chats_dir = self.base_dir / "chats"
        
        # Create directories
        for directory in [self.base_dir, self.companies_dir, 
                         self.embeddings_dir, self.chats_dir]:
            directory.mkdir(exist_ok=True)
            
        # In-memory cache
        self._cache = {}

    def save_company_data(self, company_id: str, data: Dict) -> bool:
        """Save company information and documents"""
        try:
            # Save basic company info as JSON
            company_file = self.companies_dir / f"{company_id}.json"
            with open(company_file, 'w') as f:
                json.dump({
                    'company_id': company_id,
                    'updated_at': datetime.now().isoformat(),
                    'documents': data.get('documents', []),
                    'config': data.get('config', {})
                }, f)

            # Save embeddings as pickle (more efficient for numpy arrays)
            if 'embeddings' in data:
                emb_file = self.embeddings_dir / f"{company_id}.pkl"
                with open(emb_file, 'wb') as f:
                    pickle.dump(data['embeddings'], f)

            # Update cache
            self._cache[f"company_{company_id}"] = data
            
            return True
        except Exception as e:
            print(f"Error saving company data: {str(e)}")
            return False

    def get_company_data(self, company_id: str) -> Optional[Dict]:
        """Retrieve company data, using cache if available"""
        cache_key = f"company_{company_id}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # Load basic company info
            company_file = self.companies_dir / f"{company_id}.json"
            if not company_file.exists():
                return None
                
            with open(company_file, 'r') as f:
                data = json.load(f)
            
            # Load embeddings if they exist
            emb_file = self.embeddings_dir / f"{company_id}.pkl"
            if emb_file.exists():
                with open(emb_file, 'rb') as f:
                    data['embeddings'] = pickle.load(f)
            
            # Update cache
            self._cache[cache_key] = data
            return data
            
        except Exception as e:
            print(f"Error loading company data: {str(e)}")
            return None

    def save_chat(self, company_id: str, chat_data: Dict) -> bool:
        """Save chat interaction"""
        try:
            chat_file = self.chats_dir / f"{company_id}_chats.jsonl"
            
            # Append chat to file
            with open(chat_file, 'a') as f:
                chat_data['timestamp'] = datetime.now().isoformat()
                f.write(json.dumps(chat_data) + '\n')
                
            return True
        except Exception as e:
            print(f"Error saving chat: {str(e)}")
            return False

    def get_chats(self, company_id: str, limit: int = 100) -> List[Dict]:
        """Retrieve recent chats for a company"""
        try:
            chat_file = self.chats_dir / f"{company_id}_chats.jsonl"
            if not chat_file.exists():
                return []
                
            chats = []
            with open(chat_file, 'r') as f:
                for line in f:
                    chats.append(json.loads(line.strip()))
            
            # Return most recent chats first
            return sorted(chats, 
                         key=lambda x: x['timestamp'], 
                         reverse=True)[:limit]
                         
        except Exception as e:
            print(f"Error loading chats: {str(e)}")
            return []

    def clear_cache(self):
        """Clear the in-memory cache"""
        self._cache = {}

# Create singleton instance
store = DataStore()

# Export functions for easier access
def save_data(company_id: str, data: Dict) -> bool:
    return store.save_company_data(company_id, data)

def get_data(company_id: str) -> Optional[Dict]:
    return store.get_company_data(company_id)

def save_chat_interaction(company_id: str, chat_data: Dict) -> bool:
    return store.save_chat(company_id, chat_data)

def get_chat_history(company_id: str, limit: int = 100) -> List[Dict]:
    return store.get_chats(company_id, limit)