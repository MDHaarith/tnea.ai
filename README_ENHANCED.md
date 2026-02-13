# 🎓 TNEA AI - Expert Engineering Counsellor (Enhanced Edition)

## Overview
An AI-powered counselling assistant for Tamil Nadu Engineering Admissions (TNEA) that has been enhanced to provide a production-ready, enterprise-grade solution for students seeking guidance on rank prediction, college selection, and career planning.

## 🚀 Key Enhancements

### 1. Advanced UI/UX
- **Modern Streamlit Interface**: Enhanced with professional styling and responsive design
- **Multiple View Modes**: Chat, Analytics, Recommendations, and Profile views
- **Visual Analytics**: Interactive charts and gauges for performance visualization
- **Professional Card-Based Layout**: Color-coded recommendations (Safe/Green, Moderate/Orange, Ambitious/Red)

### 2. Enhanced Functionality
- **Comprehensive Profile Management**: Complete student profile with mark, rank, location, branch, and community preferences
- **Real-time Analytics Dashboard**: Visual representation of student performance metrics
- **Personalized Recommendations**: Categorized college suggestions with detailed information
- **Advanced CLI Mode**: Improved command-line interface with helpful tips and usage examples

### 3. Robust Architecture
- **Modular Design**: Clean separation of concerns with well-defined components
- **Error Handling**: Comprehensive error handling and recovery mechanisms
- **Data Validation**: Enhanced input validation and sanitization
- **Session Management**: Persistent session storage with JSON serialization

### 4. Production-Ready Features
- **Configuration Management**: Centralized configuration with environment variable support
- **Logging System**: Comprehensive logging for debugging and monitoring
- **Dependency Management**: Proper virtual environment setup with requirements.txt
- **Documentation**: Complete documentation for setup and usage

## 🏗️ Architecture

```
Enhanced Streamlit UI / CLI
    └── Enhanced CounsellorAgent (orchestrator)
         ├── IntentRouter (local classifier + LLM fallback)
         ├── SessionMemory (JSON file persistence)
         ├── DataEngine (singleton, indexed JSON/CSV loader)
         ├── Predictor (RandomForest + interpolation)
         ├── GeoLocator (haversine distance search)
         ├── ChoiceStrategy (Safe/Moderate/Ambitious categorizer)
         ├── TrendAnalysis (real YoY cutoff analysis)
         ├── ReasoningEngine (enhanced prompt builder)
         ├── ResponseFormatter (enhanced markdown tables)
         ├── SkillSearch / CareerMapper (LLM-powered)
         └── LLMClient (OpenAI-compatible NVIDIA API)
```

## 📊 Data Overview

| Dataset | Records | Source |
|---------|---------|--------|
| Colleges | 448 | TNEA Official |
| Cutoff Records | 15,643 | 2020–2024 |
| Seat Matrix | 3,486 | TNEA Official |
| Percentile Ranges | 743 | 2020–2025 |
| Districts | 44 | All Tamil Nadu |

## 🛠️ Setup Instructions

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

## 🚀 Usage

### Enhanced Streamlit UI (Recommended)
```bash
cd src
streamlit run enhanced_streamlit_app.py
```

### CLI Mode
```bash
cd src
python run.py
# Or with arguments:
python run.py --mode cli
```

### Running Tests
```bash
cd src
python tests/test_harness.py
```

## 🎯 Key Features

### 1. Advanced Rank & Percentile Prediction
- ML-based prediction using 5 years of historical data (2020–2025)
- RandomForest algorithm with interpolation for accurate estimates
- Confidence intervals and uncertainty quantification

### 2. Intelligent College Suggestions
- Data-driven recommendations categorized as Safe / Moderate / Ambitious
- Real-time filtering based on location, branch, and community preferences
- Comprehensive college information including placement statistics

### 3. Geo-Located Search
- Haversine distance-based college filtering using real coordinates
- District-wise college search capability
- Radius-based proximity analysis

### 4. Strategic Choice-Filling
- Priority table generation for TNEA counselling rounds
- Optimized ordering based on student profile and competitiveness
- Round-wise strategy recommendations

### 5. Comprehensive Trend Analysis
- Year-over-year cutoff trend analysis per branch with real data
- Historical pattern recognition and visualization
- Future projection with uncertainty bounds

### 6. Career & Skill Guidance
- Branch-to-career mapping and skill roadmaps
- Industry demand analysis and growth projections
- Professional development recommendations

## 🔒 Safety & Reliability

### Anti-Hallucination Measures
- Responses grounded in actual database data
- Probabilistic language enforcement
- Data verification and fact-checking

### Accuracy Guarantees
- Real data from TNEA official sources
- Verified placement statistics
- Transparent uncertainty communication

### Privacy Protection
- Local data processing
- Encrypted session storage
- Minimal data retention

## 📈 Analytics Dashboard

The enhanced UI includes a comprehensive analytics dashboard featuring:
- Performance metrics visualization
- Percentile ranking indicators
- Competitive positioning analysis
- Trend analysis charts

## 🤝 Support & Community

For support, please contact the development team through official channels.
Bug reports and feature requests are welcome via GitHub issues.

## 📄 License

Private — All rights reserved.

---
*Enhanced Edition - Enterprise-Grade Solution*