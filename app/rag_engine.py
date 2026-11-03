import os
import glob
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGEngine:
    def __init__(self, knowledge_base_dir: str = None):
        if knowledge_base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.kb_dir = os.path.join(base_dir, "knowledge_base")
        else:
            self.kb_dir = knowledge_base_dir

        self.documents: List[Dict[str, str]] = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self._load_and_index()

    def _load_and_index(self):
        """Loads all markdown files, chunks by headers, and indexes them."""
        doc_files = glob.glob(os.path.join(self.kb_dir, "*.md"))
        chunks = []

        for filepath in doc_files:
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Split into logical sections by markdown header
            sections = content.split("\n## ")
            for i, sec in enumerate(sections):
                text = sec.strip()
                if not text:
                    continue
                if i > 0:
                    text = "## " + text
                chunks.append({
                    "source": filename,
                    "content": text
                })

        self.documents = chunks
        if self.documents:
            corpus = [doc["content"] for doc in self.documents]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Finds top-k most relevant knowledge base chunks."""
        if not self.documents or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Sort indices by highest score
        ranked_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            # Only return chunks with positive relevance
            if score > 0.05:
                results.append({
                    "source": self.documents[idx]["source"],
                    "content": self.documents[idx]["content"],
                    "score": round(score, 3)
                })

        return results

# Singleton instance
rag_engine = RAGEngine()
