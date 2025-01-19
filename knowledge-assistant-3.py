import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class EngineeringKnowledgeAssistant:
    def __init__(self):
        self.knowledge_base = pd.DataFrame(columns=['topic', 'problem', 'solution', 'expert', 'date_added'])
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        
    def add_knowledge(self, topic, problem, solution, expert):
        """Add new knowledge to the database"""
        new_entry = {
            'topic': topic,
            'problem': problem,
            'solution': solution,
            'expert': expert,
            'date_added': pd.Timestamp.now()
        }
        self.knowledge_base = pd.concat([self.knowledge_base, pd.DataFrame([new_entry])], ignore_index=True)
        # Update vectors
        self._update_vectors()
        
    def query_knowledge(self, question, n_results=3):
        """Query the knowledge base for similar problems/solutions"""
        if self.vectors is None or len(self.knowledge_base) == 0:
            return []
            
        # Vectorize the query
        query_vector = self.vectorizer.transform([question])
        
        # Calculate similarity
        similarities = cosine_similarity(query_vector, self.vectors)
        
        # Get top N results
        top_indices = np.argsort(similarities[0])[-n_results:][::-1]
        
        results = []
        for idx in top_indices:
            entry = self.knowledge_base.iloc[idx]
            results.append({
                'topic': entry['topic'],
                'problem': entry['problem'],
                'solution': entry['solution'],
                'expert': entry['expert'],
                'similarity_score': similarities[0][idx]
            })
            
        return results
        
    def _update_vectors(self):
        """Update the TF-IDF vectors for the knowledge base"""
        combined_text = self.knowledge_base.apply(
            lambda x: f"{x['topic']} {x['problem']} {x['solution']}", axis=1
        )
        self.vectors = self.vectorizer.fit_transform(combined_text)
    
    def export_knowledge(self, filepath):
        """Export knowledge base to CSV"""
        self.knowledge_base.to_csv(filepath, index=False)
    
    def import_knowledge(self, filepath):
        """Import knowledge base from CSV"""
        self.knowledge_base = pd.read_csv(filepath)
        self._update_vectors()
