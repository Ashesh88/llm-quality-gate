import os
import glob
import re
from typing import List, Dict, Any

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class RAGEngine:
    def __init__(self, knowledge_base_dir: str = None):
        if knowledge_base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.kb_dir = os.path.join(base_dir, "knowledge_base")
        else:
            self.kb_dir = knowledge_base_dir

        self.documents: List[Dict[str, str]] = []
        self.vectorizer = TfidfVectorizer(stop_words='english') if SKLEARN_AVAILABLE else None
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
        if self.documents and SKLEARN_AVAILABLE:
            corpus = [doc["content"] for doc in self.documents]
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Finds top-k most relevant knowledge base chunks."""
        if not self.documents:
            return []

        if SKLEARN_AVAILABLE and self.tfidf_matrix is not None:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            ranked_indices = similarities.argsort()[::-1][:top_k]

            results = []
            for idx in ranked_indices:
                score = float(similarities[idx])
                if score > 0.05:
                    results.append({
                        "source": self.documents[idx]["source"],
                        "content": self.documents[idx]["content"],
                        "score": round(score, 3)
                    })
            if results:
                return results

        # Fallback keyword overlap
        q_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for doc in self.documents:
            d_words = set(re.findall(r"\w+", doc["content"].lower()))
            overlap = len(q_words.intersection(d_words)) / max(1, len(q_words))
            scored.append((overlap, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"source": d["source"], "content": d["content"], "score": round(s, 3)} for s, d in scored[:top_k]]

# Singleton instance
rag_engine = RAGEngine()
