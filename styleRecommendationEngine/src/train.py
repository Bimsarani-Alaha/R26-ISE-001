import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from src.dataset import FashionDataset
from src.model import MultiTaskModel

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)

# LOAD DATASET
df = pd.read_csv("data/new_data2.csv")

# IMPORTANT
df = df.dropna().reset_index(drop=True)

# BETTER TEXT FOR TRAINING
df["text"] = (
    df["gender"].astype(str) + " " +
    df["articleType"].astype(str) + " " +
    df["baseColour"].astype(str) + " " +
    df["usage"].astype(str) 
)

# LABEL ENCODERS
color_enc = LabelEncoder()
usage_enc = LabelEncoder()
type_enc = LabelEncoder()

df["baseColour"] = color_enc.fit_transform(df["baseColour"])
df["usage"] = usage_enc.fit_transform(df["usage"])
df["articleType"] = type_enc.fit_transform(df["articleType"])

train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42
)

train_dataset = FashionDataset(train_df)

train_loader = DataLoader(
    train_dataset,
    batch_size=16,
    shuffle=True
)

model = MultiTaskModel(
    n_color=len(color_enc.classes_),
    n_usage=len(usage_enc.classes_),
    n_type=len(type_enc.classes_)
).to(device)

optimizer = AdamW(model.parameters(), lr=2e-5)

epochs = 3

for epoch in range(epochs):

    model.train()

    total_loss = 0

    for batch in train_loader:

        optimizer.zero_grad()

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        loss = model(
            input_ids,
            attention_mask,
            labels
        )

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1} Loss: {total_loss}")

# SAVE MODEL
torch.save(
    model.state_dict(),
    "artifacts/fashion_model.pth"
)

# SAVE ENCODERS
pickle.dump(
    color_enc,
    open("artifacts/color_encoder.pkl", "wb")
)

pickle.dump(
    usage_enc,
    open("artifacts/usage_encoder.pkl", "wb")
)

pickle.dump(
    type_enc,
    open("artifacts/type_encoder.pkl", "wb")
)

print("Training completed")