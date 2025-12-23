# Light Parsing System for Food and Symptom Extraction

> **Exercise C** submission for Ashwam Backend Engineering Internship.  
> Built a two-parser architecture to demonstrate clean separation of concerns and system design thinking.

A privacy-first, deterministic parsing system for extracting food and symptom signals from women's health journal entries.

## Overview

This system implements a **two-parser architecture** that separates concerns between food extraction and symptom extraction. Both parsers operate independently and are coordinated by a lightweight pipeline orchestrator.

### Architecture

```
┌─────────────────────────────────────┐
│   LightParsePipeline (Orchestrator) │
└────────────┬────────────────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
┌──────────┐  ┌──────────────┐
│  Food    │  │  Symptom     │
│  Parser  │  │  Parser      │
└──────────┘  └──────────────┘
```

**Why Separate Parsers?**
- **Independent evolution**: Food and symptom lexicons change at different rates
- **Isolated testing**: Each parser can be validated independently
- **Clear ownership**: Different team members can maintain different parsers
- **Modularity**: Easy to add new parsers (e.g., MedicationParser) without touching existing code

## Quick Start

### Installation

```bash
# Clone or download the project
cd light_parser

# Install dependencies
pip install -r requirements.txt
```

### Run Parsing

```bash
# Basic usage
python main.py --in data/entries.jsonl --out parsed.jsonl

# With verbose output
python main.py --in data/entries.jsonl --out results/output.jsonl --verbose

# Check version
python main.py --version
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=parsers --cov-report=html

# Run specific test file
pytest tests/test_food_parser.py -v
```

## What Gets Extracted

### FoodParser

Extracts food items with the following attributes:

- **name**: Normalized food name (e.g., "egg" not "eggs")
- **quantity**: Numeric quantity if present (supports "half", "quarter", decimals)
- **unit**: Unit of measurement (bowl, cup, piece, plate, slice, etc.)
- **meal**: Meal context (breakfast, lunch, dinner, snack, unknown)
- **confidence**: Confidence score (0-1)

**Special handling:**
- Skipped meals: Detects "Skipped dinner" and marks with `name: "skipped"`
- Hinglish foods: Supports dal, chawal, dahi, idli, dosa, paratha, etc.
- Plural normalization: "eggs" → "egg", "almonds" → "almond"

### SymptomParser

Extracts symptoms with the following attributes:

- **name**: Normalized symptom name (e.g., "bloating" not "bloated")
- **severity**: Severity level if mentioned (numeric "6/10" or descriptive "severe")
- **time_hint**: Temporal context (morning, afternoon, evening, night, after_meal)
- **negated**: Boolean indicating if symptom was negated ("no headache")
- **confidence**: Confidence score (0-1)

**Special handling:**
- Negation detection: "No headache today" → `negated: true`
- Hinglish support: "bahut" maps to "severe"
- Multi-word symptoms: Detects "back pain", "stomach pain", "sore throat"
- Synonym normalization: "tired" → "fatigue", "bloated" → "bloating"

## Detection Approach

### Food Detection

1. **Lexicon-based matching**: 70+ food terms including Indian foods
2. **Quantity extraction**: Looks in a 20-character window before food mention
3. **Meal inference**: 
   - Explicit keywords: "breakfast", "lunch", "dinner"
   - Hinglish: "lunch mein"
   - Time-based: "morning" → breakfast, "night" → dinner
4. **Skip detection**: "Skipped", "skip kiya" with meal context

**Confidence calculation:**
- Base: 0.7 for lexicon match
- +0.15 if quantity present
- +0.1 if meal context identified
- +0.05 for common foods (rice, egg, bread, etc.)

### Symptom Detection

1. **Lexicon-based matching**: 50+ symptom terms covering women's health
2. **Negation detection**: Looks 30 characters before symptom for "no", "not", "without", etc.
3. **Severity extraction**: Numeric (6/10) or descriptive (mild, severe)
4. **Time extraction**: Pattern matching for morning/afternoon/evening/night/after_meal

**Confidence calculation:**
- Base: 0.75 for lexicon match
- +0.15 if severity specified
- +0.05 if time hint present
- Higher confidence (0.9+) for negated symptoms (strong signal)
- +0.05 for clear symptoms (cramps, migraine, nausea)

### Overlap Handling

