import torch
import torch.nn as nn
from transformers import DistilBertModel


class MultiTaskModel(nn.Module):
    def __init__(self, n_color, n_usage, n_type):
        super().__init__()

        self.bert = DistilBertModel.from_pretrained("distilbert-base-uncased")

        hidden = 768
        self.dropout = nn.Dropout(0.3)

        self.color_head = nn.Linear(hidden, n_color)
        self.usage_head = nn.Linear(hidden, n_usage)
        self.type_head = nn.Linear(hidden, n_type)

    def forward(self, input_ids, attention_mask, labels=None):

        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls = outputs.last_hidden_state[:, 0]

        x = self.dropout(cls)

        color_logits = self.color_head(x)
        usage_logits = self.usage_head(x)
        type_logits = self.type_head(x)

        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()

            loss = (
                loss_fn(color_logits, labels[:, 0]) +
                loss_fn(usage_logits, labels[:, 1]) +
                loss_fn(type_logits, labels[:, 2])
            )

            return loss

        return color_logits, usage_logits, type_logits