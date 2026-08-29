# AI-Based Occasion-Aware Fashion Recommendation and AI Stylist System

## Qwen3-VL:8B Implementation Specification

---

# 1. Project Overview

Build an AI-powered fashion recommendation system for a real-world clothing store using:

- Qwen3-VL:8B
- Ollama
- Product dataset
- Product images
- Backend recommendation engine
- Frontend customer interface

The main research focus is:

> **Occasion-aware clothing recommendation**

The system should understand the customer's clothing requirements and use the `occasion` information as an important recommendation feature when the customer provides an occasion.

However, **occasion must not be mandatory**.

If the customer does not mention an occasion, the system must continue recommending products using the other requirements without inventing an occasion.

---

# 2. Exact Dataset

The system must use the following exact 15-column dataset:

```text
product_id
gender
category
article_type
base_colour
occasion
available_sizes
pattern
sleeve_type
neck_type
material
style
description
price
image_path
```

Do not add unnecessary columns such as:

```text
stock_quantity
availability
brand
discount
sku
inventory_id
```

for the initial implementation.

The current dataset already contains product size information through:

```text
available_sizes
```

Therefore, `available_sizes` is the source of truth for size availability.

---

# 3. Dataset Column Description

| Column | Description |
|---|---|
| `product_id` | Unique product identifier |
| `gender` | Gender associated with the product |
| `category` | Main clothing category |
| `article_type` | Type of clothing/dress |
| `base_colour` | Main product color |
| `occasion` | Occasion for which the product is suitable |
| `available_sizes` | Sizes available for the product |
| `pattern` | Product pattern |
| `sleeve_type` | Sleeve type |
| `neck_type` | Neck type |
| `material` | Product material |
| `style` | Product style |
| `description` | Product description |
| `price` | Product price |
| `image_path` | Product image location |

---

# 4. Main Research Focus — Occasion

The primary research focus is:

```text
Customer Requirement
        ↓
Occasion Understanding
        ↓
Occasion-Aware Recommendation
```

The system should investigate how understanding the customer's intended occasion can improve clothing recommendations.

Occasion examples may include:

```text
Wedding
Birthday
Party
Office
Casual outing
Formal event
Date
Vacation
Festival
Dinner
Interview
Sports
Beach
Traditional event
```

The actual occasion values must be based on the dataset. Do not assume that all values above exist in the dataset.

---

# 5. Occasion Must Be Optional

The customer is **not required** to provide an occasion.

There are three possible cases.

## Case 1 — Customer explicitly mentions an occasion

Example:

```text
I need a black elegant dress for a birthday party.
```

The system should extract:

```text
occasion = Birthday Party
```

The occasion should receive a high importance during recommendation.

---

## Case 2 — Customer does not mention an occasion

Example:

```text
I need a black elegant dress.
```

The system must return:

```json
{
  "occasion": null
}
```

The system must NOT assume:

```text
Wedding
Party
Birthday
Office
Date
```

Instead, recommendations should be based on the customer's other requirements:

```text
Article Type
Color
Style
Pattern
Material
Sleeve Type
Neck Type
Description
Price
```

---

## Case 3 — Customer requests multiple/flexible occasions

Example:

```text
I need a dress that I can wear to parties and dinners.
```

The system should extract:

```json
{
  "occasion": [
    "Party",
    "Dinner"
  ]
}
```

The recommendation engine should prefer products suitable for the requested occasions.

---

# 6. Critical Occasion Rule

```text
IF customer mentions occasion
        ↓
Use occasion as a major recommendation feature

IF customer does NOT mention occasion
        ↓
occasion = null
        ↓
Do NOT invent an occasion
        ↓
Do NOT remove products because occasion is missing
        ↓
Recommend using other requirements
```

This distinction is important for the research evaluation.

---

# 7. Exact Customer Flow

```text
Customer
   ↓
Select Gender
   ↓
Select Size
   ↓
Enter Natural-Language Requirements
   ↓
Qwen3-VL:8B analyzes requirements
   ↓
Extract Occasion if mentioned
   ↓
Backend filters Gender
   ↓
Backend filters Selected Size
   ↓
Requirement Matching
   ↓
Occasion-aware ranking if occasion exists
   ↓
Rank Products
   ↓
Display Recommended Products
   ↓
Customer Selects One Product
   ↓
Qwen3-VL:8B analyzes selected product image
   ↓
Generate AI Stylist Tips
```

