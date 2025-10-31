# validate_rag.py
import pandas as pd
from backend.rag_pipeline import query_rag, add_document_from_file, is_fitted
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer, util
import numpy as np
import time
import fitz  # PyMuPDF for PDF reading

# ====== Step 1: Prepare RAG Knowledge Base ======
def load_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

if not is_fitted():
    print("🔧 Building knowledge base from Tenancy Agreement...")
    text = load_pdf_text("Track_B_Tenancy_Agreement.pdf")
    add_document_from_file(text, file_type="txt")

# ====== Step 2: Define 20 Evaluation Questions ======
questions = [
    ("What is the monthly rental amount?", "S$7500 per month."),
    ("Who is the landlord of the property?", "Peter Richardson Williams."),
    ("When does the tenancy start?", "22 February 2024."),
    ("How much is the security deposit?", "S$15000, equivalent to two months’ rent."),
    ("What is the address of the rented premises?", "88 Orchard Boulevard #15-03, Singapore 238863."),
    ("What is the tenant responsible for regarding minor repairs?", "Tenant responsible for repairs up to S$200 per item; landlord covers the rest."),
    ("Who pays for aircon servicing?", "Landlord is responsible for servicing and fair wear repairs."),
    ("How long is the defect-free period?", "30 days from the start date."),
    ("What happens if the tenant sublets without permission?", "It constitutes a breach and may lead to termination."),
    ("Who bears the property tax?", "The landlord."),
    ("Under what conditions can the tenant terminate the lease early?", "After 12 months if transferred, deported, or denied residence (diplomatic clause)."),
    ("What happens if rent is unpaid for more than 7 days?", "Landlord can re-enter and terminate the tenancy."),
    ("How is the late payment interest calculated?", "Monthly rent × 10% ÷ 365 × number of late days."),
    ("What are the landlord’s obligations regarding repairs?", "Maintain structure, wiring, pipes; repair within 14 days after notice."),
    ("What are the tenant’s obligations regarding pets?", "Tenant cannot keep pets without landlord’s written consent."),
    ("How is damage due to acts of God treated?", "Not the tenant’s responsibility."),
    ("What should the landlord do before letting out a mortgaged property?", "Obtain written consent from the financial institution."),
    ("How long before expiry should the tenant request renewal?", "At least 2 months before expiry."),
    ("When can the landlord terminate due to en-bloc redevelopment?", "With 3 months’ written notice."),
    ("What are the conditions for rent suspension?", "If the property becomes uninhabitable due to causes beyond both parties’ control.")
]

# ====== Step 3: Scorers ======
rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
model = SentenceTransformer('all-MiniLM-L6-v2')

# ====== Step 4: Evaluation Loop ======
results = []
for q, ref in questions:
    print(f"🔹 Evaluating: {q}")
    start = time.time()
    try:
        pred = query_rag(q)
    except Exception as e:
        pred = f"[Error: {e}]"
    elapsed = time.time() - start

    # Compute ROUGE-L
    r = rouge.score(ref, pred)['rougeL']
    rouge_l = r.fmeasure

    # Compute semantic similarity
    emb_ref = model.encode(ref, convert_to_tensor=True)
    emb_pred = model.encode(pred, convert_to_tensor=True)
    sem_sim = util.cos_sim(emb_ref, emb_pred).item()

    # Compute Exact Match (for factual Qs)
    em = 1.0 if ref.lower().strip() in pred.lower() else 0.0

    # Weighted score
    final_score = 0.4 * rouge_l + 0.3 * em + 0.3 * sem_sim

    results.append({
        "Question": q,
        "Reference": ref,
        "Prediction": pred,
        "ROUGE-L": round(rouge_l, 3),
        "EM": em,
        "SemanticSim": round(sem_sim, 3),
        "Time(s)": round(elapsed, 2),
        "FinalScore": round(final_score, 3)
    })

# ====== Step 5: Save Results ======
df = pd.DataFrame(results)
df.loc["Average"] = df.mean(numeric_only=True)
df.to_excel("rag_validation_report.xlsx", index=False)
print("✅ Validation completed. Results saved to rag_validation_report.xlsx")
