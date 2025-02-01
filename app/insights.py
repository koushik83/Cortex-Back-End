from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
from .store import get_chat_history, get_data
from .bot import bot_instance

class InsightsAnalyzer:
    def __init__(self):
        self.confidence_threshold = 0.7  # Minimum confidence score for good responses
        self.frequent_question_threshold = 3  # Min occurrences to be considered frequent

    def get_company_insights(self, company_id: str, days: int = 30) -> Dict:
        """Generate comprehensive insights for a company"""
        chats = get_chat_history(company_id)
        if not chats:
            return self._empty_insights()

        # Convert chats to DataFrame for easier analysis
        df = pd.DataFrame(chats)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter for specified time period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_df = df[df['timestamp'] > cutoff_date]

        return {
            "summary": self._generate_summary(recent_df),
            "usage_patterns": self._analyze_usage_patterns(recent_df),
            "common_topics": self._identify_common_topics(recent_df),
            "performance_metrics": self._calculate_performance_metrics(recent_df),
            "improvement_suggestions": self._generate_suggestions(recent_df)
        }

    def _generate_summary(self, df: pd.DataFrame) -> Dict:
        """Generate high-level summary statistics"""
        return {
            "total_interactions": len(df),
            "unique_users": df['user_id'].nunique() if 'user_id' in df.columns else None,
            "avg_confidence": df['confidence'].mean() if 'confidence' in df.columns else None,
            "total_queries_today": len(df[df['timestamp'].dt.date == datetime.now().date()]),
            "active_hours": self._get_active_hours(df)
        }

    def _analyze_usage_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze when and how the chatbot is being used"""
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()

        return {
            "peak_hours": self._get_peak_hours(df),
            "busiest_days": self._get_busiest_days(df),
            "usage_trends": self._calculate_usage_trends(df),
            "session_analysis": self._analyze_sessions(df)
        }

    def _identify_common_topics(self, df: pd.DataFrame) -> Dict:
        """Identify frequently discussed topics and question patterns"""
        messages = df['message'].tolist() if 'message' in df.columns else []
        
        # Use bot's embedding model to cluster similar questions
        embeddings = bot_instance.model.encode(messages)
        clusters = self._cluster_questions(embeddings)
        
        return {
            "frequent_questions": self._get_frequent_questions(messages, clusters),
            "topic_distribution": self._get_topic_distribution(messages, clusters),
            "trending_topics": self._identify_trending_topics(df)
        }

    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate key performance indicators"""
        return {
            "response_quality": {
                "high_confidence_rate": len(df[df['confidence'] > self.confidence_threshold]) / len(df),
                "avg_confidence": df['confidence'].mean(),
                "confidence_trend": self._calculate_confidence_trend(df)
            },
            "efficiency": {
                "response_times": self._calculate_response_times(df),
                "resolution_rate": self._calculate_resolution_rate(df)
            }
        }

    def _generate_suggestions(self, df: pd.DataFrame) -> List[Dict]:
        """Generate actionable improvement suggestions"""
        suggestions = []
        
        # Analyze low confidence responses
        low_conf = df[df['confidence'] < self.confidence_threshold]
        if len(low_conf) > 0:
            suggestions.append({
                "type": "content_gap",
                "description": "Consider adding more content for these topics",
                "examples": self._get_low_confidence_examples(low_conf)
            })

        # Identify missing knowledge areas
        missing_topics = self._identify_missing_knowledge(df)
        if missing_topics:
            suggestions.append({
                "type": "knowledge_gap",
                "description": "Add information about these topics",
                "topics": missing_topics
            })

        return suggestions

    def _cluster_questions(self, embeddings: np.ndarray, n_clusters: int = 10) -> np.ndarray:
        """Cluster similar questions using K-means"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        return kmeans.fit_predict(embeddings)

    def _get_frequent_questions(self, messages: List[str], clusters: np.ndarray) -> List[Dict]:
        """Identify frequently asked questions within clusters"""
        frequent_questions = []
        
        for cluster_id in range(len(set(clusters))):
            cluster_messages = [msg for i, msg in enumerate(messages) if clusters[i] == cluster_id]
            if len(cluster_messages) >= self.frequent_question_threshold:
                frequent_questions.append({
                    "cluster_id": cluster_id,
                    "sample_questions": cluster_messages[:3],
                    "frequency": len(cluster_messages)
                })
        
        return sorted(frequent_questions, key=lambda x: x['frequency'], reverse=True)

    def _get_topic_distribution(self, messages: List[str], clusters: np.ndarray) -> Dict[int, int]:
        """Calculate topic distribution based on clusters"""
        return dict(Counter(clusters))

    def _identify_trending_topics(self, df: pd.DataFrame) -> List[Dict]:
        """Identify topics that are trending up in recent interactions"""
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_df = df[df['timestamp'] > recent_cutoff]
        
        if len(recent_df) == 0:
            return []

        # Compare topic frequencies
        return self._compare_topic_frequencies(df, recent_df)

    def _calculate_confidence_trend(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate confidence score trends over time"""
        df['date'] = df['timestamp'].dt.date
        daily_confidence = df.groupby('date')['confidence'].mean()
        
        return [
            {"date": date.strftime("%Y-%m-%d"), "confidence": conf}
            for date, conf in daily_confidence.items()
        ]

    def _empty_insights(self) -> Dict:
        """Return empty insights structure when no data is available"""
        return {
            "summary": {
                "total_interactions": 0,
                "unique_users": 0,
                "avg_confidence": 0,
                "total_queries_today": 0,
                "active_hours": []
            },
            "usage_patterns": {
                "peak_hours": [],
                "busiest_days": [],
                "usage_trends": [],
                "session_analysis": {}
            },
            "common_topics": {
                "frequent_questions": [],
                "topic_distribution": {},
                "trending_topics": []
            },
            "performance_metrics": {
                "response_quality": {
                    "high_confidence_rate": 0,
                    "avg_confidence": 0,
                    "confidence_trend": []
                },
                "efficiency": {
                    "response_times": {},
                    "resolution_rate": 0
                }
            },
            "improvement_suggestions": []
        }

# Create singleton instance
analyzer = InsightsAnalyzer()

# Export functions for easier access
def get_analytics(company_id: str, days: int = 30) -> Dict:
    """Get comprehensive analytics for a company"""
    return analyzer.get_company_insights(company_id, days)

def get_realtime_metrics(company_id: str) -> Dict:
    """Get real-time performance metrics"""
    return {
        "online_users": analyzer._calculate_online_users(company_id),
        "response_times": analyzer._calculate_current_response_times(company_id),
        "active_sessions": analyzer._get_active_sessions(company_id)
    }