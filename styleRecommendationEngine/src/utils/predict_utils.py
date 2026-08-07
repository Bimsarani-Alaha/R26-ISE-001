import os
import torch
import pickle
import pandas as pd
import numpy as np

from transformers import DistilBertTokenizerFast
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.model import MultiTaskModel

ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ARTIFACTS_DIR = os.path.join(ENGINE_DIR, "artifacts")
DATA_DIR = os.path.join(ENGINE_DIR, "data")

_loaded = None


def _ensure_loaded():
    global _loaded
    if _loaded is not None:
        return _loaded

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # TOKENIZER
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

    # LOAD ENCODERS
    color_enc = pickle.load(open(os.path.join(ARTIFACTS_DIR, "color_encoder.pkl"), "rb"))
    usage_enc = pickle.load(open(os.path.join(ARTIFACTS_DIR, "usage_encoder.pkl"), "rb"))
    type_enc = pickle.load(open(os.path.join(ARTIFACTS_DIR, "type_encoder.pkl"), "rb"))

    # LOAD MODEL
    model = MultiTaskModel(
        n_color=len(color_enc.classes_),
        n_usage=len(usage_enc.classes_),
        n_type=len(type_enc.classes_),
    )

    model.load_state_dict(
        torch.load(
            os.path.join(ARTIFACTS_DIR, "fashion_model.pth"),
            map_location=device,
        )
    )

    model.to(device)
    model.eval()

    # LOAD DATASET
    products_df = pd.read_csv(os.path.join(DATA_DIR, "new_data2.csv"))
    products_df = products_df.dropna().reset_index(drop=True)

    # BETTER SEARCH TEXT
    products_df["combined_text"] = (
        products_df["gender"].astype(str) + " " +
        products_df["articleType"].astype(str) + " " +
        products_df["baseColour"].astype(str) + " " +
        products_df["usage"].astype(str)
    )

    # EMBEDDING MODEL
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # PRECOMPUTE PRODUCT EMBEDDINGS
    product_embeddings = embedding_model.encode(
        products_df["combined_text"].tolist(),
        convert_to_numpy=True,
    )

    _loaded = {
        "device": device,
        "tokenizer": tokenizer,
        "color_enc": color_enc,
        "usage_enc": usage_enc,
        "type_enc": type_enc,
        "model": model,
        "products_df": products_df,
        "embedding_model": embedding_model,
        "product_embeddings": product_embeddings,
    }

    return _loaded


# PREDICTION FUNCTION
def predict(text):
    state = _ensure_loaded()

    enc = state["tokenizer"](
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128,
    )

    input_ids = enc["input_ids"].to(state["device"])
    attention_mask = enc["attention_mask"].to(state["device"])

    with torch.no_grad():
        color_logits, usage_logits, type_logits = state["model"](
            input_ids,
            attention_mask,
        )

        color_pred = torch.argmax(color_logits, dim=1).item()
        usage_pred = torch.argmax(usage_logits, dim=1).item()
        type_pred = torch.argmax(type_logits, dim=1).item()

    return {
        "color": state["color_enc"].inverse_transform([color_pred])[0],
        "usage": state["usage_enc"].inverse_transform([usage_pred])[0],
        "articleType": state["type_enc"].inverse_transform([type_pred])[0],
    }


# RECOMMENDATION FUNCTION
def recommend_products(user_text, top_n=8):
    state = _ensure_loaded()

    # USER EMBEDDING
    user_embedding = state["embedding_model"].encode(
        [user_text],
        convert_to_numpy=True,
    )

    # COSINE SIMILARITY
    similarities = cosine_similarity(
        user_embedding,
        state["product_embeddings"],
    )[0]

    # TOP RESULTS
    top_indices = np.argsort(similarities)[::-1][:top_n]

    recommendations = state["products_df"].iloc[top_indices].copy()
    recommendations["similarity"] = similarities[top_indices]

    return recommendations
