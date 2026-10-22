# cleanup_ui.py -> Removes CSV upload, simplifies sidebar, translates to English
from pathlib import Path
import re

p = Path("app.py")
s = p.read_text(encoding="utf-8")
log = []

# ========== 1. TRANSLATE HINGLISH TO ENGLISH ==========
translations = [
    # Main description
    ('Public social comments ko AI-powered FOR / AGAINST / ABSTAIN votes mein convert karke transparent, manipulation-proof voting results nikalne wala intelligent system.',
     'An intelligent system that converts public social comments into AI-powered FOR / AGAINST / ABSTAIN votes, delivering transparent and manipulation-proof voting results.'),
    
    # Sidebar labels
    ('Comments to fetch', 'Comments to Fetch'),
    ('Max comments to analyze (speed vs coverage)', 'Max Comments to Analyze'),
    ('Auto fallback to demo data', 'Auto Fallback to Demo Data'),
    ('Demo dataset', 'Demo Dataset'),
    ('Fast rule-based mode', 'Fast Rule-Based Mode'),
    ('Clear cache', 'Clear Cache'),
    ('Cache cleared.', 'Cache cleared.'),
    
    # Buttons
    ('Analyze URL', 'Analyze URL'),
    ('Run Demo', 'Run Demo'),
    ('Reset', 'Reset'),
    
    # Status messages
    ('Fetching comments...', 'Fetching comments...'),
    ('Fetch done', 'Fetch done'),
    ('Analyzing', 'Analyzing'),
    ('Analysis complete', 'Analysis complete'),
    ('Live fetch failed/unavailable. Using authorized demo dataset.',
     'Live fetch failed. Using authorized demo dataset.'),
    ('Live fetch failed and fallback is disabled.',
     'Live fetch failed and fallback is disabled.'),
    ('Using cached comments for this post.',
     'Using cached comments for this post.'),
    ('Invalid Instagram URL. Use /p/, /reel/, or /tv/ link.',
     'Invalid Instagram URL. Use /p/, /reel/, or /tv/ link.'),
    ('Please enter an Instagram URL.',
     'Please enter an Instagram URL.'),
    
    # Metrics
    ('Total Comments', 'Total Comments'),
    ('Brand Health (/100)', 'Vote Integrity'),
    ('Positive', 'FOR Votes'),
    ('Neutral', 'ABSTAIN'),
    ('Negative', 'AGAINST Votes'),
    ('Toxic', 'Invalid Ballots'),
    ('Top Emotion', 'Dominant Emotion'),
    
    # Risk status
    ('Risk Status:', 'Verdict:'),
    ('Healthy', '✅ APPROVED'),
    ('Monitor', '⚠️ REVIEW NEEDED'),
    ('Warning', '⚠️ CONTROVERSIAL'),
    ('Critical', '❌ REJECTED'),
    
    # Tabs
    ('📊 Insights', '📊 Analytics'),
    ('🗳️ Social Voting', '🗳️ Voting Results'),
    ('💬 Comment Explorer', '💬 Comment Analysis'),
    ('📄 Report', '📄 Export Report'),
    
    # Low sample warning
    ('Low sample size: sirf', 'Low sample size: only'),
    ('comments mile.', 'comments fetched.'),
    ('Insights ki statistical confidence kam hogi — fetch amount badhao ya koi active post try karo.',
     'Statistical confidence may be low. Increase fetch amount or try a more active post.'),
]

for old, new in translations:
    if old in s:
        s = s.replace(old, new)
        log.append(f"Translated: '{old[:40]}...' → '{new[:40]}...'")

# ========== 2. REMOVE UPLOAD CSV SECTION ==========
# Find and remove the entire Upload CSV block
csv_pattern = r'Upload CSV\s*\n\s*col_csv.*?(?=\n\s*col_demo|\n\s*col_reset|\n\s*# Actions)'
if re.search(csv_pattern, s, re.DOTALL):
    s = re.sub(csv_pattern, '', s, flags=re.DOTALL)
    log.append("Removed Upload CSV section")
else:
    # Fallback: remove specific lines
    lines_to_remove = [
        'Upload CSV',
        'col_csv, col_demo, col_reset = st.columns([3, 1, 1])',
        'with col_csv:',
        'csv_file = st.file_uploader("Upload CSV", type=["csv"])',
    ]
    for line in lines_to_remove:
        if line in s:
            s = s.replace(line, '')
            log.append(f"Removed: {line}")

# ========== 3. SIMPLIFY SIDEBAR ==========
# Remove complex settings, keep only essential ones
sidebar_removals = [
    'max_analyze = st.slider("Max comments to analyze (speed vs coverage)",',
    'fast_mode = st.checkbox(',
    'Demo dataset',
    'demo_dataset = st.selectbox(',
    'Clear cache',
    'if st.button("Clear cache"):',
]

for removal in sidebar_removals:
    if removal in s:
        # Find the line and remove it + next few lines if it's a multi-line statement
        lines = s.split('\n')
        new_lines = []
        skip_next = 0
        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                continue
            if removal in line:
                # Check if it's a multi-line statement
                if line.strip().endswith(',') or line.strip().endswith('('):
                    skip_next = 2  # Skip next 2 lines
                log.append(f"Removed sidebar setting: {removal[:50]}")
            else:
                new_lines.append(line)
        s = '\n'.join(new_lines)

# ========== 4. FIX BRAND HEALTH METRIC TRUNCATION ==========
if 'Brand Health (/100)' in s:
    s = s.replace('Brand Health (/100)', 'Vote Integrity')
    log.append("Fixed Brand Health metric label")

# ========== 5. UPDATE PAGE CONFIG ==========
if 'page_title="AI-Based Social Voting System"' in s:
    log.append("Page title already updated")

# ========== 6. FIX UPLOAD CSV REFERENCE IN ACTIONS ==========
# Remove csv_file variable references
if 'csv_file is not None:' in s:
    # Find and remove the entire CSV handling block
    csv_block_start = s.find('if csv_file is not None:')
    if csv_block_start != -1:
        csv_block_end = s.find('\n\nif reset_btn:', csv_block_start)
        if csv_block_end != -1:
            s = s[:csv_block_start] + s[csv_block_end:]
            log.append("Removed CSV file handling logic")

# ========== 7. UPDATE SUBTITLE ==========
old_subtitle = 'st.caption("Powered by CommentSense AI engine — sentiment • toxicity • emotion • aspects")'
new_subtitle = 'st.caption("Powered by CommentSense AI Engine — Sentiment • Toxicity • Emotion • Aspect Analysis")'
if old_subtitle in s:
    s = s.replace(old_subtitle, new_subtitle)
    log.append("Updated subtitle to English")

# ========== 8. FIX COLUMN LAYOUT (remove col_csv) ==========
# Change from 3 columns to 2 columns for Run Demo and Reset
if 'col_csv, col_demo, col_reset = st.columns([3, 1, 1])' in s:
    s = s.replace('col_csv, col_demo, col_reset = st.columns([3, 1, 1])',
                  'col_demo, col_reset = st.columns([1, 1])')
    log.append("Fixed column layout (removed CSV column)")

# ========== SAVE ==========
p.write_text(s, encoding="utf-8")
print("✅ UI cleanup complete:")
for line in log:
    print(f"   - {line}")
print(f"\n📊 Total changes: {len(log)}")