---

# 8. System Architecture

```text
                         CUSTOMER
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
        Gender             Size         Requirements
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                     QWEN3-VL:8B
                  Requirement Analysis
                            │
                            ▼
                  Structured Requirements
                            │
                            ▼
                RECOMMENDATION ENGINE
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        Gender Filter   Size Filter   Requirement
                                        Matching
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                    Occasion Analysis
                            │
                  ┌─────────┴─────────┐
                  │                   │
          Occasion Provided     Occasion Missing
                  │                   │
                  ▼                   ▼
          High-weight occasion   Do not assume
              matching            any occasion
                  │                   │
                  └─────────┬─────────┘
                            ▼
                         Ranking
                            │
                            ▼
                     Top Recommendations
                            │
                            ▼
                   Customer Selects Product
                            │
                            ▼
                    Selected Product Image
                            +
                     Product Metadata
                            +
                   Customer Requirements
                            │
                            ▼
                     QWEN3-VL:8B
                            │
                            ▼
                     AI Stylist Tips
```

---

# 9. Role of Qwen3-VL:8B

Qwen3-VL:8B should be used for:

- Natural-language requirement understanding
- Requirement extraction
- Occasion understanding
- Product image understanding
- Multimodal reasoning
- AI stylist recommendations

Qwen should NOT be responsible for:

- Database filtering
- Size availability
- Price calculations
- Direct inventory decisions
- Deterministic product ranking

The backend must handle these operations.

---

# 10. Customer Input

The customer provides:

## Gender

Selected from the available dataset values.

## Size

The UI should support:

```text
XS
S
M
L
XL
2XL
3XL
4XL
```

Only sizes actually supported by the product data should be considered available.

## Requirements

The customer enters natural language.

Examples:

```text
I need a black elegant dress for a birthday party.
```

```text
I need a comfortable black dress.
```

```text
I want something suitable for a wedding, preferably blue and elegant.
```

---

# 11. Requirement Extraction

Qwen3-VL receives the customer's requirements.

Example input:

```text
I need a black elegant dress for a birthday party.
```

Expected output:

```json
{
  "occasion": [
    "Birthday Party"
  ],
  "preferred_colors": [
    "Black"
  ],
  "article_types": [
    "Dress"
  ],
  "style_preferences": [
    "Elegant"
  ],
  "materials": [],
  "patterns": [],
  "sleeve_types": [],
  "neck_types": [],
  "other_requirements": [],
  "price_preference": null
}
```

---

# 12. Example When Occasion Is Missing

Customer:

```text
I need a black elegant dress.
```

Expected:

```json
{
  "occasion": null,
  "preferred_colors": [
    "Black"
  ],
  "article_types": [
    "Dress"
  ],
  "style_preferences": [
    "Elegant"
  ],
  "materials": [],
  "patterns": [],
  "sleeve_types": [],
  "neck_types": [],
  "other_requirements": [],
  "price_preference": null
}
```

Do not change this to `Party`, `Wedding`, `Birthday`, or another invented occasion.

---

# 13. Requirement JSON Schema

Use:

```json
{
  "occasion": null,
  "preferred_colors": [],
  "article_types": [],
  "style_preferences": [],
  "materials": [],
  "patterns": [],
  "sleeve_types": [],
  "neck_types": [],
  "other_requirements": [],
  "price_preference": null
}
```

When an occasion is provided:

```json
{
  "occasion": ["Wedding"]
}
```

When multiple occasions are provided:

```json
{
  "occasion": ["Party", "Dinner"]
}
```

When no occasion is provided:

```json
{
  "occasion": null
}
```

---

# 14. Qwen Requirement Prompt

Create:

```text
prompts/requirement_prompt.txt
```

Use a prompt similar to:

