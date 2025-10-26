from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass
from google.adk.tools import FunctionTool


# Minimal in-memory vector store (you can replace with FAISS, etc.)
@dataclass
class Doc:
    id: str
    text: str
    vec: np.ndarray


class TinyStore:
    def __init__(self):
        self.docs: List[Doc] = []


    def add(self, id: str, text: str, vec: np.ndarray):
        self.docs.append(Doc(id=id, text=text, vec=vec))


    def search(self, qvec: np.ndarray, k: int = 5):
        if not self.docs:
            return []
        sims = [float(qvec @ d.vec / (np.linalg.norm(qvec) * np.linalg.norm(d.vec) + 1e-9)) for d in self.docs]
        topk = np.argsort(sims)[::-1][:k]
        return [(self.docs[i], sims[i]) for i in topk]


STORE = TinyStore()


# Embeddings: simple bag-of-words toy to avoid external deps. Replace with real embeddings as needed.
def embed(text: str) -> np.ndarray:
    tokens = text.lower().split()
    vocab = {}
    for t in tokens:
        vocab[t] = vocab.get(t, 0) + 1
    vec = np.array([v for _, v in sorted(vocab.items())], dtype=float)
    if vec.size == 0:
        vec = np.zeros(1)
    return vec


async def rag_add(id: str, text: str) -> Dict[str, Any]:
    STORE.add(id, text, embed(text))
    return {"status": "ok", "count": len(STORE.docs)}


async def rag_query(query: str, k: int = 5) -> Dict[str, Any]:
    results = STORE.search(embed(query), k=k)
    return {"matches": [{"id": d.id, "score": s, "text": d.text} for d, s in results]}


RagAddTool = FunctionTool(func=rag_add)
RagQueryTool = FunctionTool(func=rag_query)