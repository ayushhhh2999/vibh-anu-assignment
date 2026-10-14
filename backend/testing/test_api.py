
"""
Vibh-Anu API Integration Test Suite

Covers:
1. Health endpoint
2. Login for all five departments
3. Invalid-password rejection
4. JWT authentication and /api/auth/me
5. Marketing-only endpoint authorization
6. Authentication requirement for lead listing
7. Marketing lead creation and input validation
8. Department-specific lead visibility
9. Communication-only update permissions
10. Contact number and status protection
11. Empty update rejection
12. Submission blocked when meeting details are missing
13. Successful Communication updates
14. Successful transition to Vigilance
15. Visibility after transition
16. Rejection of edits after transition

Run from the testing directory:
    python test_api.py

The script creates one new test lead and leaves it in the database.
"""

import sys
import time
import uuid

import requests
from test_config import BASE_URL, test_password


TIMEOUT = 10

DEPARTMENTS = {
    "marketing": "marketing@vibhanu.com",
    "communication": "communication@vibhanu.com",
    "vigilance": "vigilance@vibhanu.com",
    "support": "support@vibhanu.com",
    "sales": "sales@vibhanu.com",
}

results = []
tokens = {}


# --------------------------------------------------
# Common testing helpers
# --------------------------------------------------

def check(name, passed, details=""):
    passed = bool(passed)
    results.append((name, passed))

    print(f"[{'PASS' if passed else 'FAIL'}] {name}")

    if details:
        print(f"       {details}")


def api_request(method, path, token=None, **kwargs):
    headers = kwargs.pop("headers", {}).copy()

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return requests.request(
        method,
        f"{BASE_URL}{path}",
        headers=headers,
        timeout=TIMEOUT,
        **kwargs,
    )


def response_json(response):
    try:
        return response.json()
    except ValueError:
        return None


def login(email, password):
    response = api_request(
        "POST",
        "/api/auth/login",
        json={"email": email, "password": password},
    )

    if response.status_code != 200:
        return None

    data = response_json(response) or {}
    return data.get("access_token")


def lead_is_visible(leads, lead_id):
    return any(
        isinstance(lead, dict) and lead.get("id") == lead_id
        for lead in leads
    )


def get_leads(role):
    response = api_request(
        "GET",
        "/api/leads",
        token=tokens[role],
    )

    data = response_json(response)

    if response.status_code != 200 or not isinstance(data, list):
        return response, None

    return response, data


def print_summary():
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed

    print("\n" + "=" * 64)
    print("VIBH-ANU TEST SUMMARY")
    print("=" * 64)
    print(f"Total tests : {len(results)}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {failed}")

    if failed:
        print("\nFailed tests:")
        for name, success in results:
            if not success:
                print(f"  - {name}")

        print("\nFix the failed tests before proceeding.")
        sys.exit(1)

    print("\nAll tests passed!")
    sys.exit(0)


# --------------------------------------------------
# Main test suite
# --------------------------------------------------

