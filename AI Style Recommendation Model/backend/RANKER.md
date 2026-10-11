# Fashion recommendation ranking

The recommendations endpoint uses Qwen to extract requirements, filters the
catalogue by gender, size and budget, and scores attribute matches as before.
FashionSigLIP then compares the original request with product images for up to 50
eligible products from each of the exact and alternative groups. Each group
returns its top five. Cartographer is the text-ranking fallback if visual scoring
is disabled or unavailable; rule-based ordering is the final fallback.
Products with zero rule-based relevance remain excluded from alternatives.

Cartographer uses concise product attributes as title-like text. Neither model can verify
missing attributes or move an alternative into the exact group. The existing
`match_score` remains the attribute score used by the UI. The optional
`reranker_score` is a raw relevance logit used only for ordering, not a probability
or a percentage. It is null when text reranking is skipped or unavailable.
`visual_score` is cosine similarity in [-1, 1], not a match probability. Products
with missing/corrupt images have a null visual score and follow visually scored
products within the same group; their original metadata order is preserved.

## FashionSigLIP local files and caching

The supplied `app/fashionclip` folder contains Marqo FashionSigLIP. This integration
uses only these files:

- `onnx/text_model.onnx`
- `onnx/vision_model.onnx`
- `tokenizer.json`
- `preprocessor_config.json`

It uses full-precision ONNX CPU inference and canonicalized text capped at 64
tokens, with RGB images resized and normalized according to the supplied
preprocessor. It does not execute the downloaded custom Python wrapper or make
Hub requests. Additional downloaded safetensors/quantized files are left intact.

The native encoders run in a persistent local Python worker process. This avoids
the observed Windows DLL conflict when ONNX Runtime imports after pandas, and a
worker failure falls back to text ranking. The process closes when the backend
exits normally. Each backend process has its own worker and model memory.

Image embeddings are computed on demand in batches, cached in memory and under
`AI Style Recommendation Model/.cache/fashionclip`, and reused across restarts.
Image path, size and modification time plus model/preprocessor signatures form
the cache key. Updated images are re-encoded; restart after changing model files.
Missing or unreadable images are skipped. Only files inside the catalogue image
directory are read. First-time searches take longer than cached searches.

| Variable | Default | Purpose |
| --- | --- | --- |
| `FASHIONCLIP_ENABLED` | `true` | Set `false` to return to Cartographer ranking. |
| `FASHIONCLIP_MODEL_PATH` | `backend/app/fashionclip` | Local model directory. |
| `FASHIONCLIP_CACHE_DIR` | `.cache/fashionclip` inside the AI Style project | Persisted image embeddings. |
| `FASHIONCLIP_BATCH_SIZE` | `8` | Images encoded per batch. |
| `FASHIONCLIP_THREADS` | `2` | ONNX CPU threads per encoder. |

The shared `RANKER_CANDIDATES_PER_GROUP` setting controls the metadata shortlist
for visual and text ranking. Visual search cannot recover a product excluded
from this shortlist. Increase it and measure latency if recall is insufficient.

## Setup

From this backend directory:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The local `app/RankerModel` directory must contain the original `config.json`,
`model.safetensors`, `tokenizer_config.json`, `tokenizer.json`, `vocab.txt`, and
`special_tokens_map.json` from:
https://huggingface.co/2013khansohail/cartographer-ecommerce-reranker-MiniLM-L6-v2

The configuration was retrieved from that repository, rather than inferred from
the weights. The loader uses Transformers directly to obtain raw classifier
logits, matching the checkpoint's Identity activation. It does not require
sentence-transformers or download files during requests.

## Settings

Set these environment variables before starting the backend:

| Variable | Default | Purpose |
| --- | --- | --- |
| `RANKER_ENABLED` | `true` | Set `false` to use only existing rule-based ranking. |
| `RANKER_MODEL_PATH` | `app/RankerModel` beside backend code | Local model directory; use an absolute path for overrides. |
| `RANKER_BATCH_SIZE` | `16` | Number of pairs per inference batch. |
| `RANKER_CANDIDATES_PER_GROUP` | `50` | Rule-ranked shortlist size per group, at least five. |

Inference runs on CPU with a 256-token pair limit. The model loads lazily once per
server process. Ranking runs in a worker thread so inference does not block the
async event loop. Load/inference failures log a warning and retain the complete
rule-based result; fix the files/dependencies and restart to retry.

## Validation

```powershell
python -m pytest -q
```

With the installed Windows PyTorch 2.13 runtime, pytest's fault handler can emit
a DLL access-violation diagnostic even when loading succeeds and all tests pass.
Preloading PyTorch before pytest avoids that observed diagnostic:

```powershell
python -c "import torch, pytest; raise SystemExit(pytest.main(['-q']))"
```

The model was trained on English shopping queries and product titles. Validate
ranking quality on held-out clothing requests before treating scores as quality
measurements. A successful model smoke test establishes loading and inference,
not catalogue-wide recommendation accuracy.
