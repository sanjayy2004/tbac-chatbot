import os
import json
import pandas as pd
import re
from pathlib import Path

# ── Load role mapping ──────────────────────────────────────────
with open("role_mapping.json", "r") as f:
    ROLE_MAPPING = json.load(f)

DATA_DIR = Path("data/raw")

# ── Text cleaning ──────────────────────────────────────────────
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)
    text = text.strip()
    return text

# ── Chunking ───────────────────────────────────────────────────
def chunk_text(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        chunks.append((chunk_id, chunk))
        chunk_id += 1
        start += chunk_size - overlap
    return chunks

# ── Get roles that can access a document ──────────────────────
def get_roles_for_document(doc_relative_path):
    accessible_roles = []
    for role, config in ROLE_MAPPING["roles"].items():
        for doc in config["documents"]:
            if Path(doc).name == Path(doc_relative_path).name:
                accessible_roles.append(role)
                break
    return list(set(accessible_roles))

# ── Process markdown files ─────────────────────────────────────
def process_markdown(file_path, department):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned)
    results = []
    for chunk_id, chunk in chunks:
        results.append({
            "chunk_id": f"{department}_{file_path.stem}_{chunk_id}",
            "text": chunk,
            "source": str(file_path.name),
            "department": department,
            "file_type": "markdown",
            "accessible_roles": get_roles_for_document(file_path)
        })
    return results

# ── Process CSV files ──────────────────────────────────────────
def process_csv(file_path, department):
    df = pd.read_csv(file_path, encoding="utf-8", encoding_errors="replace")
    results = []
    chunk_id = 0
    for i in range(0, len(df), 20):
        batch = df.iloc[i:i+20]
        text = batch.to_string(index=False)
        cleaned = clean_text(text)
        results.append({
            "chunk_id": f"{department}_{file_path.stem}_{chunk_id}",
            "text": cleaned,
            "source": str(file_path.name),
            "department": department,
            "file_type": "csv",
            "accessible_roles": get_roles_for_document(file_path)
        })
        chunk_id += 1
    return results

# ── Main processor ─────────────────────────────────────────────
def process_all_documents():
    all_chunks = []
    departments = ["Finance", "HR", "marketing", "engineering", "general"]

    for dept in departments:
        dept_path = DATA_DIR / dept
        if not dept_path.exists():
            print(f"⚠️  Folder not found: {dept_path}")
            continue

        for file_path in dept_path.iterdir():
            if file_path.suffix == ".md":
                print(f"✅ Processing: {file_path.name}")
                chunks = process_markdown(file_path, dept.lower())
                all_chunks.extend(chunks)
            elif file_path.suffix == ".csv":
                print(f"✅ Processing: {file_path.name}")
                chunks = process_csv(file_path, dept.lower())
                all_chunks.extend(chunks)
            else:
                print(f"⏭️  Skipping: {file_path.name}")

    # Save chunks to JSON
    output_path = Path("data/processed_chunks.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Done! Total chunks created: {len(all_chunks)}")
    print(f"📁 Saved to: {output_path}")
    return all_chunks

if __name__ == "__main__":
    process_all_documents()