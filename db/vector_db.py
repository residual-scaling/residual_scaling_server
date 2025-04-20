from rank_bm25 import BM25Okapi
from db.base_db import BaseDB
from config import db_hyperparameter


class VectorDB(BaseDB):
    def __init__(self):
        self.db = []
        self.tokenized_corpus = []
        self.bm25 = None
        self.k = db_hyperparameter["k"]
        self.bm25th = db_hyperparameter["bm25threshold"]

    def put(self, txt):
        print("[VectorDB] Adding to db...")
        self.db.append(txt)
        tokenized = self._tokenize(txt)
        self.tokenized_corpus.append(tokenized)
        self._update_bm25()
        print(f"[VectorDB] cur db size: {len(self.db)}")

    def get(self, query_txt):
        print("[VectorDB] Searching...")
        if not self.db:
            print("[VectorDB] db is empty")
            return []

        query_tokens = self._tokenize(query_txt)
        scores = self.bm25.get_scores(query_tokens)
        scored_docs = list(zip(scores, self.db))
        # print(f"[VectorDB] scored_docs len: {len(scored_docs)}")
        # print(f"[VectorDB] scored_docs: {scored_docs}")

        # Filter out documents with score lower than th
        scored_docs = [doc for doc in scored_docs if doc[0] >= self.bm25th]
        # print(f"[VectorDB] scored_docs len after filter: {len(scored_docs)}")
        # Sort by descending score, then ascending text for determinism
        scored_docs.sort(key=lambda x: (-x[0], x[1]))

        scored_docs = scored_docs[:self.k]
        scored_docs = [doc[1] for doc in scored_docs]
        return scored_docs

    def _tokenize(self, text):
        return text.lower().split()

    def _update_bm25(self):
        self.bm25 = BM25Okapi(self.tokenized_corpus)
