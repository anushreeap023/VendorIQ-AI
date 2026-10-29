# 📊 VendorIQ AI — Smart Vendor Proposal Comparison Agent

An AI-powered Streamlit application that helps procurement teams upload vendor
proposal PDFs, automatically extract key terms with Gemini, compare vendors
side-by-side, detect contract risks, score and rank vendors, and export a
polished procurement report.

## ✨ Features

- Upload up to 5 vendor proposal PDFs, auto text extraction (pdfplumber + PyPDF2 fallback)
- Gemini-powered structured extraction: cost, delivery, warranty, support, payment terms, features, risks
- Side-by-side comparison table
- AI recommendation engine with confidence score & trade-offs
- Risk detection module with Low/Medium/High severity + Contract Risk Alert System
- Vendor Scoring System (0–100) across 6 weighted criteria + ranking leaderboard
- Interactive analytics: radar chart, score bar chart, ranking chart, cost comparison chart
- AI-generated executive summary report
- AI negotiation suggestions + estimated savings analysis
- Procurement Health Score & Best Value for Money badge
- CSV and PDF export
- Dark/Light mode, responsive corporate dashboard UI
- **Offline demo mode**: the whole app works even without a Gemini API key, using rule-based fallbacks, so it's always demoable

## 🗂️ Project Structure

```
vendoriq/
├── app.py                     # Main Streamlit application
├── requirements.txt
├── README.md
├── utils/
│   ├── __init__.py
│   ├── pdf_extractor.py       # PDF text extraction
│   ├── gemini_client.py       # All Gemini API calls + offline fallbacks
│   ├── scoring.py             # Vendor scoring engine
│   ├── charts.py              # Plotly chart builders
│   └── export.py              # CSV / PDF report generation
├── assets/
│   └── style.css              # Corporate procurement theme
└── sample_data/
    └── generate_samples.py    # Generates 3 sample vendor proposal PDFs for demoing
```

## 🚀 Setup & Run

1. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Generate sample vendor proposals to test with**
   ```bash
   python sample_data/generate_samples.py
   ```
   This creates 3 ready-to-upload demo PDFs in `sample_data/`.

4. **(Optional) Get a Gemini API key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and create a free API key.
   - You can paste it directly into the app's sidebar at runtime — no `.env` file required.
   - Without a key, the app still runs fully in **offline demo mode** with heuristic extraction/scoring, so you can explore the entire UI.

5. **Run the app**
   ```bash
   streamlit run app.py
   ```
   The app opens automatically in your default browser (Chrome recommended) at
   `http://localhost:8501`.

## 🧭 How to Use

1. Go to **Upload & Overview**, paste your Gemini API key in the sidebar (optional), upload up to 5 vendor PDFs, and click **Analyze Proposals with AI**.
2. Explore **Comparison Table** for a full side-by-side breakdown.
3. Check **Scoring & Leaderboard** for ranked vendor scores.
4. Click **AI Recommendation** to get the best-vendor pick with reasoning.
5. Review **Risk Detection** for flagged contract risks by severity.
6. Explore **Analytics** for radar/bar/ranking/cost charts.
7. Generate the **Executive Summary** for a narrative procurement report.
8. Visit **Negotiation & Savings** for AI-generated negotiation talking points.
9. Head to **Export** to download the CSV summary or a full PDF report.

## 🛠️ Notes for Judges / Reviewers

- The app is built so evaluation never blocks on API availability — every AI
  feature has a graceful, clearly-labeled offline fallback.
- Gemini model used: `gemini-1.5-flash` (fast + cost-efficient, configurable
  in `utils/gemini_client.py`).
- All scoring logic is transparent and auditable in `utils/scoring.py`.