```text
You are a fashion requirement extraction assistant.

Analyze the customer's clothing request.

Extract only the customer's explicitly stated or clearly implied
requirements.

The main research feature is OCCASION.

If the customer explicitly mentions an occasion, extract it.

If the customer does NOT mention an occasion, return:

"occasion": null

Do NOT invent or assume an occasion.

Return ONLY valid JSON using this schema:

{
  "occasion": null,
  "preferred_colors": [],
  "article_types": [],
  "style_preferences": [],
  "materials": [],
  "patterns": [],
  "sleeve_types": [],
  "neck_types": [],
  "other_requirements": [],
  "price_preference": null
}

Do not recommend products.

Do not invent customer requirements.

Gender and size are provided separately by the application.
```

---

# 15. Dataset Validation

Before recommendation:

```text
Load Dataset
      ↓
Validate Exact 15 Columns
      ↓
Validate Product IDs
      ↓
Normalize available_sizes
      ↓
Validate Prices
      ↓
Validate Image Paths
```

Required columns:

```text
product_id
gender
category
article_type
base_colour
occasion
available_sizes
pattern
sleeve_type
neck_type
material
style
description
price
image_path
```

---

# 16. Size Normalization

`available_sizes` may appear as:

```text
S,M,L
```

or:

```text
S, M, L
```

or:

```text
["S","M","L"]
```

Normalize all formats into:

```python
["S", "M", "L"]
```

Then check:

```python
customer_size in available_sizes
```

---

# 17. Gender Filtering

First filter products by the selected gender.

Example:

```text
Customer Gender = Female
```

Retrieve matching products.

If `Unisex` products exist, handle them using a configurable rule.

---

# 18. Size Filtering

After gender filtering:

```text
Customer Size
      ↓
available_sizes
      ↓
Is selected size available?
```

If:

```text
M ∈ available_sizes
```

the product continues.

If:

```text
M ∉ available_sizes
```

the product is excluded.

This is a **hard constraint**.

---

# 19. Requirement Matching

Match requirements against:

```text
article_type
base_colour
occasion
style
pattern
material
sleeve_type
neck_type
category
description
```

---

# 20. Occasion-Aware Recommendation

When occasion is provided, occasion should be one of the most important features.

Initial configurable weights:

```text
article_type       20%
occasion           30%
base_colour        20%
style              15%
pattern             5%
material            5%
sleeve_type         2.5%
neck_type           2.5%
```

These weights are initial values and must be evaluated experimentally.

The research principle is:

```text
Occasion = High Importance
```

when the customer provides an occasion.

---

# 21. When Occasion Is Missing

When:

```text
occasion = null
```

the system must not penalize every product simply because the customer did not provide an occasion.

Instead, calculate the recommendation using:

```text
article_type
base_colour
style
pattern
material
sleeve_type
neck_type
category
description
```

Example:

```text
Customer:
"I need a black elegant dress."

Occasion:
NULL

Use:
Article type → important
Color → important
Style → important
Description → useful
Occasion → not used as a customer-match constraint
```

The product's occasion can still be shown as contextual information.

---

# 22. Research Strategy for Missing Occasion

The research should explicitly evaluate two scenarios.

## Scenario A — Occasion Provided

Example:

```text
I need a dress for a wedding.
```

Use:

```text
Occasion-aware recommendation
```

## Scenario B — Occasion Missing

Example:

```text
I need an elegant blue dress.
```

Use:

```text
No assumed occasion
```

This allows evaluation of whether occasion-aware recommendation improves recommendation quality when occasion information is available while maintaining useful recommendations when it is absent.

---

# 23. Multiple Occasions

If customer says:

```text
I need something for parties and dinners.
```

Qwen returns:

```json
{
  "occasion": [
    "Party",
    "Dinner"
  ]
}
```

Products matching either requested occasion receive higher scores.

Products matching both can receive an additional versatility bonus.

---

# 24. Occasion Normalization

Customers may use different expressions:

```text
wedding ceremony
wedding
marriage function
```

These may refer to the same concept.

Create:

```text
config/occasion_mapping.json
```

Example:

```json
{
  "marriage": "wedding",
  "wedding ceremony": "wedding",
  "birthday celebration": "birthday"
}
```

Only create mappings relevant to the actual dataset.

---

# 25. Semantic Matching

Exact string matching may not always work.

Example:

```text
Customer:
birthday celebration

Dataset:
birthday party
```

