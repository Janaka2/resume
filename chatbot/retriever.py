import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import QA_PATH, FACTS_PATH, PROFILE_DOC, RESUME_SOURCE_URL
from utils import load_json, safe_read_text, fetch_resume_text_from_url

class Retriever:
    def __init__(self):
        self.qa = []
        self.docs = []
        self.doc_titles = []
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = None

    def build_corpus(self):
        self.qa = load_json(QA_PATH, [])
        facts = load_json(FACTS_PATH, {})
        facts_lines = []
        if facts:
            facts_lines.extend([facts.get("title", ""), facts.get("location", "")])
            facts_lines.extend(facts.get("summary", []))
            facts_lines.extend(facts.get("contact", []))
        facts_text = "\n".join([l for l in facts_lines if l])

        docs_texts = []
        resume_text = safe_read_text(PROFILE_DOC)
        if not resume_text and RESUME_SOURCE_URL:
            resume_text = fetch_resume_text_from_url(RESUME_SOURCE_URL)
        if resume_text:
            docs_texts.append(resume_text)
            self.doc_titles.append("profile_resume.txt")

        units = []
        titles = []

        if facts_text.strip():
            units.append(f"Profile facts:\n{facts_text}")
            titles.append("profile_facts")

        for item in self.qa:
            q = item.get("q", "").strip()
            a = item.get("a", "").strip()
            if q or a:
                units.append(f"Q: {q}\nA: {a}")
                titles.append(f"qa::{q[:60]}")

        for i, txt in enumerate(docs_texts):
            units.append(txt)
            titles.append(self.doc_titles[i])

        if not units:
            units = ["Janaka is a Senior Full-Stack Java Engineer in Switzerland."]
            titles = ["placeholder"]

        self.docs = units
        try:
            self.matrix = self.vectorizer.fit_transform(self.docs)
        except Exception as e:
            print("Vectorizer fit error:", e)
            self.docs = units
            self.matrix = None
        return titles

    def search(self, query: str, k: int = 6):
        if self.matrix is None:
            return []
        try:
            qv = self.vectorizer.transform([query])
            sims = cosine_similarity(qv, self.matrix).ravel()
            idx = np.argsort(-sims)[:k]
            return [self.docs[i] for i in idx if sims[i] > 0.01]
        except Exception as e:
            print("search error:", e)
            return []

# Singleton retriever
retriever = Retriever()
retriever.build_corpus()
