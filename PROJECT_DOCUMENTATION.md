# Smart Lab Report Analyser
## Project Documentation & Literature Review

---

## Abstract

The **Smart Lab Report Analyser** is an intelligent healthcare informatics system that automates the extraction, analysis, and interpretation of medical laboratory test reports. The system leverages Optical Character Recognition (OCR), pattern-based Natural Language Processing (NLP), and rule-based clinical interpretation to transform unstructured lab reports (PDF/images) into structured, actionable health insights. This project addresses the critical need for automating the time-consuming manual interpretation of lab results while maintaining clinical safety through non-diagnostic, informational outputs.

**Keywords:** OCR, Medical Report Analysis, NLP, Healthcare Informatics, Laboratory Information System, Python, FastAPI, Streamlit

---

## 1. Introduction

### 1.1 Problem Statement

Healthcare facilities generate millions of laboratory test reports daily. Manual interpretation of these reports is:
- **Time-consuming**: Clinicians spend significant time reviewing and explaining lab results
- **Error-prone**: Manual data entry and interpretation can introduce errors
- **Inconsistent**: Interpretation quality varies across practitioners
- **Access-limited**: Patients often struggle to understand their own lab reports

### 1.2 Proposed Solution

This project presents an end-to-end intelligent system that:
1. Extracts text from lab report documents (PDF and images)
2. Parses extracted text to identify medical parameters and values
3. Compares results against standard reference ranges
4. Generates patient-friendly insights and explanations
5. Produces downloadable PDF reports

### 1.3 Objectives

- Develop an OCR-based text extraction module for medical documents
- Implement regex-based pattern matching for parameter identification
- Create a rule-based interpretation engine with confidence scoring
- Build a user-friendly web interface for report upload and analysis
- Generate comprehensive, downloadable analysis reports

---

## 2. Literature Review

### 2.1 OCR for Medical Document Digitization

Optical Character Recognition (OCR) is foundational for converting scanned medical documents into machine-readable text. Research has shown that deep learning-based OCR algorithms achieve **78-95% accuracy** for medical laboratory test reports [1][2].

**Key Papers:**

| Paper | Key Contribution | Relevance |
|-------|------------------|-----------|
| "An Information Extraction Pipeline for Laboratory Test Reports" (NIH) | Multi-stage pipeline with OCR and NER using CRF | *Base architecture reference* |
| "DeepSSR: Deep Learning for Structurizing Paper-based Medical Reports" | YOLOv3 for table detection, CRNN for text recognition | *Advanced extraction techniques* |
| "Deep Learning OCR Post-Correction using RoBERTa" | Transformer-based OCR error correction | *Error handling strategies* |

**Challenges Identified:**
- Non-standard document layouts across laboratories
- Low-quality scanned documents
- Mixed data types (text, numeric values, units)
- Medical terminology not in general lexicons

### 2.2 Natural Language Processing in Healthcare

NLP enables the extraction of structured information from unstructured medical text. Transformer-based models like **BERT** and **BioBERT** have achieved state-of-the-art results in medical text classification [3].

**Techniques Used in Literature:**

1. **Named Entity Recognition (NER)**: Identifies medical entities (test names, values, units)
2. **Information Extraction (IE)**: Converts unstructured text to structured data
3. **Text Classification**: Categorizes lab results into diagnostic categories

**This Project's Approach:**
- Uses **regex-based pattern matching** for parameter extraction
- Implements **unit-aware normalization** for value comparison
- Assigns **confidence scores** (High/Medium/Low) based on extraction certainty

### 2.3 Automated Lab Report Interpretation

AI-powered interpretation systems can reduce diagnosis time by up to **60%** while improving consistency [4]. However, these systems must balance automation with clinical safety.

**Key Considerations:**
- Non-diagnostic language to avoid liability
- Clear disclaimers for AI-generated content
- Reference range comparison rather than diagnosis
- Human-in-the-loop verification

### 2.4 Related System Architectures

| System | Architecture | OCR Tool | NLP Approach |
|--------|-------------|----------|--------------|
| Lab-AI (arXiv) | RAG-based LLM | Commercial | LLM with retrieval |
| DeepSSR (NIH) | Deep learning pipeline | Custom CNN | Table extraction |
| **This Project** | Modular pipeline | pytesseract/pdfplumber | Regex + Rules |

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                      (Streamlit Frontend)                        │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP API
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       BACKEND SERVER                             │
│                       (FastAPI + Uvicorn)                        │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  Extractor  │─▶│   Parser    │─▶│Interpretation│─▶│ Report  │ │
│  │   Module    │  │   Module    │  │   Module    │  │Generator│ │
│  │(OCR/PDF)    │  │  (Regex)    │  │  (Rules)    │  │  (PDF)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │    Database     │                          │
│                    │   (SQLite)      │                          │
│                    └─────────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Module Description

#### 3.2.1 Text Extraction Module (`extractor.py`)
- **Purpose**: Extract text from uploaded lab reports
- **Technologies**: 
  - `pdfplumber` for PDF text extraction
  - `pytesseract` for image OCR
- **Supported Formats**: PDF, PNG, JPG, JPEG, TIFF, BMP

#### 3.2.2 Parser Module (`parser.py`)
- **Purpose**: Identify and extract medical parameters from text
- **Features**:
  - 60+ medical parameter patterns
  - Unit-aware value normalization
  - Confidence scoring system (High/Medium/Low)
  - Reference range comparison

**Parameters Covered:**
- Complete Blood Count (CBC): Hemoglobin, RBC, WBC, Platelets, etc.
- Metabolic Panel: Glucose, Creatinine, BUN, Electrolytes
- Liver Function Tests: SGOT, SGPT, Bilirubin, ALP
- Lipid Profile: Cholesterol, HDL, LDL, Triglycerides
- Thyroid Panel: TSH, T3, T4, FT3, FT4
- Vitamins: Vitamin D, B12
- And more...