Use normalized matching first.

A later enhancement can add semantic similarity or embeddings.

---

# 26. Description Matching

Use the `description` field to improve recommendation relevance.

Example:

```text
Description:
Elegant lightweight dress suitable for evening celebrations.
```

Customer:

```text
I need something elegant for an evening event.
```

The description can contribute to the score.

---

# 27. Price Handling

If customer says:

```text
I need something below 5000.
```

Extract:

```json
{
  "price_preference": {
    "max": 5000
  }
}
```

Backend performs:

```text
price <= 5000
```

Do not ask Qwen to calculate or filter prices.

---

# 28. Recommendation Ranking

If occasion is provided:

```text
Final Score =
    0.20 Article Type
  + 0.30 Occasion
  + 0.20 Color
  + 0.15 Style
  + 0.05 Pattern
  + 0.05 Material
  + 0.025 Sleeve
  + 0.025 Neck
```

If occasion is missing, redistribute its weight.

Example:

```text
Final Score =
    0.30 Article Type
  + 0.25 Color
  + 0.20 Style
  + 0.10 Pattern
  + 0.05 Material
  + 0.05 Sleeve
  + 0.05 Neck
```

Weights must be configurable.

---

# 29. Hard vs Soft Constraints

## Hard Constraints

Always respect:

```text
Gender
Selected Size
```

If the customer explicitly specifies a strict maximum price, price can also be a hard constraint.

## Soft Constraints

Use for ranking:

```text
Occasion
Color
Article Type
Style
Pattern
Material
Sleeve
Neck
Description
```

When explicitly requested, occasion and article type should receive high importance.

---

# 30. Recommendation Result

Return Top 5 products.

Example:

```json
{
  "recommendations": [
    {
      "product_id": "P001",
      "image_path": "images/P001.jpg",
      "article_type": "Dress",
      "base_colour": "Black",
      "occasion": "Birthday",
      "style": "Elegant",
      "price": 4500,
      "selected_size": "M",
      "match_score": 0.92
    }
  ]
}
```

---

# 31. Recommendation Explanation

Each recommendation may show why it was selected.

When occasion is provided:

```text
This dress matches your selected size, black color,
dress type, elegant style and birthday occasion.
```

When occasion is not provided:

```text
This dress matches your selected size, black color,
dress type and elegant style.
```

Do not claim an occasion the customer never mentioned.

---

# 32. No-Match Handling

If no exact match exists:

```text
Gender + Size
```

must remain valid.

Relax soft requirements progressively:

```text
1. Gender + Size + Article Type + Occasion + Color
2. Gender + Size + Article Type + Occasion
3. Gender + Size + Article Type
4. Gender + Size
```

Then rank the closest products.

Display:

```text
No exact match was found.
Here are the closest available options in your selected size.
```

---

# 33. Product Selection

After displaying recommendations:

```text
Customer selects one product
```

Retrieve:

```text
product_id
image_path
all product metadata
customer gender
customer size
original requirements
structured requirements
```

---

# 34. AI Stylist Stage

The second Qwen task begins only after product selection.

Input:

```text
Selected Product Image
+
Product Metadata
+
Customer Requirements
```

Qwen3-VL analyzes the actual clothing image and provides:

```text
Overall styling
Accessories
Footwear
Color combinations
Layering
Occasion suitability
Complementary items
```

---

# 35. Stylist Prompt

Create:

```text
prompts/stylist_prompt.txt
```

Suggested prompt:

```text
You are an AI fashion stylist.

Analyze the selected clothing item's image and product information.

Consider the customer's original requirements.

Provide practical styling recommendations specifically for
the selected clothing item.

If the customer provided an occasion, make the styling advice
appropriate for that occasion.

If the customer did not provide an occasion, do not invent
a specific occasion. Give generally versatile styling advice
based on the selected product.

Include:

- overall styling
- accessories
- footwear
- complementary colors
- layering when relevant
- occasion advice when an occasion was provided
- complementary clothing items

Do not judge or criticize the customer's body or physical appearance.

Return ONLY valid JSON.
```

---

# 36. Stylist Output

Use:

