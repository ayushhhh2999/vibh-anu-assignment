
import sys
import uuid

import requests
from test_config import BASE_URL, test_password

TIMEOUT = 20

ACCOUNTS = {
    "marketing": "marketing@vibhanu.com",
    "communication": "communication@vibhanu.com",
    "vigilance": "vigilance@vibhanu.com",
    "support": "support@vibhanu.com",
    "sales": "sales@vibhanu.com",
}

results = []
tokens = {}


def check(name, passed, details=""):
    passed = bool(passed)
    results.append((name, passed))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    if details:
        print(f"       {details}")


def api(method, path, role=None, **kwargs):
    headers = kwargs.pop("headers", {}).copy()

    if role:
        headers["Authorization"] = f"Bearer {tokens[role]}"

    return requests.request(
        method,
        BASE_URL + path,
        headers=headers,
        timeout=TIMEOUT,
        **kwargs,
    )


def data(response):
    try:
        return response.json()
    except ValueError:
        return {}


def summary():
    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed

    print("\n" + "=" * 55)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed:
        print("\nFailed tests:")
        for name, ok in results:
            if not ok:
                print(f"- {name}")
        sys.exit(1)

    print("All executed Sales tests passed!")
    sys.exit(0)


def main():
    print("VIBH-ANU SALES INTEGRATION TESTS\n")

    # Authenticate every department.
    for role, email in ACCOUNTS.items():
        password = test_password(role)

        response = api(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        tokens[role] = data(response).get("access_token")

        check(
            f"{role.title()} login",
            response.status_code == 200 and bool(tokens[role]),
            f"HTTP {response.status_code}",
        )

    if any(not token for token in tokens.values()):
        print("Login failed. Workflow tests cannot continue.")
        summary()
        return

    # Create a fresh test lead.
    suffix = uuid.uuid4().hex[:8]
    contact = "9876543210"

    response = api(
        "POST",
        "/api/leads",
        role="marketing",
        json={
            "name": f"Sales Test {suffix}",
            "contact_number": contact,
        },
    )

    lead_id = data(response).get("id")

    check(
        "Create test lead",
        response.status_code == 201 and lead_id is not None,
        f"HTTP {response.status_code}",
    )

    if lead_id is None:
        summary()
        return

    # Communication stage.
    response = api(
        "PATCH",
        f"/api/leads/{lead_id}/communication",
        role="communication",
        json={
            "postal_address": "Sector 45, Gurugram, Haryana",
            "meeting_date": "2026-10-20",
            "meeting_time": "15:30:00",
            "remark": "Sales integration test",
        },
    )

    check("Complete Communication details", response.status_code == 200)

    response = api(
        "POST",
        f"/api/leads/{lead_id}/communication/submit",
        role="communication",
    )

    check("Submit to Vigilance", response.status_code == 200)

    # Vigilance stage. This placeholder tests backend workflow,
    # not actual audio decoding or playback.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/audio",
        role="vigilance",
        files={
            "file": (
                "sales-test.wav",
                b"test audio placeholder",
                "application/octet-stream",
            )
        },
    )

    check(
        "Upload required audio",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    check(
        "Vigilance submits to Support",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    # Support stage.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/support/allocate",
        role="support",
    )

    check(
        "Support allocates to Sales",
        response.status_code == 200
        and data(response).get("lead", {}).get("status") == "sales",
        f"HTTP {response.status_code}",
    )

    # Sales sees the lead, but sensitive fields are hidden.
    response = api("GET", "/api/leads", role="sales")
    leads = data(response)

    lead_summary = (
        next(
            (item for item in leads if item.get("id") == lead_id),
            None,
        )
        if isinstance(leads, list)
        else None
    )

    check(
        "Sales sees allocated lead",
        response.status_code == 200 and lead_summary is not None,
    )

    if lead_summary:
        check(
            "Sensitive details hidden before claim",
            lead_summary.get("contact_number") is None
            and lead_summary.get("postal_address") is None,
        )

    # A non-Sales role cannot stream audio.
    response = api(
        "GET",
        f"/api/leads/{lead_id}/sales/audio",
        role="support",
    )

    check(
        "Support cannot access Sales audio endpoint",
        response.status_code == 403,
        f"HTTP {response.status_code}",
    )

    # Sales can retrieve the audio.
    response = api(
        "GET",
        f"/api/leads/{lead_id}/sales/audio",
        role="sales",
    )

    check(
        "Sales can stream allocated audio",
        response.status_code == 200 and len(response.content) > 0,
        f"HTTP {response.status_code}",
    )

    # Claiming before playback acknowledgement must fail.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/claim",
        role="sales",
    )

    check(
        "Claim blocked before playback acknowledgement",
        response.status_code == 403,
        f"HTTP {response.status_code}",
    )

    # Record playback completion acknowledgement.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/playback-complete",
        role="sales",
    )

    check(
        "Playback acknowledgement recorded",
        response.status_code == 200
        and data(response).get("completed") is True,
        f"HTTP {response.status_code}",
    )

    # Claim after acknowledgement.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/claim",
        role="sales",
    )

    claim_data = data(response)
    claimed_lead = claim_data.get("lead", {})

    check(
        "Sales claims lead",
        response.status_code == 200
        and claimed_lead.get("status") == "claimed",
        f"HTTP {response.status_code}",
    )

    check(
        "Full details visible after claim",
        response.status_code == 200
        and claimed_lead.get("contact_number") == contact
        and claimed_lead.get("postal_address")
        == "Sector 45, Gurugram, Haryana",
    )

    # A duplicate claim must fail.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/claim",
        role="sales",
    )

    check(
        "Duplicate claim rejected",
        response.status_code == 409,
        f"HTTP {response.status_code}",
    )

    # Another department cannot acknowledge playback.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/playback-complete",
        role="support",
    )

    check(
        "Non-Sales playback acknowledgement rejected",
        response.status_code == 403,
        f"HTTP {response.status_code}",
    )

    
    # A claimed lead must not be available for another claim.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/sales/claim",
        role="sales",
    )

    check(
        "Claimed lead cannot be claimed again",
        response.status_code == 409,
        f"HTTP {response.status_code}",
    )

    summary()


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"\nAPI request failed: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTesting interrupted.")
        sys.exit(130)

