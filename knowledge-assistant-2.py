import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pytesseract
from pdf2image import convert_from_path
import docx
import os
from typing import List, Dict, Union
import ezdxf
import base64

class EngineeringKnowledgeAssistant:
    def __init__(self):
        self.knowledge_base = pd.DataFrame(columns=[
            'topic', 'problem', 'solution', 'expert', 'date_added', 
            'attachments', 'cad_references', 'validation_status', 
            'validators'
        ])
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        
    def add_knowledge(self, topic: str, problem: str, solution: str, 
                     expert: str, attachments: List[str] = None, 
                     cad_references: List[str] = None):
        """Add new knowledge to the database with support for attachments and CAD references"""
        new_entry = {
            'topic': topic,
            'problem': problem,
            'solution': solution,
            'expert': expert,
            'date_added': pd.Timestamp.now(),
            'attachments': attachments if attachments else [],
            'cad_references': cad_references if cad_references else [],
            'validation_status': 'pending',
            'validators': []
        }
        self.knowledge_base = pd.concat([self.knowledge_base, pd.DataFrame([new_entry])], ignore_index=True)
        self._update_vectors()
        
    def extract_knowledge_from_documents(self, file_path: str) -> Dict[str, str]:
        """Extract knowledge from various document types"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_ext == '.docx':
            return self._extract_from_docx(file_path)
        elif file_ext in ['.dwg', '.dxf']:
            return self._extract_from_cad(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_from_pdf(self, file_path: str) -> Dict[str, str]:
        """Extract text content from PDF files"""
        images = convert_from_path(file_path)
        text_content = []
        
        for image in images:
            text = pytesseract.image_to_string(image)
            text_content.append(text)
            
        return self._analyze_extracted_content('\n'.join(text_content))
    
    def _extract_from_docx(self, file_path: str) -> Dict[str, str]:
        """Extract text content from Word documents"""
        doc = docx.Document(file_path)
        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return self._analyze_extracted_content(content)
    
    def _extract_from_cad(self, file_path: str) -> Dict[str, str]:
        """Extract metadata and annotations from CAD files"""
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        annotations = []
        for entity in msp:
            if entity.dxftype() == 'MTEXT':
                annotations.append(entity.text)
                
        return self._analyze_extracted_content('\n'.join(annotations))
    
    def _analyze_extracted_content(self, content: str) -> Dict[str, str]:
        """Analyze extracted content to identify problems and solutions"""
        # Simple keyword-based analysis - could be enhanced with NLP
        sections = {
            'topic': '',
            'problem': '',
            'solution': ''
        }
        
        keywords = {
            'topic': ['subject:', 'topic:', 'regarding:'],
            'problem': ['issue:', 'problem:', 'challenge:'],
            'solution': ['solution:', 'resolution:', 'approach:']
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower()
            
            for section, section_keywords in keywords.items():
                if any(keyword in line_lower for keyword in section_keywords):
                    current_section = section
                    sections[section] = line.split(':', 1)[1].strip()
                    break
                    
            if current_section and line.strip() and ':' not in line_lower:
                sections[current_section] += ' ' + line.strip()
                
        return sections
    
    def validate_knowledge(self, entry_id: int, validator: str, status: str) -> None:
        """Allow collaborative validation of knowledge entries"""
        if entry_id < len(self.knowledge_base):
            if validator not in self.knowledge_base.at[entry_id, 'validators']:
                self.knowledge_base.at[entry_id, 'validators'].append(validator)
                
            # Update status if we have enough validators
            if len(self.knowledge_base.at[entry_id, 'validators']) >= 2:
                self.knowledge_base.at[entry_id, 'validation_status'] = status
    
    def integrate_with_cad(self, cad_file: str, knowledge_id: int) -> None:
        """Link knowledge entries with CAD drawings"""
        doc = ezdxf.readfile(cad_file)
        
        # Add a new layer for knowledge references
        if 'Knowledge_Links' not in doc.layers:
            doc.layers.new('Knowledge_Links')
            
        # Add reference to modelspace
        msp = doc.modelspace()
        msp.add_mtext(
            f"Knowledge ID: {knowledge_id}\n"
            f"Topic: {self.knowledge_base.at[knowledge_id, 'topic']}",
            dxfattribs={
                'layer': 'Knowledge_Links',
                'height': 2.5
            }
        )
        
        # Save the modified CAD file
        doc.save()
        
    def query_knowledge(self, question: str, n_results: int = 3) -> List[Dict]:
        """Enhanced query function with validation status"""
        if self.vectors is None or len(self.knowledge_base) == 0:
            return []
            
        query_vector = self.vectorizer.transform([question])
        similarities = cosine_similarity(query_vector, self.vectors)
        top_indices = np.argsort(similarities[0])[-n_results:][::-1]
        
        results = []
        for idx in top_indices:
            entry = self.knowledge_base.iloc[idx]
            results.append({
                'topic': entry['topic'],
                'problem': entry['problem'],
                'solution': entry['solution'],
                'expert': entry['expert'],
                'validation_status': entry['validation_status'],
                'validators': entry['validators'],
                'attachments': entry['attachments'],
                'cad_references': entry['cad_references'],
                'similarity_score': similarities[0][idx]
            })
            
        return results
        
    def _update_vectors(self):
        """Update the TF-IDF vectors for the knowledge base"""
        combined_text = self.knowledge_base.apply(
            lambda x: f"{x['topic']} {x['problem']} {x['solution']}", axis=1
        )
        self.vectors = self.vectorizer.fit_transform(combined_text)
    
    def export_knowledge(self, filepath: str) -> None:
        """Export knowledge base to CSV"""
        self.knowledge_base.to_csv(filepath, index=False)
    
    def import_knowledge(self, filepath: str) -> None:
        """Import knowledge base from CSV"""
        self.knowledge_base = pd.read_csv(filepath)
        self._update_vectors()
