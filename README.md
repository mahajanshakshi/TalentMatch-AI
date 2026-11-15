# ⚡ TalentMatch AI

> **Enterprise AI Resume Parser & Intelligent Job Matcher**  
> Autonomous, explainable resume parsing and job description evaluation powered by Groq LLMs, Pydantic v2, and Streamlit.

---

## 🌟 Key Features

1. **Multi-Format Resume Ingestion**:
   - Native support for **PDF** (`PyMuPDF`) and **Word** (`.docx` via `python-docx`).
   - Automatic extraction, normalization, unicode cleanup, and bullet standardization.
   - Built-in token counter and character budgeting.

2. **Pydantic v2 Structured Extraction**:
   - Structured candidate profile extraction: contact info, professional summary, categorized skills (technical, tools, soft skills, domain), work experience highlights, education, certifications, and projects.
   - Structured job description extraction: required skills, preferred skills, soft skills, tools & platforms, minimum experience, and core deliverables.

3. **High-Speed Groq LLM Integration**:
   - Powered by official Groq Python SDK with `temperature=0.0` and JSON mode for deterministic, reproducible results.
   - Default high-performance model: `llama-3.3-70b-versatile` (with quick selector for `llama-3.1-8b-instant`).

4. **Explainable 4-Dimensional Scoring (0 - 100)**:
   - **Skills Alignment (40%)**: Coverage of mandatory and preferred technical competencies.
   - **Experience Relevance (25%)**: Seniority, years of experience, and domain track record.
   - **Responsibilities Fit (20%)**: Alignment with day-to-day role deliverables.
   - **Education & Credentials (15%)**: Academic degrees, certifications, and specialized credentials.
   - Deterministic mathematical weighting with categorical verdicts: `Strong Match`, `Good Match`, `Potential Match`, `Moderate Match`, `Low Match`.

5. **Actionable Insights & Skill Gap Analysis**:
   - Color-coded badges for Matched Required Skills, Matched Preferred Skills, Missing Critical Skills, and Bonus Proficiencies.
   - Strengths and Risk factor identification.
   - Targeted recommendations: Resume optimization tips, quantifiable impact framing, skill gap bridging, and interview prep focus.

6. **Interactive Analytics & Reporting**:
   - Plotly radial match score gauge and dimensional bar chart.
   - Downloadable reports in **Markdown (`.md`)** and structured **JSON (`.json`)**.
   - Built-in sample presets for instant one-click demonstration.

---

## 🏗️ Project Architecture

```
Ai Resume Analyzer/
├── .env                       # Environment variables (GROQ_API_KEY)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore file
├── requirements.txt           # Pinned production dependencies
├── config.py                  # Central configuration and environment loader
├── app.py                     # Streamlit application entry point
├── README.md                  # Documentation
│
├── core/                      # Modular backend services
│   ├── __init__.py
│   ├── document_parser.py     # PDF & DOCX extraction (PyMuPDF & python-docx)
│   ├── text_cleaner.py        # Text normalization and sanitization
│   ├── schemas.py             # Pydantic v2 data models
│   ├── groq_service.py        # Official Groq SDK client wrapper with JSON mode
│   ├── prompts.py             # System prompts for extraction and matching
│   ├── analyzer.py            # Orchestrator & mathematical scoring engine
│   ├── token_counter.py       # Tiktoken & heuristic token counter
│   ├── report_generator.py    # Markdown and JSON report exporter
│   └── samples.py             # Built-in demo resumes and job descriptions
│
├── ui/                        # Presentation layer
│   ├── __init__.py
│   ├── styles.py              # Custom glassmorphic CSS
│   └── components.py          # Plotly gauge, bar charts, and HTML pills
│
└── tests/                     # Automated test suite (pytest)
    ├── __init__.py
    ├── test_document_parser.py
    ├── test_text_cleaner.py
    ├── test_schemas.py
    ├── test_analyzer.py
    ├── test_report_generator.py
    └── test_token_counter.py
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup

The virtual environment `.venv` is already configured in this workspace.

To activate the virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Configure Your Groq API Key

Open the generated `.env` file in the root directory and paste your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
*(You can also paste the API key directly into the application's sidebar at runtime).*

### 3. Launch the Streamlit Application

Run the application using the virtual environment's Streamlit executable:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Open your browser at `http://localhost:8501`.

### 4. Run the Test Suite

Execute all automated unit and integration tests:
```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```

---

## 📊 Evaluation & Scoring Methodology

$$\text{Overall Score} = (S_{\text{skills}} \times 0.40) + (S_{\text{experience}} \times 0.25) + (S_{\text{responsibilities}} \times 0.20) + (S_{\text{education}} \times 0.15)$$

| Overall Score | Categorical Verdict | Recommendation |
| :---: | :---: | :--- |
| **85.0 – 100.0** | `Strong Match` | Fast-track to interview. High probability of immediate contribution. |
| **70.0 – 84.9** | `Good Match` | Strong candidate with minor skill or experience gaps. |
| **55.0 – 69.9** | `Potential Match` | Promising baseline qualifications; assess gaps during technical screening. |
| **40.0 – 54.9** | `Moderate Match` | Significant gaps in mandatory skills or required experience. |
| **0.0 – 39.9** | `Low Match` | Substantial misalignment with the core job requirements. |

---

## 🔒 Security & Privacy

- Extracted resume text and job descriptions are processed directly via Groq's official API.
- No resume data or API credentials are logged or persisted outside the session.
- `.env` and virtual environment files are protected in `.gitignore`.

