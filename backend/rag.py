import os
import requests
import json
from dotenv import load_dotenv
from backend.vector_store import search
from backend.rbac import preprocess_query, filter_results_by_role

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")

# ── LLM Configuration ──────────────────────────────────────────
# ── LLM Configuration ──────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Build prompt ───────────────────────────────────────────────
def build_prompt(query, context, role):
    role_display = role.replace("_", " ").title()
    prompt = f"""<s>[INST] You are a helpful company internal assistant. 
You answer questions based ONLY on the provided company documents.
The user has the role: {role_display}
They only have access to documents relevant to their department.
If the answer is not in the context, say "I don't have enough information in your accessible documents to answer this."
Always be professional and concise.

Context from company documents:
{context}

Question: {query} [/INST]"""
    return prompt

# ── Call HuggingFace LLM ───────────────────────────────────────
# ── Call Groq LLM ──────────────────────────────────────────────
def call_llm(prompt):
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512
        )
        return completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"LLM Exception: {e}")
        return None
# ── Calculate confidence score ─────────────────────────────────
def calculate_confidence(results):
    if not results:
        return 0.0
    avg_distance = sum(r["distance"] for r in results) / len(results)
    confidence = max(0.0, min(1.0, 1.0 - avg_distance))
    return round(confidence, 2)

# ── Main RAG pipeline ──────────────────────────────────────────
def rag_pipeline(query, user_role):
    # Step 1: Preprocess query
    clean_query = preprocess_query(query)
    print(f"🔍 Query: {clean_query} | Role: {user_role}")

    # Step 2: Retrieve relevant chunks
    results = search(clean_query, user_role, top_k=4)

    # Step 3: Filter by role
    filtered = filter_results_by_role(results, user_role)
    print(f"📄 Retrieved {len(filtered)} relevant chunks")

    if not filtered:
        return {
            "answer": "I couldn't find any relevant information in the documents you have access to. Please check with your administrator if you need access to additional resources.",
            "sources": [],
            "confidence": 0.0,
            "query": clean_query
        }

    # Step 4: Build context
    context_parts = []
    for r in filtered:
        context_parts.append(f"Document: {r['source']}\n{r['text']}")
    context = "\n\n---\n\n".join(context_parts)

    # Step 5: Build prompt
    prompt = build_prompt(clean_query, context, user_role)

    # Step 6: Call LLM
    print("🤖 Calling LLM...")
    llm_response = call_llm(prompt)

    # Step 7: Handle response
    if llm_response == "MODEL_LOADING":
        answer = "The AI model is loading, please try again in 20 seconds."
    elif llm_response == "TIMEOUT":
        answer = "The request timed out. Using document excerpt instead:\n\n" + filtered[0]["text"][:600]
    elif llm_response is None:
        answer = "Based on your accessible documents:\n\n" + filtered[0]["text"][:600]
    else:
        answer = llm_response

    # Step 8: Build sources with attribution
    sources = []
    seen = set()
    for r in filtered:
        if r["source"] not in seen:
            sources.append({
                "source": r["source"],
                "department": r["department"],
                "preview": r["text"][:150] + "..."
            })
            seen.add(r["source"])

    confidence = calculate_confidence(filtered)
    print(f"✅ Response generated | Confidence: {confidence}")

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "query": clean_query
    }

# ── Test RAG pipeline ──────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 Testing RAG Pipeline\n")

    test_cases = [
        ("What is the total revenue?", "finance"),
        ("What are the employee leave policies?", "employee"),
        ("What were the marketing results in Q1?", "marketing"),
    ]

    for query, role in test_cases:
        print(f"\n{'='*50}")
        result = rag_pipeline(query, role)
        print(f"Answer: {result['answer'][:300]}")
        print(f"Sources: {[s['source'] for s in result['sources']]}")
        print(f"Confidence: {result['confidence']}")