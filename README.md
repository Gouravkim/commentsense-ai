# CommentSense AI

Instagram comments ko brand intelligence mein convert karne wala hackathon-ready AI dashboard.

## Features

- Input modes:
  - Instagram Post/Reel URL
  - CSV upload
  - Demo button
- Fetch strategy:
  - Best-effort instagrapi public fetch
  - Optional authorized JSON provider
  - Auto fallback to demo dataset
- AI analysis:
  - Sentiment
  - Toxicity
  - Emotion
  - Aspect-based keyword insights
- Dashboard:
  - Brand Health Score
  - Sentiment pie
  - Emotion bar
  - Toxicity gauge
  - Aspect stacked bar
  - Crisis alert
  - Executive summary
  - Comment explorer with filters
- Reports:
  - CSV download
  - JSON download
  - Optional PDF download

## Install

```bash
python -m venv venv
source venv/bin/activate
# Windows:
# venv\Scripts\activate

pip install -r requirements.txt