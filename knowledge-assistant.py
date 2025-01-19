import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import pytesseract
from pdf2image import convert_from_path
import docx
import os
from typing import List, Dict, Union, Optional
import ezdxf
import json
from datetime import datetime
import difflib
from dataclasses import dataclass
import threading
import queue
from git import Repo

@dataclass
class KnowledgeVersion:
    """Track versions of knowledge entries"""
    content: Dict
    timestamp: datetime
    author: str
    commit_message: str
    version_id: str

class ProjectManagementIntegration:
    """Integration with project management systems"""
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        
    def link_to_project(self, knowledge_id: str, project_id: str) -> None:
        """Link knowledge entry to project"""
        # Implementation would depend on specific PM system API
        pass
        
    def sync_project_status(self, knowledge_id: str) -> Dict:
        """Get latest project status"""
        # Implementation would depend on specific PM system API
        pass
        
    def create_task(self, title: str, description: str, assignee: str) -> str:
        """Create task in PM system"""
        # Implementation would depend on specific PM system API
        pass

class CollaborationHub:
    """Real-time collaboration management"""
    def __init__(self):
        self.active_sessions = {}
        self.message_queue = queue.Queue()
        self.lock = threading.Lock()
        
    def start_editing_session(self, knowledge_id: str, user: str) -> str:
        """Start collaborative editing session"""
        session_id = f"{knowledge_id}-{datetime.now().timestamp()}"
        with self.lock:
            self.active_sessions[session_id] = {
                'knowledge_id': knowledge_id,
                'users': [user],
                'locked_by': user
            }
        return session_id
        
    def join_session(self, session_id: str, user: str) -> bool:
        """Join existing editing session"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['users'].append(user)
                return True
        return False
        
    def push_update(self, session_id: str, user: str, update: Dict) -> None:
        """Push update to collaboration session"""
        if session_id in self.active_sessions:
            self.message_queue.put({
                'session_id': session_id,
                'user': user,
                'update': update,
                'timestamp': datetime.now()
            })
            
    def get_updates(self, session_id: str) -> List[Dict]:
        """Get pending updates for session"""
        updates = []
        while not self.message_queue.empty():
            update = self.message_queue.get()
            if update['session_id'] == session_id:
                updates.append(update)
        return updates

class EngineeringKnowledgeAssistant:
    def __init__(self, repo_path: str = "./knowledge_repo"):
        super().__init__()
        self.knowledge_base = pd.DataFrame(columns=[
            'topic', 'problem', 'solution', 'expert', 'date_added', 
            'attachments', 'cad_references', 'validation_status', 
            'validators', 'project_links', 'categories'
        ])
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        self.classifier = RandomForestClassifier()
        self.version_history = {}
        self.repo = Repo.init(repo_path)
        self.collaboration_hub = CollaborationHub()
        self.project_mgmt = None
        
    def initialize_project_mgmt(self, api_key: str, base_url: str) -> None:
        """Initialize project management integration"""
        self.project_mgmt = ProjectManagementIntegration(api_key, base_url)
        
    def train_classifier(self, training_data: pd.DataFrame) -> None:
        """Train the problem classifier"""
        X = self.vectorizer.fit_transform(
            training_data['problem'] + ' ' + training_data['solution']
        )
        y = training_data['categories']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.classifier.fit(X_train, y_train)
        print(f"Classifier accuracy: {self.classifier.score(X_test, y_test)}")
        
    def predict_categories(self, problem: str, solution: str) -> List[str]:
        """Predict categories for new knowledge entries"""
        text = f"{problem} {solution}"
        vector = self.vectorizer.transform([text])
        return self.classifier.predict(vector)
        
    def create_version(self, knowledge_id: int, author: str, 
                      commit_message: str) -> str:
        """Create new version of knowledge entry"""
        entry = self.knowledge_base.iloc[knowledge_id].to_dict()
        version = KnowledgeVersion(
            content=entry,
            timestamp=datetime.now(),
            author=author,
            commit_message=commit_message,
            version_id=f"v{len(self.version_history.get(knowledge_id, []))}"
        )
        
        if knowledge_id not in self.version_history:
            self.version_history[knowledge_id] = []
            
        self.version_history[knowledge_id].append(version)
        
        # Save to Git repository
        entry_path = f"knowledge_{knowledge_id}.json"
        with open(entry_path, 'w') as f:
            json.dump(entry, f)
            
        self.repo.index.add([entry_path])
        self.repo.index.commit(commit_message)
        
        return version.version_id
        
    def get_version_history(self, knowledge_id: int) -> List[KnowledgeVersion]:
        """Get version history for knowledge entry"""
        return self.version_history.get(knowledge_id, [])
        
    def compare_versions(self, knowledge_id: int, 
                        version1: str, version2: str) -> Dict[str, List[str]]:
        """Compare two versions of a knowledge entry"""
        versions = self.get_version_history(knowledge_id)
        v1 = next(v for v in versions if v.version_id == version1)
        v2 = next(v for v in versions if v.version_id == version2)
        
        diff = {}
        for key in v1.content.keys():
            if isinstance(v1.content[key], str) and isinstance(v2.content[key], str):
                diff[key] = list(difflib.unified_diff(
                    v1.content[key].splitlines(),
                    v2.content[key].splitlines()
                ))
                
        return diff
        
    def start_collaboration(self, knowledge_id: int, user: str) -> str:
        """Start collaborative editing session"""
        return self.collaboration_hub.start_editing_session(str(knowledge_id), user)
        
    def join_collaboration(self, session_id: str, user: str) -> bool:
        """Join collaborative editing session"""
        return self.collaboration_hub.join_session(session_id, user)
        
    def push_collaborative_update(self, session_id: str, user: str, 
                                update: Dict) -> None:
        """Push update in collaborative session"""
        self.collaboration_hub.push_update(session_id, user, update)
        
    def get_collaborative_updates(self, session_id: str) -> List[Dict]:
        """Get updates from collaborative session"""
        return self.collaboration_hub.get_updates(session_id)
        
    def link_to_project(self, knowledge_id: int, project_id: str) -> None:
        """Link knowledge entry to project"""
        if self.project_mgmt:
            self.project_mgmt.link_to_project(str(knowledge_id), project_id)
            if 'project_links' not in self.knowledge_base.at[knowledge_id]:
                self.knowledge_base.at[knowledge_id, 'project_links'] = []
            self.knowledge_base.at[knowledge_id, 'project_links'].append(project_id)
            
    def create_task_from_knowledge(self, knowledge_id: int, 
                                 assignee: str) -> str:
        """Create task from knowledge entry"""
        if self.project_mgmt:
            entry = self.knowledge_base.iloc[knowledge_id]
            task_id = self.project_mgmt.create_task(
                title=f"Review: {entry['topic']}",
                description=f"Problem: {entry['problem']}\nSolution: {entry['solution']}",
                assignee=assignee
            )
            return task_id
        return None

    def add_knowledge(self, topic: str, problem: str, solution: str, 
                     expert: str, attachments: List[str] = None, 
                     cad_references: List[str] = None):
        """Enhanced add_knowledge with automatic categorization"""
        categories = self.predict_categories(problem, solution)
        new_entry = {
            'topic': topic,
            'problem': problem,
            'solution': solution,
            'expert': expert,
            'date_added': pd.Timestamp.now(),
            'attachments': attachments if attachments else [],
            'cad_references': cad_references if cad_references else [],
            'validation_status': 'pending',
            'validators': [],
            'project_links': [],
            'categories': categories
        }
        
        self.knowledge_base = pd.concat(
            [self.knowledge_base, pd.DataFrame([new_entry])], 
            ignore_index=True
        )
        self._update_vectors()
        
        # Create initial version
        knowledge_id = len(self.knowledge_base) - 1
        self.create_version(
            knowledge_id=knowledge_id,
            author=expert,
            commit_message="Initial knowledge entry"
        )
