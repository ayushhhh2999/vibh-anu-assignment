
import sys
from pathlib import Path

import requests
from test_config import BASE_URL, audio_fixture_path, test_password

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
    headers = kwargs.pop("headers", {})
    if role:
        headers["Authorization"] = f"Bearer {tokens[role]}"

    return requests.request(
        method,
        BASE_URL + path,
        headers=headers,
        timeout=TIMEOUT,
        **kwargs,
    )


def json_data(response):
    try:
        return response.json()
    except ValueError:
        return {}


def main():
    print("VIBH-ANU VIGILANCE TESTS\n")

    # Login to all departments.
    for role, email in ACCOUNTS.items():
        password = test_password(role)

        response = api(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        tokens[role] = json_data(response).get("access_token")

        check(
            f"{role.title()} login",
            response.status_code == 200 and tokens[role] is not None,
            f"HTTP {response.status_code}",
        )

    if any(not token for token in tokens.values()):
        print("Cannot continue: a department login failed.")
        summary()
        return

    # Ask for an actual audio file on the computer.
    audio_path = audio_fixture_path()

    if not audio_path.is_file():
        print("Audio file not found. No workflow tests were run.")
        summary()
        return

    if audio_path.suffix.lower() not in {
        ".mp3", ".wav", ".m4a", ".ogg", ".webm"
    }:
        print("Choose a file with a supported audio extension.")
        summary()
        return

    # Create a fresh lead as Marketing.
    response = api(
        "POST",
        "/api/leads",
        role="marketing",
        json={
            "name": "Vigilance Integration Test",
            "contact_number": "9876543210",
        },
    )

    lead = json_data(response)
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
            "remark": "Vigilance integration test",
        },
    )

    check(
        "Communication completes meeting details",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    response = api(
        "POST",
        f"/api/leads/{lead_id}/communication/submit",
        role="communication",
    )

    data = json_data(response)
    check(
        "Communication submits lead to Vigilance",
        response.status_code == 200
        and data.get("lead", {}).get("status") == "vigilance",
        f"HTTP {response.status_code}",
    )

    # Verification must fail before an audio upload.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    check(
        "Verification blocked without audio",
        response.status_code == 400,
        f"HTTP {response.status_code}",
    )

    # Other departments cannot upload audio.
    for role in ("marketing", "communication", "support", "sales"):
        with audio_path.open("rb") as audio:
            response = api(
                "POST",
                f"/api/leads/{lead_id}/vigilance/audio",
                role=role,
                files={
                    "file": (
                        audio_path.name,
                        audio,
                        "application/octet-stream",
                    )
                },
            )

        check(
            f"{role.title()} cannot upload Vigilance audio",
            response.status_code == 403,
            f"HTTP {response.status_code}",
        )

    # Invalid file extension must be rejected.
    with audio_path.open("rb") as audio:
        response = api(
            "POST",
            f"/api/leads/{lead_id}/vigilance/audio",
            role="vigilance",
            files={
                "file": ("test.txt", audio, "text/plain")
            },
        )

    check(
        "Unsupported audio extension rejected",
        response.status_code == 400,
        f"HTTP {response.status_code}",
    )

    # Vigilance uploads the real recording.
    with audio_path.open("rb") as audio:
        response = api(
            "POST",
            f"/api/leads/{lead_id}/vigilance/audio",
            role="vigilance",
            files={
                "file": (
                    audio_path.name,
                    audio,
                    "application/octet-stream",
                )
            },
        )

    data = json_data(response)

    check(
        "Vigilance audio upload succeeds",
        response.status_code == 200
        and data.get("audio_available") is True,
        f"HTTP {response.status_code}; response={data}",
    )

    # Now verification should succeed.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    data = json_data(response)

    check(
        "Vigilance verifies lead",
        response.status_code == 200
        and data.get("lead", {}).get("status") == "support",
        f"HTTP {response.status_code}; response={data}",
    )

    # Check final visibility.
    expected = {
        "marketing": True,
        "communication": False,
        "vigilance": False,
        "support": True,
        "sales": False,
    }

    for role, should_see in expected.items():
        response = api("GET", "/api/leads", role=role)
        leads = json_data(response)

        visible = (
            isinstance(leads, list)
            and any(item.get("id") == lead_id for item in leads)
        )

        check(
            f"Final visibility: {role.title()}",
            response.status_code == 200 and visible == should_see,
            f"Expected visible={should_see}; actual={visible}",
        )

    # Re-verification should fail after the transition.
    response = api(
        "POST",
        f"/api/leads/{lead_id}/vigilance/verify",
        role="vigilance",
    )

    check(
        "Cannot verify the same lead twice",
        response.status_code == 409,
        f"HTTP {response.status_code}",
    )

    summary()


def summary():
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    print("\n" + "=" * 50)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed:
        print("\nFailed tests:")
        for name, result in results:
            if not result:
                print(f"- {name}")
        sys.exit(1)

    print("All executed tests passed!")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"\nAPI request failed: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTesting interrupted.")
        sys.exit(130)
