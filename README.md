<div align="center">

# 🗳️ CommentSense AI

### AI-Based Social Voting System & Brand Intelligence Dashboard

**Turn raw Instagram comments into actionable brand intelligence and transparent, manipulation-resistant FOR / AGAINST / ABSTAIN votes.**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Transformers](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?logo=huggingface&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?logo=pytorch&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Hackathon%20Ready-success)

</div>

---


## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Social Voting Engine](#-social-voting-engine)
- [Reports & Exports](#-reports--exports)
- [Data Sources & Fallback Strategy](#-data-sources--fallback-strategy)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Responsible Use](#-responsible-use)
- [Contributing](#-contributing)
- [Author](#-author)

---

## 🔍 Overview

Brands, campaigns and public proposals receive thousands of comments on social media, but reading them manually is slow, subjective and easy to manipulate.

**CommentSense AI** automates this. It collects comments from an Instagram post or reel (or from a CSV file), runs them through an NLP pipeline, and presents the results in an interactive dashboard:

- **What do people feel?** Sentiment, emotion and toxicity analysis for every comment.
- **What are they talking about?** Aspect-based keyword insights.
- **How healthy is the brand?** A Brand Health Score with a crisis and risk alert.
- **What is the public verdict?** Every comment is converted into a **FOR / AGAINST / ABSTAIN** ballot, with duplicate and bot detection to protect the integrity of the result.

The app is built with Streamlit, so the whole system runs locally in a browser with a single command.
<img width="957" height="500" alt="image" src="https://github.com/user-attachments/assets/aebbeaa1-a650-4aa7-9a22-cc32edf7febd" />

---

## ✨ Key Features

### 📥 Flexible Input
| Mode | Description |
|------|-------------|
| **Instagram URL** | Paste a Post, Reel or TV link (`/p/`, `/reel/`, `/tv/`) |
| **CSV Upload** | Analyze your own exported comment data |
| **Demo Mode** | One-click demo with four bundled datasets: `mixed`, `healthy`, `crisis`, `hinglish` |

### 🧠 AI Analysis
- **Sentiment**: positive, neutral or negative, with a confidence score
- **Emotion**: joy, anger, sadness, fear, surprise, disgust and neutral
- **Toxicity**: toxic comment detection with scores
- **Aspect-Based Insights**: keyword and aspect extraction with per-aspect sentiment
- **Hinglish support**: a dedicated demo dataset for mixed Hindi-English comments
- **Fast Rule-Based Mode**: skips transformer models when downloads are slow or unavailable

### 📊 Interactive Dashboard
<img width="931" height="100" alt="image" src="https://github.com/user-attachments/assets/52916e6f-3961-41cd-8dd4-6eb3cf2f7a9c" />

- Brand Health Score (out of 100) and a 7-card KPI row
- Sentiment pie chart, emotion bar chart, toxicity gauge, aspect-based stacked bar chart
- Executive summary generated automatically from the analysis
- Colour-coded **Crisis & Action Alert** (Healthy, Monitor, Warning, Critical)
- **Comment Explorer** with filters for sentiment, emotion, aspect, free-text search and toxic-only. Toxic comments are hidden by default and can be revealed.

### 🗳️ Social Voting Engine
- Converts each comment into a FOR / AGAINST / ABSTAIN vote
- Toxic comments are marked **invalid ballots**
- Optional **duplicate and bot ballot removal** with visible stuffing evidence
- **Vote Integrity Score** (0-100), turnout and winning margin
- Verdict banner, including an *unreliable result* warning when manipulation is suspected
- In-app manual voting with double-vote protection
- Downloadable voting result as JSON

### 📄 Reports
- CSV, JSON and (optional) PDF export of the full analysis

---

## ⚙️ How It Works

```
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│  Input       │   │  Fetch &     │   │  AI Analysis    │   │  Dashboard       │
│  URL / CSV / │──▶│  Cache       │──▶│  Sentiment      │──▶│  Insights        │
│  Demo        │   │  (fallback)  │   │  Emotion        │   │  Social Voting   │
└──────────────┘   └──────────────┘   │  Toxicity       │   │  Comment Explorer│
                                      │  Aspects        │   │  Reports         │
                                      └─────────────────┘   └──────────────────┘
```
<img width="340" height="380" alt="Screenshot 2026-10-19 123317" src="https://github.com/user-attachments/assets/104b8bf9-8a9e-4b24-92ee-38e06dd7c6b3" />

1. **Ingest**: comments are fetched from Instagram, a CSV or the demo data. Results are cached.
2. **Analyze**: the analyzer scores each comment (up to the configured analysis limit).
3. **Aggregate**: metrics, brand health, risk level and an executive summary are computed.
4. **Vote**: comments are converted into ballots, cleaned and counted.
5. **Present and export**: results are shown in the dashboard and can be downloaded.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend / App** | [Streamlit](https://streamlit.io/) with custom glassmorphism CSS |
| **Visualization** | [Plotly](https://plotly.com/python/) |
| **NLP / ML** | [Hugging Face Transformers](https://huggingface.co/docs/transformers) and [PyTorch](https://pytorch.org/), with a rule-based fallback |
| **Data Handling** | [pandas](https://pandas.pydata.org/) |
| **Instagram Fetching** | [instagrapi](https://github.com/subzeroid/instagrapi) |
| **Reporting** | [ReportLab](https://www.reportlab.com/) (PDF) |
| **Configuration** | [python-dotenv](https://pypi.org/project/python-dotenv/) |

---

## 📁 Project Structure

```
commentsense-ai/
├── app.py               # Streamlit entry point: UI, tabs, charts, voting view
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment configuration
├── .gitignore
├── .streamlit/          # Streamlit configuration
├── scripts/             # Helper / utility scripts
└── src/
    ├── analyzer.py      # Sentiment, toxicity, emotion and aspect analysis
    ├── fetcher.py       # Comment fetching from URL and CSV
    ├── providers.py     # Data providers and demo dataset loader
    ├── cache.py         # Comment caching and cache clearing
    ├── metrics.py       # Brand health score and risk status
    ├── summary.py       # Executive summary generation
    ├── voting.py        # Social ballot computation and manual voting
    └── report.py        # CSV / JSON / PDF export
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+**
- `pip`
- An internet connection on first run, to download the Hugging Face models (not needed in Fast Rule-Based Mode)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Gouravkim/commentsense-ai.git
cd commentsense-ai

# 2. Create and activate a virtual environment
python -m venv venv

# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Create your environment file
cp .env.example .env        # Windows: copy .env.example .env
```

### Run the App

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser, then click **Run Demo** to see the dashboard immediately.

---

## 🔧 Configuration

Copy `.env.example` to `.env` and adjust the values you need. All variables are optional.

| Variable | Description | Default |
|----------|-------------|---------|
| `IG_AUTHORIZED_COMMENTS_FILE` | Path to a local JSON file of authorized comments (a list, or a dict keyed by shortcode) | *empty* |
| `IG_ACCESS_TOKEN` | Placeholder for a future official Instagram Graph API integration | *empty* |
| `IG_USER_ID` | Placeholder for the Graph API user ID | *empty* |
| `IG_MEDIA_ID` | Placeholder for the Graph API media ID | *empty* |
| `INSTAGRAM_REQUEST_AMOUNT` | Number of comments to request from Instagram | `100` |
| `INSTAGRAM_DELAY_MIN` | Minimum delay between requests (seconds) | `2` |
| `INSTAGRAM_DELAY_MAX` | Maximum delay between requests (seconds) | `5` |
| `COMMENTSENSE_DISABLE_TRANSFORMERS` | Force rule-based mode if transformer models are slow or unavailable | `false` |

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### Sidebar Settings (in-app)

| Setting | Purpose |
|---------|---------|
| **Comments to Fetch** (50-1000) | How many comments to pull from the source |
| **Max Comments to Analyze** (50-500) | Caps analysis size to keep the app fast |
| **Auto Fallback to Demo Data** | Loads demo data if the live fetch fails |
| **Demo Dataset** | Choose `demo_mixed`, `demo_healthy`, `demo_crisis` or `demo_hinglish` |
| **Fast Rule-Based Mode** | Skips transformer models for quick results |
| **Clear Cache** | Removes cached comments |

---

## 📖 Usage Guide

1. **Start the app** with `streamlit run app.py`.
2. **Choose a data source**
   - Paste an Instagram post or reel URL and click **Analyze URL**, or
   - Click **Run Demo** to use a bundled dataset.
3. **Explore the tabs**
   - **📊 Insights**: KPIs, charts, executive summary and crisis alert
   - **🗳️ Social Voting**: ballot results, integrity score and manual voting
   - **💬 Comment Explorer**: filter and search individual comments
   - **📄 Report**: download CSV, JSON or PDF
4. Click **Reset** to clear the current session and start over.

---

## 🗳️ Social Voting Engine

Every analyzed comment is treated as a ballot:

| Ballot | Meaning |
|--------|---------|
| ✅ **FOR** | The comment expresses support |
| ❌ **AGAINST** | The comment expresses opposition |
| 😐 **ABSTAIN** | The comment is neutral or undecided |
| 🚫 **INVALID** | The comment is toxic and not counted |

**Integrity protections**

- **Duplicate and bot filtering**: repeated comment text is flagged and can be removed before counting.
- **Ballot stuffing evidence**: a table shows the most duplicated comments and how many copies exist.
- **Vote Integrity Score**: a 0-100 score. Below 50, the verdict is shown as **unreliable**.
- **Double-vote protection**: manual votes are tied to a voter ID so each voter can vote once.

**Outputs**: FOR, AGAINST and ABSTAIN counts, decided turnout, winning margin, verdict banner and a downloadable `voting_result.json`.

---

## 📤 Reports & Exports

| Format | Contents |
|--------|----------|
| **CSV** | Per-comment analysis: sentiment, emotion, toxicity, aspects, scores |
| **JSON** | Full analysis with metadata and executive summary |
| **PDF** | Formatted report (requires `reportlab`, included in `requirements.txt`) |

Filenames include the source name and a UTC timestamp, for example `commentsense_20261022_153000_report.json`.

---

## 🛟 Data Sources & Fallback Strategy

The app tries several sources in order and always falls back gracefully:

1. **Cache**: reuses comments already fetched for the same post.
2. **instagrapi**: best-effort fetch of public comments.
3. **Authorized JSON provider** (optional): a local file set via `IG_AUTHORIZED_COMMENTS_FILE`.
4. **Demo dataset**: used automatically when live fetch fails and *Auto Fallback* is on.

The current data source is always displayed above the results (live, cached, CSV, demo or fallback demo), so you know what you are looking at.

---

## 🩺 Troubleshooting

| Problem | Fix |
|---------|-----|
| Live Instagram fetch fails | Instagram often blocks unauthenticated requests. Enable **Auto Fallback to Demo Data** or use **Run Demo**. |
| Model download is slow or fails | Turn on **Fast Rule-Based Mode** or set `COMMENTSENSE_DISABLE_TRANSFORMERS=true`. |
| `ModuleNotFoundError` | Activate your virtual environment and re-run `pip install -r requirements.txt`. |
| PDF download is missing | Install `reportlab` with `pip install reportlab`. |
| App feels slow | Lower **Max Comments to Analyze** in the sidebar. |
| Stale results | Click **Clear Cache** in the sidebar. |

---

## 🗺️ Roadmap

- [ ] Official Instagram Graph API integration
- [ ] Support for more platforms (YouTube, X, Facebook)
- [ ] Multilingual and improved Hinglish models
- [ ] Time-series trend tracking across posts
- [ ] Docker image and one-click cloud deployment
- [ ] Unit tests and CI pipeline

---

## ⚖️ Responsible Use

- Only analyze content you are **authorized** to access, and respect Instagram's Terms of Service and applicable privacy laws.
- Social comment voting is an **indicative signal**, not a legally binding or statistically representative poll.
- Model outputs can be wrong, especially for sarcasm, slang and code-mixed text. Treat results as decision support, not ground truth.

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 👤 Author

**Gourav**
B.Tech CSE (AI & ML) · Software Engineering Intern

- GitHub: [@Gouravkim](https://github.com/Gouravkim)

---

<div align="center">

⭐ If you find this project useful, please consider giving it a star.

</div>
