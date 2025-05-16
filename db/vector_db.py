from rank_bm25 import BM25Okapi
from db.base_db import BaseDB
from config import db_hyperparameter
from rsprotocol.protocol import RSMsgDelimiter
from util import log_flush
import json
import os


class VectorDB(BaseDB):
    def __init__(self, port: int):
        self.port = port

        # data base
        self.db = []
        self.tokenized_corpus = []

        # bm25 similarity search setting
        self.bm25 = None
        self.k = db_hyperparameter["k"]
        self.bm25th = db_hyperparameter["bm25threshold"]

        # set up logger
        self.fileIO = open(f'./log/vector_{self.port}.log', 'a')
        log_flush(self.fileIO, "===============================")

    def put(self, txt):
        log_flush(self.fileIO, "[VectorDB] Adding to db...")
        self.db.append(txt)
        tokenized = self._tokenize(txt)
        self.tokenized_corpus.append(tokenized)
        self._update_bm25()
        log_flush(self.fileIO, f"[VectorDB] save done, cur db size: {len(self.db)}, saved txt: ({txt})")

    def get(self, query_txt):
        log_flush(self.fileIO, "[VectorDB] Searching...")
        if not self.db:
            log_flush(self.fileIO, "[VectorDB] db is empty")
            return [], []

        query_tokens = self._tokenize(query_txt)
        scores = self.bm25.get_scores(query_tokens)
        # print(f"[VectorDB] scores: {scores}")
        scored_docs = list(zip(scores, self.db))

        # Filter out documents with score lower than th
        scored_docs = [doc for doc in scored_docs if doc[0] >= self.bm25th]
        qualified_size = len(scored_docs)

        # Sort by descending score, then ascending text for determinism
        scored_docs.sort(key=lambda x: (-x[0], x[1]))

        scored_docs = scored_docs[:self.k]
        log_flush(self.fileIO, f"[VectorDB] search done, count of bm25 score higher than ({self.bm25th}) is ({qualified_size}), original query: ({query_txt}), scored_docs: ({scored_docs})")

        scores = [sd[0] for sd in scored_docs]
        scores = [float(s) for s in scores]
        docs = [sd[1] for sd in scored_docs]
        return scores, docs
    
    def get_plain(self, query_txt):
        _, docs = self.get(query_txt)
        return docs
    
    def get_with_score_str(self, query_txt):
        scores, docs = self.get(query_txt)
        scores_str = RSMsgDelimiter.RS_SCORE_SEPERATOR.join([str(s) for s in scores])
        return [scores_str] + docs

    def _tokenize(self, text):
        return text.lower().split()

    def _update_bm25(self):
        self.bm25 = BM25Okapi(self.tokenized_corpus)


    def save(self, path: str = "./storage/"):
        file_path = path + f"vectordb_{self.port}.json"
        log_flush(self.fileIO, f"[VectorDB] Saved db to {file_path}")
        saved_data = {"db": self.db, "tokenized_corpus": self.tokenized_corpus}
        with open(file_path, 'w') as fp:
            json.dump(saved_data, fp)

    def exist_backup(self, path: str = "./storage/"):
        file_path = path + f"vectordb_{self.port}.json"
        return os.path.isfile(file_path)

    def load(self, path: str = "./storage/"):
        if not self.exist_backup(path):
            raise Exception(f"In VectorDB.load(), load file with path {path} and port {self.port} does not exist.")
        file_path = path + f"vectordb_{self.port}.json"
        log_flush(self.fileIO, f"[VectorDB] Load db from {file_path}")
        with open(file_path) as f:
            loaded_data = json.load(f)
            assert len(loaded_data["db"]) == len(loaded_data["tokenized_corpus"])
            if len(loaded_data["db"]) == 0:
                return
            self.db, self.tokenized_corpus = loaded_data["db"], loaded_data["tokenized_corpus"]
        # update bm25
        self._update_bm25()
