from sentence_transformers import SentenceTransformer
import json
import numpy as np

def get_vector_as_str(model: SentenceTransformer, text: str) -> str:
    """
        This function turns <text> into a vector using <model>, then returns
        its json string representation.
    """

    vector = model.encode(text)
    return json.dumps(vector.tolist())

def get_vector_str_as_array(vector_str: str) -> np.ndarray:
    """
        Convert a JSON stringified vector back into a np array.
    """

    return np.array(json.loads(vector_str), dtype=np.float32)