def main():
    print("=" * 64)
    print("VIBH-ANU API INTEGRATION TESTS")
    print("=" * 64)
    print(f"API URL: {BASE_URL}\n")

    # 1. Health check
    try:
        response = api_request("GET", "/health")
        data = response_json(response) or {}

        check(
            "Health endpoint",
            response.status_code == 200
            and data.get("status") == "healthy",
            f"HTTP {response.status_code}; response={data}",
        )
    except requests.RequestException as exc:
        check("Health endpoint", False, str(exc))
        print("\nStart the server: uvicorn app.main:app --reload")
        print_summary()
        return

    # 2. Load local test credentials, with a prompt only for standalone use.
    passwords = {role: test_password(role) for role in DEPARTMENTS}

    # 3. Login for every department
    for role, email in DEPARTMENTS.items():
        try:
            tokens[role] = login(email, passwords[role])

            check(
                f"{role.title()} login",
                tokens[role] is not None,
                "Access token received"
                if tokens[role]
                else "Login failed",
            )
        except requests.RequestException as exc:
            tokens[role] = None
            check(f"{role.title()} login", False, str(exc))

    # Invalid password
    try:
        response = api_request(
            "POST",
            "/api/auth/login",
            json={
                "email": DEPARTMENTS["marketing"],
                "password": "wrong-password-for-testing",
            },
        )

        check(
            "Invalid password returns 401",
            response.status_code == 401,
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Invalid password returns 401", False, str(exc))

    # Stop dependent tests if login did not work.
    if any(tokens.get(role) is None for role in DEPARTMENTS):
        print("\nCannot run authenticated tests because a login failed.")
        print_summary()
        return

    # 4. /api/auth/me and token identity
    for role, email in DEPARTMENTS.items():
        try:
            response = api_request(
                "GET",
                "/api/auth/me",
                token=tokens[role],
            )
            data = response_json(response) or {}

            check(
                f"{role.title()} identity endpoint",
                response.status_code == 200
                and data.get("email") == email
                and data.get("role") == role,
                f"HTTP {response.status_code}; role={data.get('role')}",
            )
        except requests.RequestException as exc:
            check(f"{role.title()} identity endpoint", False, str(exc))

    # 5. Marketing-only endpoint
    for role in DEPARTMENTS:
        try:
            response = api_request(
                "GET",
                "/api/marketing/check",
                token=tokens[role],
            )

            expected = 200 if role == "marketing" else 403

            check(
                f"Marketing check permission: {role}",
                response.status_code == expected,
                f"Expected {expected}; received {response.status_code}",
            )
        except requests.RequestException as exc:
            check(f"Marketing check permission: {role}", False, str(exc))

    # 6. Unauthenticated lead list
    try:
        response = api_request("GET", "/api/leads")

        check(
            "Lead list requires authentication",
            response.status_code in (401, 403),
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Lead list requires authentication", False, str(exc))

    # 7. Create a fresh lead
    suffix = uuid.uuid4().hex[:8]
    test_name = f"API Test {suffix}"
    test_contact = f"9{int(time.time() * 1000) % 1_000_000_000:09d}"
    lead_id = None

    try:
        response = api_request(
            "POST",
            "/api/leads",
            token=tokens["marketing"],
            json={
                "name": test_name,
                "contact_number": test_contact,
            },
        )

        data = response_json(response) or {}
        lead_id = data.get("id")

        check(
            "Marketing creates lead",
            response.status_code == 201 and lead_id is not None,
            f"HTTP {response.status_code}; response={data}",
        )

        if lead_id is not None:
            check(
                "Lead begins in Communication",
                data.get("status") == "communication",
                f"Status={data.get('status')}",
            )

            check(
                "Contact number stored correctly",
                data.get("contact_number") == test_contact,
            )
    except requests.RequestException as exc:
        check("Marketing creates lead", False, str(exc))

    # 8. Other roles cannot create leads
    for role in ("communication", "vigilance", "support", "sales"):
        try:
            response = api_request(
                "POST",
                "/api/leads",
                token=tokens[role],
                json={
                    "name": f"Forbidden {suffix}",
                    "contact_number": test_contact,
                },
            )

            check(
                f"{role.title()} cannot create leads",
                response.status_code == 403,
                f"HTTP {response.status_code}",
            )
        except requests.RequestException as exc:
            check(f"{role.title()} cannot create leads", False, str(exc))

    # 9. Invalid lead creation data
    try:
        response = api_request(
            "POST",
            "/api/leads",
            token=tokens["marketing"],
            json={"name": "A", "contact_number": "123"},
        )

        check(
            "Invalid lead creation data returns 422",
            response.status_code == 422,
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Invalid lead creation data returns 422", False, str(exc))

    if lead_id is None:
        print("\nA test lead could not be created; skipping dependent tests.")
        print_summary()
        return

    # 10. Initial department visibility
    initial_visibility = {
        "marketing": True,
        "communication": True,
        "vigilance": False,
        "support": False,
        "sales": False,
    }

    for role, expected_visible in initial_visibility.items():
        try:
            response, leads = get_leads(role)
            visible = (
                lead_is_visible(leads, lead_id)
                if leads is not None
                else False
            )

            check(
                f"Initial visibility: {role.title()}",
                leads is not None and visible == expected_visible,
                f"Expected visible={expected_visible}; "
                f"actual={visible}; HTTP {response.status_code}",
            )
        except requests.RequestException as exc:
            check(f"Initial visibility: {role.title()}", False, str(exc))

    # 11. Communication-only update permissions
    valid_update = {"remark": "Integration test update"}

    for role in ("marketing", "vigilance", "support", "sales"):
        try:
            response = api_request(
                "PATCH",
                f"/api/leads/{lead_id}/communication",
                token=tokens[role],
                json=valid_update,
            )

            check(
                f"{role.title()} cannot edit Communication fields",
                response.status_code == 403,
                f"HTTP {response.status_code}",
            )
        except requests.RequestException as exc:
            check(
                f"{role.title()} cannot edit Communication fields",
                False,
                str(exc),
            )

    # 12. Contact number cannot be changed
    try:
        response = api_request(
            "PATCH",
            f"/api/leads/{lead_id}/communication",
            token=tokens["communication"],
            json={"contact_number": "1111111111"},
        )

        check(
            "Communication cannot change contact number",
            response.status_code == 422,
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Contact number protection", False, str(exc))

    # 13. Status cannot be manipulated
    try:
        response = api_request(
            "PATCH",
            f"/api/leads/{lead_id}/communication",
            token=tokens["communication"],
            json={"status": "sales"},
        )

        check(
            "Communication cannot set workflow status",
            response.status_code == 422,
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Workflow status protection", False, str(exc))

    # 14. Empty update should be rejected
    try:
        response = api_request(
            "PATCH",
            f"/api/leads/{lead_id}/communication",
            token=tokens["communication"],
            json={},
        )

        check(
            "Empty Communication update is rejected",
            response.status_code == 422,
            f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Empty Communication update is rejected", False, str(exc))

    # 15. Submission without required fields
    try:
        response = api_request(
            "POST",
            f"/api/leads/{lead_id}/communication/submit",
            token=tokens["communication"],
        )

        data = response_json(response) or {}
        detail = data.get("detail", {})
        missing = detail.get("missing_fields", [])

        check(
            "Submission without meeting details is rejected",
            response.status_code == 400
            and all(
                field in missing
                for field in (
                    "postal_address",
                    "meeting_date",
                    "meeting_time",
                )
            ),
            f"HTTP {response.status_code}; missing={missing}",
        )
    except requests.RequestException as exc:
        check("Missing details block submission", False, str(exc))

    # 16. Communication updates permitted fields
    update_payload = {
        "name": f"Updated {suffix}",
        "postal_address": "Sector 45, Gurugram, Haryana",
        "meeting_date": "2026-10-20",
        "meeting_time": "15:30:00",
        "remark": "Integration test: afternoon meeting",
    }

    try:
        response = api_request(
            "PATCH",
            f"/api/leads/{lead_id}/communication",
            token=tokens["communication"],
            json=update_payload,
        )

        data = response_json(response) or {}

        check(
            "Communication can update permitted fields",
            response.status_code == 200
            and data.get("name") == update_payload["name"]
            and data.get("postal_address")
            == update_payload["postal_address"]
            and data.get("meeting_date") == "2026-10-20"
            and str(data.get("meeting_time", "")).startswith("15:30")
            and data.get("remark") == update_payload["remark"],
            f"HTTP {response.status_code}; response={data}",
        )

        check(
            "Contact number remains unchanged after update",
            data.get("contact_number") == test_contact,
            f"Contact={data.get('contact_number')}",
        )

        check(
            "Update does not change workflow stage",
            data.get("status") == "communication",
            f"Status={data.get('status')}",
        )
    except requests.RequestException as exc:
        check("Communication updates permitted fields", False, str(exc))

    # 17. Submit completed lead to Vigilance
    try:
        response = api_request(
            "POST",
            f"/api/leads/{lead_id}/communication/submit",
            token=tokens["communication"],
        )

        data = response_json(response) or {}
        lead_data = data.get("lead", {})

        check(
            "Communication submits lead to Vigilance",
            response.status_code == 200
            and lead_data.get("status") == "vigilance",
            f"HTTP {response.status_code}; response={data}",
        )
    except requests.RequestException as exc:
        check("Submit lead to Vigilance", False, str(exc))

    # 18. Visibility after transition
    post_transition_visibility = {
        "marketing": True,
        "communication": False,
        "vigilance": True,
        "support": False,
        "sales": False,
    }

    for role, expected_visible in post_transition_visibility.items():
        try:
            response, leads = get_leads(role)
            visible = (
                lead_is_visible(leads, lead_id)
                if leads is not None
                else False
            )

            check(
                f"Post-transition visibility: {role.title()}",
                leads is not None and visible == expected_visible,
                f"Expected visible={expected_visible}; "
                f"actual={visible}; HTTP {response.status_code}",
            )
        except requests.RequestException as exc:
            check(
                f"Post-transition visibility: {role.title()}",
                False,
                str(exc),
            )

    # 19. Communication cannot edit a lead after transition
    try:
        response = api_request(
            "PATCH",
            f"/api/leads/{lead_id}/communication",
            token=tokens["communication"],
            json={"remark": "This should not be accepted"},
        )

        check(
            "Communication cannot edit after submission",
            response.status_code == 409,
            f"Expected 409; received {response.status_code}",
        )
    except requests.RequestException as exc:
        check("No editing after submission", False, str(exc))

    # 20. Duplicate submission must fail
    try:
        response = api_request(
            "POST",
            f"/api/leads/{lead_id}/communication/submit",
            token=tokens["communication"],
        )

        check(
            "Duplicate submission is rejected",
            response.status_code == 409,
            f"Expected 409; received {response.status_code}",
        )
    except requests.RequestException as exc:
        check("Duplicate submission is rejected", False, str(exc))

    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTests interrupted.")
        sys.exit(130)