Both parsers track character positions and skip overlapping matches within a small window (10-15 characters). When overlaps occur:
- Longer matches are preferred (handled by sorting lexicon by length)
- First match wins (left-to-right processing)

## Output Format

Each parsed entry produces:

```json
{
  "entry_id": "e_001",
  "foods": [
    {
      "name": "egg",
      "quantity": 2.0,
      "unit": null,
      "meal": "unknown",
      "confidence": 0.85
    }
  ],
  "symptoms": [
    {
      "name": "cramps",
      "severity": null,
      "time_hint": "afternoon",
      "negated": false,
      "confidence": 0.85
    }
  ],
  "parse_errors": [],
  "parser_version": "v1.0"
}
```

## Normalization Rules

### Food Normalization
- Plurals: "eggs" → "egg", "almonds" → "almond", "cookies" → "cookie"
- Quantities: "half" → 0.5, "quarter" → 0.25
- Case: All food names lowercase

### Symptom Normalization
- State → condition: "bloated" → "bloating", "dizzy" → "dizziness"
- Synonyms: "tired" → "fatigue", "anxious" → "anxiety"
- Hinglish: "bahut" → "severe"
- Case: All symptom names lowercase

## Known Limitations

1. **Temporal reasoning**: Cannot distinguish past/future symptoms ("headache tomorrow" vs "headache today")
2. **Negation scope**: Window-based approach may incorrectly negate across sentence boundaries
3. **Semantic understanding**: Treats "egg biryani" as separate items; doesn't understand compound dishes
4. **Lexicon maintenance**: New foods/symptoms require manual updates to detection lists

## What I Would Improve Next

### With More Time

1. **Better temporal parsing**: Distinguish past/present/future symptoms
2. **Medication tracking**: Create MedicationParser to link meds with symptoms
3. **Confidence calibration**: A/B test confidence thresholds against human labels
4. **Pronoun handling**: Basic coreference to avoid false positives
5. **Portion size normalization**: Map units to standard portions (1 bowl ≈ 200ml)

### With Better Tools

1. **Named Entity Recognition (NER)**: Use lightweight NER model for food/symptom spans
2. **Dependency parsing**: Link symptoms to severity/timing more accurately
3. **Word embeddings**: Detect unknown foods/symptoms similar to known ones
4. **Active learning**: User feedback loop to expand lexicons incrementally
5. **Multi-language models**: Proper Hinglish/Hindi handling instead of word lists

### With More Data

1. **Build frequency-based confidence**: Common patterns → higher confidence
2. **Learn negation patterns**: More sophisticated negation scope detection
3. **Discover new terms**: Identify missing food/symptom terms from user data
4. **Validate edge cases**: Real-world edge cases to improve robustness

## Design Tradeoffs

### Lexicon-Based vs ML Models

**Chosen: Lexicon-based**

✅ **Pros:**
- 100% deterministic (same input → same output)
- No training data required
- Fast inference (milliseconds)
- Easy to debug and explain
- Privacy-first (runs on-device)
- Small memory footprint

❌ **Cons:**
- Maintenance burden (manual lexicon updates)
- Misses unknown terms
- No semantic understanding
- Limited to explicit mentions

**Alternative: ML-based NER**

Would provide better generalization but violates "no trained models" constraint and reduces debuggability.

### Two Parsers vs One Unified Parser

**Chosen: Two separate parsers**

✅ **Pros:**
- Clear separation of concerns
- Independent testing and evolution
- Easier to reason about bugs
- Team can work in parallel
- Can optimize each parser differently

❌ **Cons:**
- Slight code duplication (pattern matching logic)
- Potential for inconsistent design patterns
- Marginally slower (two passes over text)

**Alternative: Single unified parser**

Would be faster but harder to maintain and test as system grows.

### Confidence Scores

**Chosen: Rule-based confidence**

Confidence is calculated using additive heuristics (quantity present +0.15, severity present +0.15, etc.).

✅ **Pros:**
- Transparent and explainable
- Consistent across runs
- Easy to tune

