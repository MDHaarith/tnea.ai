# Model Sizing Recommendations for TNEA AI

## Summary

This document provides recommendations for which prompts require larger models and which can safely run on smaller/faster models.

## Current Model: `qwen2.5:1.5b-instruct`

### Test Results with 1.5B Model
- **10 PASSED**, **3 FAILED**
- Pass rate: 77%

### Observed Limitations of Small Models (< 3B parameters)

| Issue | Example | Severity |
|-------|---------|----------|
| Numeric precision | "15,000" instead of "1500" | HIGH |
| Negative constraint following | Says "fee" when told not to | HIGH |
| Forbidden word avoidance | Uses "exact" when forbidden | MEDIUM |

---

## Prompt-by-Prompt Recommendations

### ✅ Safe for Small Models (1.5B - 3B)

| Prompt | Justification |
|--------|---------------|
| **Intent Router** | Simple classification, low risk |
| **Location Filter** | Structured output, no reasoning |
| **Response Formatter** | Formatting only, no judgment |
| **Greeting Handler** | Simple pattern matching |

### ⚠️ Recommended: Medium Models (7B - 13B)

| Prompt | Justification |
|--------|---------------|
| **College Suggestion** | Requires category logic |
| **Choice Filling Strategy** | Needs safe/moderate/ambitious reasoning |
| **Career Mapping** | Industry knowledge required |
| **Skill Search** | Web search integration |

### 🔴 Require Large Models (13B+) for Production Safety

| Prompt | Justification |
|--------|---------------|
| **Prediction Explanation** | Numeric precision critical |
| **Management Quota** | Negative constraints MUST be followed (fees, guarantees) |
| **Trend Analysis** | Must avoid confident predictions |

---

## Production Deployment Options

### Option 1: Hybrid Model Routing (Recommended)
```
Intent/Formatting → qwen2.5:1.5b-instruct (fast)
Reasoning/Safety  → llama3:8b or similar (slower but safer)
```

### Option 2: Single Larger Model
```
All prompts → qwen2.5:7b-instruct or llama3:8b
Latency:    ~2-3x slower than 1.5B
Safety:     Much better constraint following
```

### Option 3: Cloud API for High-Risk Prompts
```
Low-risk   → Local small model
High-risk  → Cloud API (GPT-4, Claude, etc.)
```

---

## Verification Requirements by Model Size

| Model Size | Required Tests | Expected Pass Rate |
|------------|----------------|-------------------|
| 1.5B | Intent + Formatting only | 100% |
| 7B | All tests | 90%+ |
| 13B+ | All tests + edge cases | 95%+ |

---

## Recommended Minimum for Production

For a counselling system where **students make real decisions**:

> **Minimum recommended model: 7B parameters**
> 
> - Better numeric grounding
> - More reliable negative constraint following
> - Acceptable latency on modern hardware

If using 1.5B model:
- Add post-processing filter for forbidden words
- Implement numeric validation layer
- Use as fallback only, not primary

---

## Test Command

```bash
python3 src/tests/test_harness.py
```

Last tested: 2026-02-08
Model: qwen2.5:1.5b-instruct
Result: 10/13 PASSED (77%)
