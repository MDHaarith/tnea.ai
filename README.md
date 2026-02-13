# 🎓 TNEA AI — Expert Engineering Counsellor

An AI-powered counselling assistant for Tamil Nadu Engineering Admissions (TNEA). Helps students with rank prediction, college suggestions, choice-filling strategy, trend analysis, and career guidance.

## Features

- **Rank & Percentile Prediction** — ML-based prediction using 5 years of historical data (2020–2025)
- **College Suggestions** — Data-driven recommendations categorized as Safe / Moderate / Ambitious
- **Geo-Located Search** — Haversine distance-based college filtering using real coordinates
- **Choice-Filling Strategy** — Priority table generation for TNEA counselling rounds
- **Trend Analysis** — Year-over-year cutoff trend analysis per branch with real data
- **Career & Skill Guidance** — Branch-to-career mapping and skill roadmaps
- **Safety-First AI** — Anti-hallucination prompts, probabilistic language enforcement, data grounding

## Architecture

```
Streamlit UI / CLI
    └── CounsellorAgent (orchestrator)
         ├── IntentRouter (local classifier + LLM fallback)
         ├── SessionMemory (JSON file persistence)
         ├── DataEngine (singleton, indexed JSON/CSV loader)
         ├── Predictor (RandomForest + interpolation)
         ├── GeoLocator (haversine distance search)
         ├── ChoiceStrategy (Safe/Moderate/Ambitious categorizer)
         ├── TrendAnalysis (real YoY cutoff analysis)
         ├── ReasoningEngine (prompt builder)
         ├── ResponseFormatter (markdown tables)
         ├── SkillSearch / CareerMapper (LLM-powered)
         └── LLMClient (OpenAI-compatible NVIDIA API)
```

## Data

| Dataset | Records | Source |
|---------|---------|--------|
| Colleges | 448 | TNEA Official |
| Cutoff Records | 15,643 | 2020–2024 |
| Seat Matrix | 3,486 | TNEA Official |
| Percentile Ranges | 743 | 2020–2025 |
| Districts | 44 | All Tamil Nadu |

## Setup

### Prerequisites

- Python 3.10+
- NVIDIA API key (free tier supported)

### Installation

```bash
# Clone the repo
git clone https://github.com/MDHaarith/tnea.ai.git
cd tnea.ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_API_KEY` | ✅ | — | NVIDIA API key for LLM |
| `NVIDIA_API_BASE` | ❌ | `https://integrate.api.nvidia.com/v1` | API base URL |
| `MODEL_NAME` | ❌ | `qwen/qwen3-coder-480b-a35b-instruct` | Model identifier |
| `DEBUG` | ❌ | `false` | Enable debug logging |

## Usage

### Streamlit UI (Recommended)

```bash
cd src
streamlit run streamlit_app.py
```

### CLI Mode

```bash
cd src
python run.py
```

### Running Tests

```bash
cd src
python tests/test_harness.py
```

## Key Design Decisions

- **Local intent classification first** — Keyword/regex classifier handles ~80% of queries without API calls, cutting costs in half
- **Indexed data lookups** — Cutoffs and seats indexed by college_code for O(1) retrieval (vs O(n) linear scan)
- **Haversine geo search** — Real distance calculation using lat/lng coordinates for all 448 colleges
- **Frozen prompts** — All production prompts versioned and frozen (`prompt_v1.0.json`) to prevent regression
- **Anti-hallucination** — AI responses grounded in actual database data; placement/salary figures never fabricated

## License

Private — All rights reserved.
