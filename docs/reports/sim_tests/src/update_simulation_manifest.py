import json
import re
from pathlib import Path
from datetime import datetime

# Configuration
# This script is located in docs/reports/sim_tests/src/
# We want to scan docs/reports/sim_tests/
BASE_DIR = Path(__file__).parent.parent.resolve()
MANIFEST_PATH = BASE_DIR / "LATEST_SIMULATIONS.json"

def clean_text(text):
    if not text: 
        return ""
    # Remove emojis and extra whitespace
    return re.sub(r'[^\w\s\(\)\.,-]', '', text).strip()

def parse_cycles(text):
    if not text:
        return 0
    # localized numbers 1,000,000 -> 1000000
    clean = text.replace(',', '').replace('_', '')
    try:
        return int(clean)
    except ValueError:
        return 0

def extract_description(content):
    # Try to find the first paragraph after Executive Summary
    match = re.search(r"## 📊 Executive Summary\s*\n\s*([^#\n]+)", content, re.MULTILINE)
    if not match:
        # Fallback 1: Try finding "## 1." (e.g. Physics Model)
        match = re.search(r"## 1\..+\n\s*([^#\n]+)", content, re.MULTILINE)
    
    if not match:
        # Fallback 2: First paragraph of text that is not a header and > 30 chars
        # Skip the first few lines which are likely metadata
        lines = content.split('\n')
        for i in range(5, len(lines)):
            line = lines[i].strip()
            if len(line) > 30 and not line.startswith('#') and not line.startswith('|') and not line.startswith('*'):
                return line[:117] + "..." if len(line) > 120 else line

    if match:
        desc = match.group(1).strip()
        # Clean up Markdown bolding/links in description
        desc = desc.replace('**', '').replace('`', '')
        if len(desc) > 150:
            return desc[:147] + "..."
        return desc
    return "Automated simulation report."

def scan_reports():
    reports = []
    
    print(f"Scanning {BASE_DIR} for markdown reports...")
    
    # Set stdout to utf-8 to avoid console errors
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    for file in BASE_DIR.glob("*.md"):
        # Skip known non-report files
        if file.name.upper() in ["README.MD", "INDEX.MD", "COPPELIASIM_SETUP.MD", "QUICK_START.MD", "COMPLETION_SUMMARY.MD"]:
            continue
        
        # Skip Roadmap
        if "ROADMAP" in file.name.upper():
            continue

        content = file.read_text(encoding="utf-8")
        
        # Regex Extraction
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        date_match = re.search(r"\*\*Date:\*\*\s+(.+)$", content, re.MULTILINE)
        status_match = re.search(r"\*\*Status:\*\*\s+(.+)$", content, re.MULTILINE)
        cycles_match = re.search(r"\*\*Cycles:\*\*\s+(.+)$", content, re.MULTILINE)
        
        # Must have title and at least one metadata field
        if title_match and (date_match or status_match or cycles_match):
            raw_title = title_match.group(1).strip()
            raw_status = status_match.group(1).strip() if status_match else "UNKNOWN"
            raw_date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
            
            # Normalize Status
            status = "PASS"
            if "FAIL" in raw_status.upper():
                status = "FAIL"
            elif "UNKNOWN" in raw_status.upper():
                status = "UNKNOWN"
            
            # Normalize Date
            try:
                date_val = raw_date.split(' ')[0]
            except:
                date_val = raw_date
            
            link = f"../reports/sim_tests/{file.name}"
            
            report = {
                "id": file.stem.replace("SIM_", "").replace("_REPORT", ""),
                "title": clean_text(raw_title),
                "description": extract_description(content),
                "date": date_val,
                "status": status,
                "link": link,
                "cycles": parse_cycles(cycles_match.group(1)) if cycles_match else 0
            }
            
            reports.append(report)
            print(f"Found: {report['title']} ({report['id']})")
            
    # Sort by Date (descending)
    reports.sort(key=lambda x: x['date'], reverse=True)
    
    return reports

def update_manifest():
    reports = scan_reports()
    
    # Write to JSON
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Manifest updated at {MANIFEST_PATH}")
    print(f"Total reports: {len(reports)}")

if __name__ == "__main__":
    update_manifest()
