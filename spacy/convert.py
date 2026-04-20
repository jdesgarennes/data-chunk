import spacy
from spacy_layout import spaCyLayout
import json
import os

# config
INPUT_DIR = "input"
OUTPUT_FILE = "output/output.jsonl"
CHUNK_SIZE = 150
OVERLAP_SENTENCES = 3

# load model
nlp = spacy.load("en_core_web_sm")
layout = spaCyLayout(nlp)

def process_file(path):
    doc = layout(path)

    chunks = []
    current = []
    current_words = 0

    for span in doc.spans["layout"]:
        if span.label_ == "table":
            continue

        # skip repeating header
        if chunks and "Original Issue Date" in span.text:
            continue

        # force break after header section
        if "Policy and Purpose" in span.text:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_words = 0

        sentences = list(nlp(span.text).sents)

        for sent in sentences:
            text = sent.text.strip()
            if not text:
                continue

            words = text.split()

            if current_words + len(words) > CHUNK_SIZE:
                chunks.append(" ".join(current))
                current = current[-OVERLAP_SENTENCES:]
                current_words = sum(len(s.split()) for s in current)

            current.append(text)
            current_words += len(words)

    if current:
        chunks.append(" ".join(current))

    return chunks

# process folder
with open(OUTPUT_FILE, "w") as out:
    chunk_id = 0

    for file in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, file)

        if not file.lower().endswith((".pdf", ".docx")):
            continue

        print(f"processing: {file}")

        try:
            chunks = process_file(path)

            for chunk in chunks:
                out.write(json.dumps({
                    "id": chunk_id,
                    "text": chunk,
                    "source": file
                }) + "\n")
                chunk_id += 1

        except Exception as e:
            print(f"failed: {file} → {e}")

print("done") 