```json
{
  "summary": "",
  "accessories": [],
  "footwear": [],
  "color_combinations": [],
  "layering": [],
  "occasion_tip": "",
  "complementary_items": []
}
```

---

# 37. Stylist Behavior When Occasion Is Known

Example:

```text
Customer:
I need a dress for a wedding.
```

The stylist should provide advice related to the wedding context.

---

# 38. Stylist Behavior When Occasion Is Missing

Example:

```text
Customer:
I need a black elegant dress.
```

The stylist must NOT say:

```text
For your wedding...
```

Instead, provide generally versatile styling advice.

---

# 39. API Endpoints

## Requirement Analysis

```text
POST /api/requirements/analyze
```

Request:

```json
{
  "requirements": "I need a black elegant dress for a birthday party."
}
```

## Recommendations

```text
POST /api/recommendations
```

Request:

```json
{
  "gender": "Female",
  "size": "M",
  "requirements": "I need a black elegant dress for a birthday party."
}
```

Processing:

```text
Validate input
      ↓
Qwen requirement analysis
      ↓
Gender filtering
      ↓
Size filtering
      ↓
Occasion handling
      ↓
Requirement matching
      ↓
Ranking
      ↓
Top 5
```

## Stylist

```text
POST /api/stylist
```

Request:

```json
{
  "gender": "Female",
  "size": "M",
  "requirements": "I need a black elegant dress for a birthday party.",
  "product_id": "P001"
}
```

---

# 40. Backend Services

Create:

```text
services/qwen_service.py
```

Responsibilities:

```text
analyze_requirements()
generate_styling_tips()
```

Create:

```text
services/product_service.py
```

Responsibilities:

```text
load dataset
get product
validate product
resolve image path
```

Create:

```text
services/recommendation_service.py
```

Responsibilities:

```text
gender filtering
size filtering
occasion handling
requirement matching
candidate generation
```

Create:

```text
services/ranking_service.py
```

Responsibilities:

```text
calculate scores
occasion scoring
requirement scoring
sort products
return Top-K
```

Create:

```text
services/retrieval_service.py
```

Responsibilities:

```text
optional text embeddings
optional image embeddings
optional vector search
```

---

# 41. Project Structure

```text
fashion-recommendation/
│
├── data/
│   └── products.csv
│
├── images/
│   ├── P001.jpg
│   ├── P002.jpg
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── requirements.py
│   │   │   ├── recommendations.py
│   │   │   └── stylist.py
│   │   ├── services/
│   │   │   ├── qwen_service.py
│   │   │   ├── product_service.py
│   │   │   ├── recommendation_service.py
│   │   │   ├── ranking_service.py
│   │   │   └── retrieval_service.py
│   │   ├── schemas/
│   │   ├── prompts/
│   │   │   ├── requirement_prompt.txt
│   │   │   └── stylist_prompt.txt
│   │   └── config.py
│   └── requirements.txt
│
├── config/
│   └── occasion_mapping.json
│
├── scripts/
│   └── validate_dataset.py
│
├── frontend/
│
└── README.md
```

---

# 42. Development Phases

## Phase 1 — Dataset

Implement:

```text
Load CSV
Validate exact 15 columns
Validate IDs
Normalize available_sizes
Validate prices
Validate image paths
```

## Phase 2 — Ollama + Qwen

Implement:

```text
Connect Ollama
Verify qwen3-vl:8b
Requirement extraction
JSON validation
Occasion extraction
```

## Phase 3 — Basic Recommendation

Implement:

```text
Gender filter
↓
Size filter
↓
Requirement matching
↓
Occasion-aware ranking
↓
Top 5
```

## Phase 4 — Frontend

Implement:

```text
Gender selection
↓
Size selection
↓
Requirement input
↓
Recommendation cards
```

## Phase 5 — Product Selection

Implement:

```text
Customer selects product
↓
Retrieve product information
↓
Retrieve product image
```

## Phase 6 — AI Stylist

Implement:

```text
Selected product image
+
Product metadata
+
Customer requirements
↓
Qwen3-VL
↓
Stylist tips
```

## Phase 7 — Optional Multimodal Retrieval

After the basic system works:

```text
Text embeddings
+
Image embeddings
+
Vector database
+
Semantic retrieval
```