❌ **Cons:**
- Not calibrated (0.85 doesn't mean "85% precision")
- Arbitrary weights
- Doesn't reflect true uncertainty

**Alternative: Learned confidence**

Would require labeled data and validation set, not feasible for deterministic system.

### Hinglish Support

**Chosen: Keyword inclusion in lexicon**

Added common Hinglish terms (dal, chawal, dahi, bahut, etc.) directly to lexicons.

✅ **Pros:**
- Simple implementation
- No language detection required
- Covers most common cases

❌ **Cons:**
- Limited to hardcoded terms
- Doesn't handle code-mixing beyond word level
- Misses transliteration variations

**Alternative: Transliteration + translation**

Would be more robust but adds complexity and potential errors.

## Testing Strategy

### Unit Tests (Independent Parsers)

- **FoodParser**: 15 test cases covering quantities, plurals, Hinglish, skipped meals
- **SymptomParser**: 18 test cases covering negation, severity, timing, normalization
- **Pipeline**: 13 test cases covering integration, error handling, determinism

### Test Coverage

- Negation handling (positive and negative cases)
- Hinglish terms (dal, chawal, bahut, etc.)
- Skipped meals
- Numeric quantities and fractional quantities
- False positive avoidance (steps, BP, battery percentage)
- Edge cases (empty input, missing fields, overlapping matches)
- Deterministic behavior (same input → same output)

### What's Tested

✅ All required detection types  
✅ Normalization rules  
✅ Confidence score ranges  
✅ Overlapping match handling  
✅ Error handling  
✅ Batch processing  

## File Structure

```
light_parser/
├── parsers/
│   ├── __init__.py           # Package exports
│   ├── food_parser.py        # FoodParser implementation
│   ├── symptom_parser.py     # SymptomParser implementation
│   └── pipeline.py           # LightParsePipeline orchestrator
├── tests/
│   ├── __init__.py
│   ├── test_food_parser.py   # FoodParser tests
│   ├── test_symptom_parser.py # SymptomParser tests
│   └── test_pipeline.py      # Pipeline integration tests
├── data/
│   └── entries.jsonl         # Input dataset (30 entries)
├── main.py                   # CLI entry point
├── requirements.txt          # Dependencies (pytest)
└── README.md                 # This file
```

## Example Usage

```python
from parsers import LightParsePipeline

# Initialize pipeline
pipeline = LightParsePipeline()

# Parse single entry
entry = {
    'entry_id': 'e_001',
    'text': '2 eggs + toast. Cramps started by noon 😣'
}

result = pipeline.run(entry)
print(result)

# Output:
# {
#   'entry_id': 'e_001',
#   'foods': [
#     {'name': 'egg', 'quantity': 2.0, 'unit': None, 'meal': 'unknown', 'confidence': 0.85},
#     {'name': 'toast', 'quantity': 1.0, 'unit': None, 'meal': 'unknown', 'confidence': 0.85}
#   ],
#   'symptoms': [
#     {'name': 'cramps', 'severity': None, 'time_hint': 'afternoon', 'negated': False, 'confidence': 0.85}
#   ],
#   'parse_errors': [],
#   'parser_version': 'v1.0'
# }
```

## Developer Notes

### Adding New Foods

Edit `FOOD_LEXICON` in [parsers/food_parser.py](parsers/food_parser.py):

```python
FOOD_LEXICON = {
    'rice', 'chawal', 'bread',
    # Add your new food here:
    'quinoa', 'hummus', 'tempeh',
}
```

### Adding New Symptoms

Edit `SYMPTOM_LEXICON` in [parsers/symptom_parser.py](parsers/symptom_parser.py):

```python
SYMPTOM_LEXICON = {
    'pain', 'cramps', 'bloating',
    # Add your new symptom here:
    'tremor', 'numbness', 'tingling',
}
```

### Extending Time Hints

Edit `TIME_HINTS` in [parsers/symptom_parser.py](parsers/symptom_parser.py):

```python
TIME_HINTS = {
    'morning': r'\b(morning|subah|AM|am)\b',
    # Add your new time pattern:
    'predawn': r'\b(predawn|early morning|fajr)\b',
}
```

## Performance

- **Parsing speed**: ~1-2ms per entry (2.7 GHz CPU)
- **Memory usage**: <10MB for full dataset
- **Determinism**: 100% (same input always produces same output)

## License

This project is submitted as part of the Ashwam Backend Engineering Internship assessment.

---

**Author**: Pranav Yayavaram  
**Date**: December 2025  
**Version**: 1.0
