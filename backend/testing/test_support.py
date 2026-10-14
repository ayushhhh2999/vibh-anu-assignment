
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


def response_json(response):
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

    print("All executed Support tests passed!")
    sys.exit(0)


def main():
    print("VIBH-ANU SUPPORT INTEGRATION TESTS\n")

    # Login to every department.
    for role, email in ACCOUNTS.items():
        password = test_password(role)

        response = api(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        tokens[role] = response_json(response).get("access_token")

        check(
            f"{role.title()} login",
            response.status_code == 200 and bool(tokens[role]),
            f"HTTP {response.status_code}",
        )

    if any(not token for token in tokens.values()):
        print("Cannot continue because a login failed.")
        summary()
        return

    # Create a new test lead.
    suffix = uuid.uuid4().hex[:8]

    response = api(
        "POST",
        "/api/leads",
        role="marketing",
        json={
            "name": f"Support Test {suffix}",
            "contact_number": "9876543210",
        },
    )

    lead = response_json(response)
    lead_id = lead.get("id")

    check(
        "Marketing creates test lead",
        response.status_code == 201 and lead_id is not None,
        f"HTTP {response.status_code}",
    )

    if lead_id is None:
        summary()
        return

    # Complete Communication stage.
    response = api(
        "PATCH",
        f"/api/leads/{lead_id}/communication",
        role="communication",
        json={
            "postal_address": "Sector 45, Gurugram, Haryana",
            "meeting_date": "2026-10-20",
            "meeting_time": "15:30:00",
            "remark": "Support integration test",
        },
    )

    check(
        "Communication updates meeting details",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    response = api(
        "POST",
        f"/api/leads/{lead_id}/communication/submit",
        role="communication",
    )

    check(
        "Communication submits to Vigilance",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    # Verify without audio must fail.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    check(
        "Vigilance cannot verify without audio",
        response.status_code == 400,
        f"HTTP {response.status_code}",
    )

    # Create a minimal test audio file.
    # This exercises extension, storage and workflow logic.
    # It is not a genuine playable audio recording.
    fake_audio = b"Support integration test audio placeholder"
    files = {
        "file": (
            "support-test.wav",
            fake_audio,
            "audio/wav",
        )
    }

    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/audio",
        role="vigilance",
        files=files,
    )

    check(
        "Vigilance upload endpoint accepts allowed extension",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    # Verify and transition to Support.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    data = response_json(response)

    check(
        "Vigilance moves lead to Support",
        response.status_code == 200
        and data.get("lead", {}).get("status") == "support",
        f"HTTP {response.status_code}",
    )

    # Support cannot allocate when using other department tokens.
    for role in ("marketing", "communication", "vigilance", "sales"):
        response = api(
            "POST",
            f"/api/leads/{lead_id}/support/allocate",
            role=role,
        )

        check(
            f"{role.title()} cannot allocate lead",
            response.status_code == 403,
            f"HTTP {response.status_code}",
        )

    # Successful allocation as Support.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/support/allocate",
        role="support",
    )

    data = response_json(response)

    check(
        "Support allocates lead to Sales",
        response.status_code == 200
        and data.get("lead", {}).get("status") == "sales",
        f"HTTP {response.status_code}; response={data}",
    )

    # Cannot allocate twice.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/support/allocate",
        role="support",
    )

    check(
        "Duplicate allocation is rejected",
        response.status_code == 409,
        f"HTTP {response.status_code}",
    )

    # Check Sales can see the lead summary.
    response = api("GET", "/api/leads", role="sales")
    leads = response_json(response)

    found = (
        isinstance(leads, list)
        and any(item.get("id") == lead_id for item in leads)
    )

    check(
        "Sales can see allocated lead",
        response.status_code == 200 and found,
        f"HTTP {response.status_code}; visible={found}",
    )

    if found:
        item = next(item for item in leads if item.get("id") == lead_id)

        check(
            "Sales contact details remain hidden before claim",
            item.get("contact_number") is None
            and item.get("postal_address") is None,
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
