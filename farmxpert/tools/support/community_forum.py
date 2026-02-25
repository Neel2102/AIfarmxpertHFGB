from typing import Dict, Any, List, Optional
import random

class CommunityForumTool:
    """
    Tool to interact with a simulated farmer community forum.
    Provides trending topics, expert answers, and community sentiment.
    """
    
    def get_trending_topics(self, category: str = "general") -> List[Dict[str, Any]]:
        """Get trending discussions in the community"""
        topics = [
            {"id": 1, "title": "Best organic pesticide for cotton?", "views": 1205, "replies": 45, "tags": ["cotton", "organic", "pest"]},
            {"id": 2, "title": "Wheat prices dropping in Rajkot mandi", "views": 890, "replies": 120, "tags": ["wheat", "market", "price"]},
            {"id": 3, "title": "How to apply subsidy for drip irrigation?", "views": 3400, "replies": 15, "tags": ["subsidy", "irrigation", "govt"]},
            {"id": 4, "title": "Yellow leaves on groundnut plants - help!", "views": 560, "replies": 8, "tags": ["groundnut", "disease", "help"]},
            {"id": 5, "title": "Review of new Mahindra tractor model", "views": 2100, "replies": 67, "tags": ["machinery", "review"]}
        ]
        
        # Filter (mock)
        if category != "general":
            return [t for t in topics if category in t["tags"] or category.lower() in t["title"].lower()]
        
        return topics

    def search_similar_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search for similar resolved issues"""
        # specialized mock responses for common queries
        if "yellow" in query.lower() or "leaf" in query.lower():
            return [{
                "question": "Yellowing leaves in wheat",
                "accepted_answer": "This is likely Nitrogen deficiency. Apply Urea or check if watering is excessive.",
                "expert_verified": True,
                "votes": 56
            }]
        elif "price" in query.lower():
            return [{
                "question": "When will onion prices rise?",
                "accepted_answer": "Market trends suggest a rise in late November due to export ban lifting.",
                "expert_verified": False,
                "votes": 120
            }]
            
        return []

    def post_question(self, user_id: str, title: str, content: str) -> Dict[str, Any]:
        """Simulate posting a question to the forum"""
        return {
            "success": True,
            "post_id": random.randint(1000, 9999),
            "status": "published",
            "message": "Your question has been posted to the 'Ask an Expert' section."
        }