---

# 43. Fine-Tuning

Do **not** fine-tune Qwen3-VL:8B initially.

The first implementation should use:

```text
Qwen3-VL:8B
+
Prompt Engineering
+
Product Dataset
+
Backend Filtering
+
Recommendation Ranking
```

Fine-tuning should only be considered after evaluating the baseline.

---

# 44. Optional Embedding Enhancement

Later, add:

```text
Customer requirement
        ↓
Text embedding
        ↓
Product description embedding
        ↓
Semantic similarity
```

For images:

```text
Product image
        ↓
Image embedding
        ↓
Image similarity
```

These can be combined with the occasion-aware recommendation score.

---

# 45. Research Experiment Design

The research should compare recommendation performance under different conditions.

## Experiment 1 — Occasion Provided

Example:

```text
I need a dress for a wedding.
```

Use:

```text
Occasion-aware recommendation
```

Measure recommendation quality.

## Experiment 2 — Occasion Missing

Example:

```text
I need an elegant blue dress.
```

Use:

```text
No assumed occasion
```

Measure recommendation quality.

## Experiment 3 — Occasion-Aware vs Baseline

Compare:

```text
Baseline recommendation
```

against:

```text
Occasion-aware recommendation
```

This determines whether occasion-aware recommendation improves recommendation relevance.

---

# 46. Evaluation Metrics

## Requirement Extraction

Evaluate:

```text
Occasion extraction accuracy
Precision
Recall
F1-score
```

Especially test:

```text
Correct occasion
No occasion → correctly returns null
Multiple occasions → correctly extracted
```

## Recommendation

Use:

```text
Precision@K
Recall@K
Hit Rate@K
NDCG@K
MRR
```

Recommended:

```text
Precision@5
Recall@5
NDCG@5
```

Compare:

```text
Occasion-aware model
```

against:

```text
Baseline recommendation
```

---

# 47. Occasion-Specific Evaluation

Create test cases from the actual dataset's occasion values.

For each:

```text
Customer Requirement
        ↓
Extract Occasion
        ↓
Retrieve Products
        ↓
Rank Products
        ↓
Evaluate Top-K
```

Do not use occasion labels that are absent from the dataset without defining how they map to the dataset.

---

# 48. Missing Occasion Evaluation

Create test cases where no occasion is mentioned.

Examples:

```text
I want a black elegant dress.

I want a comfortable blue shirt.

I need a casual outfit.

I want a simple floral dress.
```

The system must:

```text
NOT invent an occasion
```

and must still return relevant products.

---

# 49. Performance Evaluation

Measure:

```text
Qwen inference time
Requirement analysis time
Filtering time
Ranking time
Recommendation response time
Stylist generation time
Total end-to-end response time
```

---

# 50. UI Flow

## Screen 1 — Gender and Size

```text
-----------------------------------
        Find Your Perfect Outfit
-----------------------------------

Gender

[ Female ▼ ]

Size

[ XS ] [ S ] [ M ] [ L ]
[ XL ] [ 2XL ] [ 3XL ] [ 4XL ]

             [ Continue ]

-----------------------------------
```

## Screen 2 — Requirements

```text
-----------------------------------
       What are you looking for?
-----------------------------------

Tell us what you need:

[ I need a black elegant dress
  for a birthday party...       ]

             [ Find Clothes ]

-----------------------------------
```

Occasion should NOT be a required separate input.

The customer can naturally mention the occasion in their text.

## Screen 3 — Recommendations

```text
-----------------------------------
       Recommended For You
-----------------------------------

[ Image ]       [ Image ]

Black Dress     Blue Dress
Birthday        Birthday

Rs. 4500        Rs. 5000

[ View ]         [ View ]

-----------------------------------
```

## Screen 4 — AI Stylist

```text
-----------------------------------
           Your AI Stylist
-----------------------------------

[ Selected Product Image ]

How to Style
...

Accessories
...

Footwear
...

Color Combinations
...

Occasion Tip
...

Complementary Items
...

-----------------------------------
```

---

# 51. Error Handling

Handle:

```text
Ollama unavailable
Qwen unavailable
Invalid Qwen JSON
Dataset unavailable
Invalid product
Missing image
Invalid size
Invalid gender
No matching products
```