#### 3.2.3 Interpretation Module (`interpretation.py`)
- **Purpose**: Generate patient-friendly insights
- **Features**:
  - 100+ rule-based interpretations
  - Status classification (Normal/High/Low)
  - Non-diagnostic, safe medical language
  - Clear disclaimers

#### 3.2.4 Report Generator (`report_generator.py`)
- **Purpose**: Create downloadable PDF reports
- **Technology**: ReportLab
- **Output**: Professional, formatted analysis reports

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Streamlit | User interface |
| Backend | FastAPI | REST API server |
| Server | Uvicorn | ASGI server |
| OCR (PDF) | pdfplumber | PDF text extraction |
| OCR (Image) | pytesseract | Image text extraction |
| Image Processing | Pillow | Image handling |
| Data Processing | pandas | Data manipulation |
| Visualization | Altair | Charts and graphs |
| PDF Generation | ReportLab | Report creation |
| Database | PostgreSQL (via Supabase and psycopg2) | Report history |

---

## 5. Implementation Details

### 5.1 Text Extraction Algorithm

```python
def extract_text(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        return extract_from_pdf(file_path)  # pdfplumber
    elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return extract_from_image(file_path)  # pytesseract
```

### 5.2 Parameter Extraction with Confidence Scoring

The system uses multi-pattern matching with confidence levels:

```python
PATTERNS = {
    "Hemoglobin": [
        (r"Hemoglobin\s*\(Hb\)\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "High"),
        (r"Hb\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "Medium"),
    ],
    # ... 60+ parameters
}
```

**Confidence Levels:**
- **High**: Full parameter name matched (e.g., "Hemoglobin")
- **Medium**: Abbreviation matched (e.g., "Hb")
- **Low**: Ambiguous match or fallback pattern

### 5.3 Unit Normalization

The system normalizes different unit representations:

```python
UNIT_MULTIPLIERS = {
    "cells/ul": 1, "cells/µl": 1,
    "10^3/ul": 1000, "10^3/µl": 1000,
    "g/dl": 1, "g/l": 0.1,
    # ... comprehensive unit conversion
}
```

---

## 6. Results and Discussion

### 6.1 System Capabilities

| Feature | Status |
|---------|--------|
| PDF text extraction | ✓ Implemented |
| Image OCR | ✓ Implemented |
| 60+ parameter recognition | ✓ Implemented |
| Unit normalization | ✓ Implemented |
| Confidence scoring | ✓ Implemented |
| Rule-based insights | ✓ Implemented |
| PDF report generation | ✓ Implemented |
| Report history tracking | ✓ Implemented |

### 6.2 Advantages

1. **Privacy-First**: All processing happens locally; no data sent to external servers
2. **Extensible**: Easy to add new parameters and interpretation rules
3. **Safe**: Non-diagnostic language with clear disclaimers
4. **User-Friendly**: Premium medical-grade UI design
5. **Portable**: Python-based, runs on any platform

### 6.3 Limitations

1. Requires Tesseract OCR installation for image processing
2. Accuracy depends on document quality
3. Limited to Indian and common international reference ranges
4. Rule-based (not ML-based) interpretation

---

## 7. References

[1] "An Information Extraction Pipeline for Laboratory Test Reports," *PubMed Central*, NIH. Available: https://www.ncbi.nlm.nih.gov/pmc/

[2] "DeepSSR: A Deep Learning System for Structurizing Paper-based Medical Reports," *PubMed Central*, NIH. Available: https://www.ncbi.nlm.nih.gov/pmc/

[3] "Classification of Free-Text Laboratory Results Using Transformer-Based NLP," *IEEE Xplore*. Available: https://ieeexplore.ieee.org/

[4] "Automated Disease Prediction from Medical Reports using Machine Learning," *IJRPR*. Available: https://ijrpr.com/

[5] "Lab-AI: Personalized Lab Test Interpretation using Retrieval-Augmented Generation," *arXiv*. Available: https://arxiv.org/

[6] "Deep Learning OCR Post-Correction using RoBERTa for Medical Reports," *ResearchGate*. Available: https://www.researchgate.net/

[7] "NLP for Pathology Data Extraction from Clinical Reports," *PubMed Central*, NIH. Available: https://www.ncbi.nlm.nih.gov/pmc/

[8] "Optimizing OCR for Medical Records using Deep Learning," *IEEE Xplore*. Available: https://ieeexplore.ieee.org/

---

## 8. Future Enhancements

1. **Machine Learning Integration**: Replace rule-based interpretation with trained ML models
2. **Multi-Language Support**: Add support for regional languages
3. **Cloud Deployment**: Deploy as a cloud service with user authentication
4. **Mobile Application**: Develop companion mobile apps
5. **EHR Integration**: Enable integration with Electronic Health Record systems
6. **Trend Analysis**: Track parameter changes over time with historical data

---

## 9. Conclusion

The Smart Lab Report Analyser successfully demonstrates the application of OCR and NLP techniques in healthcare informatics. By combining text extraction, pattern-based parsing, and rule-based interpretation, the system provides a practical solution for automated lab report analysis while maintaining clinical safety through non-diagnostic outputs.

---

**Prepared by:** Smart Lab Report Analyser Project Team  
**Date:** January 2026  
**Version:** 1.0

---

## Appendix A: Running the Application

### Prerequisites
- Python 3.8+
- Tesseract OCR (for image processing)

### Installation
```bash
cd Smart_Lab_Report_Analyser
pip install -r requirements.txt
```

### Running
**Terminal 1 (Backend):**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
python -m streamlit run frontend/app.py
```

Access the application at: http://localhost:8501
