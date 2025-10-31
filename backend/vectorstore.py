# vectorstore.py
import faiss
import numpy as np
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"   # 避免 Metal 报错
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

import pickle
from typing import List, Tuple

# We'll store:
# - a FAISS index stored to disk
# - metadata list (parallel to vectors) saved as pickle: list of dicts {doc_id, chunk_id, text}

class SimpleVectorStore:
    def __init__(self, dim: int, index_path="vector.index", meta_path="meta.pkl"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self._load()

    def _load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatIP(self.dim)  # inner product cosine-like if vectors normalized
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.metadata = []

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def add(self, vectors: List[List[float]], metadatas: List[dict]):
        vecs = np.array(vectors).astype("float32")
        # normalize to unit length for cosine similarity via inner product
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms
        self.index.add(vecs)
        self.metadata.extend(metadatas)
        self._save()

    def search(self, query_vec: List[float], top_k: int = 4) -> List[Tuple[dict, float]]:
        q = np.array([query_vec]).astype("float32")
        # normalize
        q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)
        D, I = self.index.search(q, top_k)
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            results.append((self.metadata[idx], float(score)))
        return results