Do not expose technical stack traces to customers.

---

# 52. Missing Product Image

If a product image does not exist:

```text
Recommendation:
Still possible

Stylist:
Cannot perform image-based analysis
```

Return a controlled message.

---

# 53. Important Agent Rules

Before coding:

1. Inspect the existing repository.
2. Identify the current frontend.
3. Identify the current backend.
4. Identify the actual dataset.
5. Do not replace working components unnecessarily.
6. Verify Ollama.
7. Verify `qwen3-vl:8b`.
8. Validate the exact 15 dataset columns.
9. Test size filtering.
10. Test occasion extraction.
11. Test missing-occasion behavior.
12. Test recommendation ranking.
13. Test product selection.
14. Test stylist generation.

---

# 54. Critical Business Rules

### Rule 1
The dataset is the source of truth for product information.

### Rule 2
`available_sizes` is the source of truth for size availability.

### Rule 3
Selected customer size is a hard constraint.

### Rule 4
Qwen does not determine size availability.

### Rule 5
Qwen does not directly search the complete dataset.

### Rule 6
Backend performs filtering.

### Rule 7
Backend performs ranking.

### Rule 8
Occasion is the main research feature.

### Rule 9
Occasion is optional for the customer.

### Rule 10
If occasion is missing, do NOT invent one.

### Rule 11
If occasion is provided, give it high importance during ranking.

### Rule 12
The selected product image is used by Qwen for stylist advice.

### Rule 13
Do not expose chain-of-thought.

### Rule 14
Do not make judgments about the customer's body or physical appearance.

---

# 55. Complete Example — Occasion Provided

Dataset:

```text
P001 | Female | Apparel | Dress | Black | Party | S,M,L | Solid | Short | V-Neck | Chiffon | Elegant | Black elegant party dress | 4500 | images/P001.jpg

P002 | Female | Apparel | Dress | Red | Party | S,L,XL | Floral | Short | Round | Cotton | Casual | Red floral party dress | 4000 | images/P002.jpg

P003 | Female | Apparel | Dress | Black | Casual | M,L | Solid | Long | V-Neck | Cotton | Elegant | Black casual dress | 3500 | images/P003.jpg
```

Customer:

```text
Gender = Female
Size = M
```

Requirements:

```text
I need a black elegant dress for a birthday party.
```

Qwen:

```json
{
  "occasion": ["Birthday Party"],
  "preferred_colors": ["Black"],
  "article_types": ["Dress"],
  "style_preferences": ["Elegant"]
}
```

Gender:

```text
P001 ✓
P002 ✓
P003 ✓
```

Size:

```text
P001 → M ✓
P002 → M ✗
P003 → M ✓
```

Candidates:

```text
P001
P003
```

Occasion:

```text
P001 → Party ✓
P003 → Casual ✗
```

Therefore:

```text
P001 → High score
P003 → Lower score
```

The customer sees P001 first.

---

# 56. Complete Example — Occasion Missing

Customer:

```text
Gender = Female
Size = M

Requirements:
I need a black elegant dress.
```

Qwen:

```json
{
  "occasion": null,
  "preferred_colors": ["Black"],
  "article_types": ["Dress"],
  "style_preferences": ["Elegant"]
}
```

The system must NOT assume:

```text
Party
Wedding
Birthday
Office
```

Filtering:

```text
Gender = Female
Size = M
```

Then ranking uses:

```text
Color
Article Type
Style
Pattern
Material
Sleeve
Neck
Description
```

The system still produces recommendations.

---

# 57. Complete Example — Multiple Occasions

Customer:

```text
I need a dress that I can wear for dinner and parties.
```

Qwen:

```json
{
  "occasion": [
    "Dinner",
    "Party"
  ]
}
```

Products matching either occasion receive higher scores.

Products matching both may receive a versatility bonus.

---

# 58. Final System Architecture

