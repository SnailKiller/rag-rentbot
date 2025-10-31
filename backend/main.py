# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"   # 避免 Metal 报错
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

from document_parser import parse_file
from rag_pipeline import add_document_to_store, answer_question, retrieve_relevant
import uuid
from typing import List

app = FastAPI()
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), doc_id: str = Form(None)):
    content = await file.read()
    text = parse_file(file.filename, content)
    if not text.strip():
        return JSONResponse({"status": "error", "message": "No text extracted from file."}, status_code=400)
    if doc_id is None:
        doc_id = str(uuid.uuid4())
    # save raw file
    path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    with open(path, "wb") as f:
        f.write(content)
    chunk_count = add_document_to_store(doc_id, text)
    return {"status": "ok", "doc_id": doc_id, "chunks": chunk_count}

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    result = answer_question(question)
    return result

@app.get("/list_docs")
async def list_docs():
    # naive: read metadata from vectorstore
    from rag_pipeline import vs
    docs = {}
    for m in vs.metadata:
        docs.setdefault(m["doc_id"], 0)
        docs[m["doc_id"]] += 1
    return {"docs": docs}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
