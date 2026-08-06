
import torch
import pickle
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report
)

from torch.utils.data import DataLoader
from transformers import DistilBertTokenizerFast

from model import MultiTaskModel
from dataset import FashionDataset

# =========================
# DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/new_data1.csv")

df = df[[
    "productDisplayName",
    "baseColour",
    "usage",
    "articleType"
]]

df = df.dropna().reset_index(drop=True)

df["text"] = df["productDisplayName"].astype(str)

# =========================
# LOAD ENCODERS
# =========================
color_enc = pickle.load(open("color_encoder.pkl", "rb"))
usage_enc = pickle.load(open("usage_encoder.pkl", "rb"))
type_enc = pickle.load(open("type_encoder.pkl", "rb"))

# encode labels
df["baseColour"] = color_enc.transform(df["baseColour"])
df["usage"] = usage_enc.transform(df["usage"])
df["articleType"] = type_enc.transform(df["articleType"])

# =========================
# DATASET
# =========================
test_dataset = FashionDataset(df)

test_loader = DataLoader(
    test_dataset,
    batch_size=16,
    shuffle=False
)

# =========================
# LOAD MODEL
# =========================
model = MultiTaskModel(
    n_color=len(color_enc.classes_),
    n_usage=len(usage_enc.classes_),
    n_type=len(type_enc.classes_)
)

model.load_state_dict(
    torch.load("fashion_model.pth", map_location=device)
)

model.to(device)
model.eval()

# =========================
# STORE RESULTS
# =========================
true_colors = []
pred_colors = []

true_usage = []
pred_usage = []

true_types = []
pred_types = []

# =========================
# EVALUATION LOOP
# =========================
with torch.no_grad():

    for batch in test_loader:

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        color_logits, usage_logits, type_logits = model(
            input_ids,
            attention_mask
        )

        color_preds = torch.argmax(color_logits, dim=1)
        usage_preds = torch.argmax(usage_logits, dim=1)
        type_preds = torch.argmax(type_logits, dim=1)

        true_colors.extend(labels[:, 0].cpu().numpy())
        pred_colors.extend(color_preds.cpu().numpy())

        true_usage.extend(labels[:, 1].cpu().numpy())
        pred_usage.extend(usage_preds.cpu().numpy())

        true_types.extend(labels[:, 2].cpu().numpy())
        pred_types.extend(type_preds.cpu().numpy())

# =========================
# METRICS FUNCTION
# =========================
def evaluate_task(true_labels, pred_labels, task_name):

    accuracy = accuracy_score(true_labels, pred_labels)

    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels,
        pred_labels,
        average="weighted"
    )

    print(f"\n===== {task_name} =====")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-Score : {f1:.4f}")

# =========================
# RESULTS
# =========================
evaluate_task(true_colors, pred_colors, "Base Colour")

evaluate_task(true_usage, pred_usage, "Usage")

evaluate_task(true_types, pred_types, "Article Type")

print("\nEvaluation Completed!")

