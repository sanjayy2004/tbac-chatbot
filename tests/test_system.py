import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests

BASE_URL = "http://127.0.0.1:8080"

# ── Colors for output ──────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def passed(msg): print(f"{GREEN}✅ PASS:{RESET} {msg}")
def failed(msg): print(f"{RED}❌ FAIL:{RESET} {msg}")
def info(msg):   print(f"{YELLOW}ℹ️  INFO:{RESET} {msg}")

results = {"passed": 0, "failed": 0}

def check(condition, msg):
    if condition:
        passed(msg)
        results["passed"] += 1
    else:
        failed(msg)
        results["failed"] += 1

# ── Test 1: Health check ───────────────────────────────────────
def test_health():
    print("\n── Test 1: Health Check ──")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        check(r.status_code == 200, "API is running")
        check(r.json()["status"] == "healthy", "Health status is healthy")
    except:
        failed("API is not running!")

# ── Test 2: Login tests ────────────────────────────────────────
def test_login():
    print("\n── Test 2: Login Tests ──")
    
    # Valid login
    r = requests.post(f"{BASE_URL}/login",
        data={"username": "alice", "password": "finance123"})
    check(r.status_code == 200, "Valid login returns 200")
    check("access_token" in r.json(), "Login returns access token")
    check(r.json()["role"] == "finance", "Alice has finance role")

    # Invalid login
    r = requests.post(f"{BASE_URL}/login",
        data={"username": "alice", "password": "wrongpass"})
    check(r.status_code == 401, "Invalid password returns 401")

    # Invalid user
    r = requests.post(f"{BASE_URL}/login",
        data={"username": "nobody", "password": "pass"})
    check(r.status_code == 401, "Invalid user returns 401")

# ── Test 3: RBAC access control ───────────────────────────────
def test_rbac():
    print("\n── Test 3: RBAC Access Control ──")

    test_users = [
        ("alice", "finance123", "finance"),
        ("bob", "hr123", "hr"),
        ("carol", "mkt123", "marketing"),
        ("dave", "eng123", "engineering"),
        ("eve", "emp123", "employee"),
        ("frank", "ceo123", "c_level"),
    ]

    for username, password, expected_role in test_users:
        r = requests.post(f"{BASE_URL}/login",
            data={"username": username, "password": password})
        check(r.status_code == 200 and r.json()["role"] == expected_role,
              f"{username} has correct role: {expected_role}")

# ── Test 4: Chat endpoint ──────────────────────────────────────
def test_chat():
    print("\n── Test 4: Chat & RAG Tests ──")

    # Get token for alice (finance)
    r = requests.post(f"{BASE_URL}/login",
        data={"username": "alice", "password": "finance123"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test chat response
    r = requests.post(f"{BASE_URL}/chat",
        headers=headers,
        json={"query": "What is the total revenue?"},
        timeout=60)
    check(r.status_code == 200, "Chat endpoint returns 200")
    data = r.json()
    check("answer" in data, "Response has answer field")
    check("sources" in data, "Response has sources field")
    check(len(data["answer"]) > 10, "Answer is not empty")
    check(data["role"] == "finance", "Response shows correct role")

    # Test unauthorized access (no token)
    r = requests.post(f"{BASE_URL}/chat",
        json={"query": "What is the revenue?"})
    check(r.status_code == 401, "Unauthenticated request returns 401")

# ── Test 5: Role isolation ─────────────────────────────────────
def test_role_isolation():
    print("\n── Test 5: Role Isolation Tests ──")

    from backend.rbac import can_access_department

    # Finance cannot access HR
    check(not can_access_department("finance", "hr"),
          "Finance blocked from HR documents")

    # HR cannot access Finance
    check(not can_access_department("hr", "finance"),
          "HR blocked from Finance documents")

    # Employee cannot access Marketing
    check(not can_access_department("employee", "marketing"),
          "Employee blocked from Marketing documents")

    # C-Level can access everything
    for dept in ["finance", "hr", "marketing", "engineering", "general"]:
        check(can_access_department("c_level", dept),
              f"C-Level can access {dept}")

# ── Test 6: Vector search ──────────────────────────────────────
def test_vector_search():
    print("\n── Test 6: Vector Search Tests ──")

    from backend.vector_store import search

    results = search("total revenue", "finance", top_k=3)
    check(len(results) > 0, "Finance search returns results")
    check(all(r["department"] in ["finance", "general"] for r in results),
          "Finance search only returns finance/general docs")

    results = search("employee handbook", "employee", top_k=3)
    check(len(results) > 0, "Employee search returns results")
    check(all(r["department"] == "general" for r in results),
          "Employee search only returns general docs")

# ── Run all tests ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 RBAC CHATBOT — INTEGRATION TEST SUITE")
    print("=" * 50)

    test_health()
    test_login()
    test_rbac()
    test_chat()
    test_role_isolation()
    test_vector_search()

    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {GREEN}{results['passed']} passed{RESET} | {RED}{results['failed']} failed{RESET}")
    print("=" * 50)

    if results["failed"] == 0:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! System is ready for deployment!{RESET}")
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed. Check above for details.{RESET}")