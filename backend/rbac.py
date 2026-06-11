import json
from pathlib import Path

# ── Load role mapping ──────────────────────────────────────────
with open("role_mapping.json", "r") as f:
    ROLE_MAPPING = json.load(f)

# ── Role hierarchy (higher number = more access) ───────────────
ROLE_HIERARCHY = {
    "employee": 1,
    "hr": 2,
    "marketing": 2,
    "finance": 2,
    "engineering": 2,
    "c_level": 3
}

# ── Sample users database (will move to SQLite in Module 5) ───
USERS_DB = {
    "alice": {"password": "finance123", "role": "finance", "name": "Alice Finance"},
    "bob": {"password": "hr123", "role": "hr", "name": "Bob HR"},
    "carol": {"password": "mkt123", "role": "marketing", "name": "Carol Marketing"},
    "dave": {"password": "eng123", "role": "engineering", "name": "Dave Engineering"},
    "eve": {"password": "emp123", "role": "employee", "name": "Eve Employee"},
    "frank": {"password": "ceo123", "role": "c_level", "name": "Frank CEO"},
}

# ── Get accessible departments for a role ─────────────────────
def get_accessible_departments(role):
    if role not in ROLE_MAPPING["roles"]:
        return []
    return ROLE_MAPPING["roles"][role]["accessible_departments"]

# ── Get accessible documents for a role ───────────────────────
def get_accessible_documents(role):
    if role not in ROLE_MAPPING["roles"]:
        return []
    return ROLE_MAPPING["roles"][role]["documents"]

# ── Check if role can access a department ─────────────────────
def can_access_department(role, department):
    accessible = get_accessible_departments(role)
    return department.lower() in [d.lower() for d in accessible]

# ── Check if role can access a document ───────────────────────
def can_access_document(role, document_name):
    accessible_docs = get_accessible_documents(role)
    for doc in accessible_docs:
        if Path(doc).name.lower() == document_name.lower():
            return True
    return False

# ── Validate user login ────────────────────────────────────────
def validate_user(username, password):
    user = USERS_DB.get(username.lower())
    if user and user["password"] == password:
        return {
            "username": username.lower(),
            "role": user["role"],
            "name": user["name"]
        }
    return None

# ── Filter search results by role ─────────────────────────────
def filter_results_by_role(results, role):
    filtered = []
    for result in results:
        dept = result.get("department", "")
        source = result.get("source", "")
        if can_access_department(role, dept) or can_access_document(role, source):
            filtered.append(result)
    return filtered

# ── Query preprocessing ────────────────────────────────────────
def preprocess_query(query):
    query = query.strip()
    query = " ".join(query.split())
    if not query.endswith("?") and query.lower().startswith(("what", "who", "when", "where", "how", "why")):
        query = query + "?"
    return query

# ── Get role display info ──────────────────────────────────────
def get_role_info(role):
    info = {
        "finance": {
            "display": "Finance",
            "color": "#2ecc71",
            "description": "Access to financial reports and general documents"
        },
        "hr": {
            "display": "Human Resources",
            "color": "#3498db",
            "description": "Access to HR data and general documents"
        },
        "marketing": {
            "display": "Marketing",
            "color": "#e74c3c",
            "description": "Access to marketing reports and general documents"
        },
        "engineering": {
            "display": "Engineering",
            "color": "#9b59b6",
            "description": "Access to technical docs and general documents"
        },
        "employee": {
            "display": "Employee",
            "color": "#f39c12",
            "description": "Access to general company handbook only"
        },
        "c_level": {
            "display": "C-Level Executive",
            "color": "#1abc9c",
            "description": "Full access to all company documents"
        }
    }
    return info.get(role, {"display": role, "color": "#95a5a6", "description": ""})

# ── Test RBAC ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔐 Testing RBAC System\n")

    # Test login
    print("── Login Tests ──")
    user = validate_user("alice", "finance123")
    print(f"✅ Alice login: {user}")

    wrong = validate_user("alice", "wrongpass")
    print(f"❌ Wrong password: {wrong}")

    # Test access control
    print("\n── Access Control Tests ──")
    tests = [
        ("finance", "finance", True),
        ("finance", "hr", False),
        ("c_level", "hr", True),
        ("c_level", "finance", True),
        ("employee", "marketing", False),
        ("employee", "general", True),
    ]

    for role, dept, expected in tests:
        result = can_access_department(role, dept)
        status = "✅" if result == expected else "❌"
        print(f"{status} Role '{role}' accessing '{dept}': {result} (expected {expected})")

    # Test query preprocessing
    print("\n── Query Preprocessing ──")
    queries = ["  what is the revenue  ", "tell me about employees", "what are the expenses"]
    for q in queries:
        print(f"  '{q}' → '{preprocess_query(q)}'")