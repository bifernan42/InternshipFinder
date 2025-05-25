from loguru import logger
from sentence_transformers import SentenceTransformer
import sqlite3
from typing import List, Iterator
from utils.vectorize import get_vector_str_as_array
from sklearn.metrics.pairwise import cosine_similarity

def k_search(model: SentenceTransformer, conn: sqlite3.Connection, query: str, k=10) -> List:
    """
        This function returns the <k> most relevant offers based on <query>
    """

    query_vector = model.encode(query)
    cursor = conn.cursor()
    offers = cursor.execute("SELECT * FROM Offers").fetchall()
    score_board = [
        (
            offer[0], cosine_similarity(
                query_vector.reshape(1, -1),
                get_vector_str_as_array(offer[17]).reshape(1, -1))[0][0]
        )
        for offer in offers
    ]
    score_board.sort(key=lambda x: x[1], reverse=True)
    result = [item[0] for item in score_board[:k]]
    cursor.execute(f'SELECT * FROM Offers where id in ({', '.join('?' * len(result))})', result)
    return cursor.fetchall()