```text
                    CUSTOMER
                       │
                       ▼
               Select Gender
                       │
                       ▼
                Select Size
                       │
                       ▼
             Enter Requirements
                       │
                       ▼
                QWEN3-VL:8B
                       │
                       ▼
           Extract Requirements
                       │
                       ▼
              Is Occasion Given?
                 /          \
               YES           NO
                │             │
                ▼             ▼
        Occasion = value  occasion = null
                │             │
                ▼             ▼
        High-weight        Do NOT assume
        occasion match     any occasion
                │             │
                └──────┬──────┘
                       ▼
                Gender Filtering
                       │
                       ▼
                 Size Filtering
                       │
                       ▼
              Requirement Matching
                       │
                       ▼
                    Ranking
                       │
                       ▼
              Top Recommendations
                       │
                       ▼
             Customer Selects Product
                       │
                       ▼
              Selected Product Image
                       +
               Product Information
                       +
              Customer Requirements
                       │
                       ▼
                 QWEN3-VL:8B
                       │
                       ▼
                AI Stylist Tips
```

---

# 59. Final Research Principle

The system must answer:

### Research Question 1

Does explicitly understanding the customer's intended occasion improve clothing recommendation relevance?

### Research Question 2

Can the system still provide useful recommendations when the customer does not specify an occasion, without incorrectly assuming one?

Therefore:

```text
Occasion explicitly provided
        ↓
Occasion-aware recommendation
```

and:

```text
Occasion not provided
        ↓
No assumption
        ↓
Other requirement-based recommendation
```

This distinction should be maintained throughout implementation and evaluation.

---

# 60. Final Acceptance Criteria

- [ ] Exact 15-column dataset is used.
- [ ] Customer can select gender.
- [ ] Customer can select XS–4XL size.
- [ ] Customer can enter natural-language requirements.
- [ ] Qwen3-VL:8B extracts requirements.
- [ ] Qwen correctly extracts occasion when explicitly mentioned.
- [ ] Qwen returns `occasion = null` when occasion is not mentioned.
- [ ] System never invents an occasion.
- [ ] Gender filtering works.
- [ ] Size filtering uses `available_sizes`.
- [ ] Products without the selected size are excluded.
- [ ] Occasion receives high importance when provided.
- [ ] Missing occasion does not prevent recommendations.
- [ ] Article type is considered.
- [ ] Color is considered.
- [ ] Style is considered.
- [ ] Pattern is considered.
- [ ] Material is considered.
- [ ] Sleeve type is considered.
- [ ] Neck type is considered.
- [ ] Description can contribute to semantic matching.
- [ ] Products are ranked.
- [ ] Top 5 recommendations are displayed.
- [ ] Customer can select a product.
- [ ] Selected product image is loaded.
- [ ] Qwen3-VL analyzes selected product image.
- [ ] AI stylist tips are generated.
- [ ] Stylist advice respects the customer's occasion when provided.
- [ ] Stylist does not invent an occasion when it was not provided.
- [ ] No body/appearance judgments are generated.
- [ ] No-match cases are handled.
- [ ] Missing images are handled.
- [ ] System works without fine-tuning initially.
- [ ] Research metrics can be collected.
- [ ] Occasion-aware vs. occasion-missing scenarios can be evaluated.
- [ ] Occasion-aware ranking can be compared against a baseline.

---

# 61. FINAL CORE RULE

```text
CUSTOMER
   │
   ├── Gender
   ├── Size
   └── Natural-Language Requirements
             │
             ▼
        Qwen3-VL:8B
             │
             ▼
     Extract Requirements
             │
             ▼
       Is Occasion Given?
          /         \
        YES          NO
         │            │
         ▼            ▼
  Use Occasion     occasion=null
  as Major         Do NOT assume
  Feature          any occasion
         │            │
         └─────┬──────┘
               ▼
        Gender Filtering
               ▼
         Size Filtering
               ▼
      Requirement Matching
               ▼
            Ranking
               ▼
       Top Recommendations
               ▼
      Customer Selects Product
               ▼
       Selected Product Image
               +
        Product Information
               +
       Customer Requirements
               ▼
         Qwen3-VL:8B
               ▼
        AI Stylist Tips
```

The core research feature is **not forcing every customer to provide an occasion**.

The system must distinguish:

```text
Occasion explicitly provided
        → occasion-aware recommendation
```

from:

```text
Occasion not provided
        → no invented occasion
        → recommendation based on other requirements
```
