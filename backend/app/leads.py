
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from pathlib import Path
import os
from uuid import uuid4
from sqlalchemy import select, update
from fastapi import File, UploadFile
from datetime import datetime
from app.db import get_db
from app.models import Lead, User
from app.auth import get_current_user
from app.permissions import require_roles
from app.lead_schemas import LeadCreate, LeadListResponse
from app.communication_schemas import CommunicationUpdate

from fastapi.responses import FileResponse
from sqlalchemy import select

from app.models import AudioPlayback




router = APIRouter(
    prefix="/api/leads",
    tags=["Leads"],
)
 

def format_lead(lead: Lead, current_user: User) -> dict:
    """Return only the fields this user is allowed to see."""

    # Sales can see a summary before claiming a lead.
    if current_user.role == "sales" and lead.status == "sales":
        return {
            "id": lead.id,
            "name": lead.name,
            "contact_number": None,
            "postal_address": None,
            "meeting_date": None,
            "meeting_time": None,
            "remark": None,
            "audio_available": bool(lead.audio_path),
            "status": lead.status,
            "created_at": lead.created_at,
        }

    # Other authorized users, and Sales after claiming,
    # can see the full lead details.
    return {
        "id": lead.id,
        "name": lead.name,
        "contact_number": lead.contact_number,
        "postal_address": lead.postal_address,
        "meeting_date": lead.meeting_date,
        "meeting_time": lead.meeting_time,
        "remark": lead.remark,
        "audio_available": bool(lead.audio_path),
        "status": lead.status,
        "created_at": lead.created_at,
    }


@router.post(
    "",
    response_model=LeadListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lead(
    data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("marketing")),
):
    """Create a lead. Only Marketing can use this endpoint."""

    lead = Lead(
        name=data.name,
        contact_number=data.contact_number,
        status="communication",
        created_by_id=current_user.id,
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return format_lead(lead, current_user)


@router.get(
    "",
    response_model=list[LeadListResponse],
)
def list_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only leads relevant to the current user's department."""

    if current_user.role == "marketing":
        statement = select(Lead).where(
            Lead.created_by_id == current_user.id
        )

    elif current_user.role == "communication":
        statement = select(Lead).where(
            Lead.status == "communication"
        )

    elif current_user.role == "vigilance":
        statement = select(Lead).where(
            Lead.status == "vigilance"
        )

    elif current_user.role == "support":
        statement = select(Lead).where(
            Lead.status == "support"
        )

    elif current_user.role == "sales":
        statement = select(Lead).where(
            or_(
                Lead.status == "sales",
                Lead.claimed_by_id == current_user.id,
            )
        )

    else:
        raise HTTPException(
            status_code=403,
            detail="Your role cannot access leads.",
        )

    leads = db.scalars(statement.order_by(Lead.created_at.desc())).all()

    return [
        format_lead(lead, current_user)
        for lead in leads
    ]



@router.patch("/{lead_id}/communication")
def update_communication_details(
    lead_id: int,
    data: CommunicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("communication")
    ),
):
    """Update allowed fields while a lead is in Communication."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "communication":
        raise HTTPException(
            status_code=409,
            detail="This lead is no longer in the Communication stage.",
        )

    # Only fields declared in CommunicationUpdate are applied.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    return format_lead(lead, current_user)


@router.post("/{lead_id}/communication/submit")
def submit_to_vigilance(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("communication")
    ),
):
    """Submit a completed Communication lead to Vigilance."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "communication":
        raise HTTPException(
            status_code=409,
            detail="Only Communication-stage leads can be submitted.",
        )

    missing_fields = []

    if not lead.postal_address:
        missing_fields.append("postal_address")

    if lead.meeting_date is None:
        missing_fields.append("meeting_date")

    if lead.meeting_time is None:
        missing_fields.append("meeting_time")

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Complete the required meeting details first.",
                "missing_fields": missing_fields,
            },
        )

    lead.status = "vigilance"

    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead submitted to Vigilance successfully.",
        "lead": format_lead(lead, current_user),
    }


# Store uploaded recordings inside the backend directory.
AUDIO_DIR = Path(
    os.getenv(
        "VIBANU_AUDIO_DIR",
        str(Path(__file__).resolve().parent.parent / "uploads" / "audio"),
    )
)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20 MB

ALLOWED_AUDIO_TYPES = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".aac",
    ".webm",
}


@router.post("/{lead_id}/vigilance/audio")
def upload_vigilance_audio(
    lead_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("vigilance")
    ),
):
    """Upload the required audio recording for a Vigilance lead."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "vigilance":
        raise HTTPException(
            status_code=409,
            detail="Audio can only be uploaded during the Vigilance stage.",
        )

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio extension.",
        )

    # Generate the server-side filename instead of trusting the
    # uploaded filename.
    destination = AUDIO_DIR / f"{uuid4().hex}{extension}"
    total_size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_AUDIO_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio file exceeds the 20 MB limit.",
                    )

                output.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded audio file is empty.",
            )

        # Store a relative path in the database, not an absolute path.
        relative_path = destination.relative_to(
            AUDIO_DIR.parent.parent
        ).as_posix()

        previous_audio = lead.audio_path
        lead.audio_path = relative_path

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        # Remove the previous file only after the new path is saved.
        if previous_audio:
            previous_path = (
                AUDIO_DIR.parent.parent / previous_audio
            ).resolve()

            try:
                previous_path.relative_to(
                    AUDIO_DIR.parent.parent.resolve()
                )
                if previous_path.is_file():
                    previous_path.unlink()
            except ValueError:
                # Never delete a path outside the upload directory.
                pass

        return {
            "message": "Audio uploaded successfully.",
            "lead_id": lead.id,
            "audio_available": True,
        }

    except Exception:
        # Clean up a partially written or uncommitted new file.
        if destination.exists():
            destination.unlink()
        raise

    finally:
        file.file.close()

import getpass
import sys
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
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
        password = getpass.getpass(f"{role.title()} password: ")

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
    audio_input = input(
        "\nEnter the path to a small .mp3, .wav, .m4a, .ogg, "
        "or .webm file: "
    ).strip().strip('"')

    audio_path = Path(audio_input)

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


@router.post("/{lead_id}/vigilance/verify")
def verify_vigilance_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("vigilance")
    ),
):
    """Verify a lead and move it to the Support stage."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "vigilance":
        raise HTTPException(
            status_code=409,
            detail="Only Vigilance-stage leads can be verified.",
        )

    if not lead.audio_path:
        raise HTTPException(
            status_code=400,
            detail="Upload the required audio before verification.",
        )

    # Confirm the recording still exists within the backend directory.
    audio_file = (AUDIO_DIR.parent.parent / lead.audio_path).resolve()
    audio_root = AUDIO_DIR.resolve()

    try:
        audio_file.relative_to(audio_root)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="The stored audio path is invalid.",
        )

    if not audio_file.is_file():
        raise HTTPException(
            status_code=400,
            detail="The audio file is missing. Upload it again.",
        )

    lead.status = "support"

    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead verified and submitted to Support.",
        "lead": format_lead(lead, current_user),
    }


@router.post("/{lead_id}/support/allocate")
def allocate_lead_to_sales(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("support")
    ),
):
    """Allocate a verified lead to the Sales stage."""

    lead = db.get(Lead, lead_id)

    # 1. Ensure the lead exists.
    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    # 2. Only Support-stage leads can be allocated.
    if lead.status != "support":
        raise HTTPException(
            status_code=409,
            detail="Only verified Support-stage leads can be allocated.",
        )

    # 3. Ensure required meeting information is complete.
    missing_fields = []

    if not lead.postal_address:
        missing_fields.append("postal_address")

    if lead.meeting_date is None:
        missing_fields.append("meeting_date")

    if lead.meeting_time is None:
        missing_fields.append("meeting_time")

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Complete the required meeting details before allocation.",
                "missing_fields": missing_fields,
            },
        )

    # 4. Ensure an audio path is recorded.
    if not lead.audio_path:
        raise HTTPException(
            status_code=400,
            detail="The lead must have an audio recording.",
        )

    # 5. Confirm the audio file exists inside the upload directory.
    audio_root = AUDIO_DIR.resolve()
    audio_file = (AUDIO_DIR.parent.parent / lead.audio_path).resolve()

    try:
        audio_file.relative_to(audio_root)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="The stored audio path is invalid.",
        )

    if not audio_file.is_file():
        raise HTTPException(
            status_code=400,
            detail="The audio recording is missing.",
        )

    # 6. The server controls the workflow transition.
    lead.status = "sales"

    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead allocated to Sales successfully.",
        "lead": format_lead(lead, current_user),
    }


def get_audio_file(lead: Lead) -> Path:
    """Resolve a lead's audio path safely within the upload directory."""

    audio_root = AUDIO_DIR.resolve()

    if not lead.audio_path:
        raise HTTPException(
            status_code=404,
            detail="No audio recording is available.",
        )

    audio_file = (AUDIO_DIR.parent.parent / lead.audio_path).resolve()

    try:
        audio_file.relative_to(audio_root)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid stored audio path.",
        )

    if not audio_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Audio recording not found.",
        )

    return audio_file


@router.get("/{lead_id}/sales/audio")
def stream_sales_audio(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("sales")
    ),
):
    """Allow Sales to listen to audio for an allocated lead."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    # Sales can play an unclaimed lead or their own claimed lead.
    if not (
        lead.status == "sales"
        or (
            lead.status == "claimed"
            and lead.claimed_by_id == current_user.id
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="This lead is not available to your Sales account.",
        )

    audio_file = get_audio_file(lead)

    return FileResponse(
        path=audio_file,
        media_type="application/octet-stream",
        filename=audio_file.name,
        content_disposition_type="inline",
    )


@router.post("/{lead_id}/sales/playback-complete")
def mark_playback_complete(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("sales")
    ),
):
    """Record the Sales user's playback-completion acknowledgement."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "sales":
        raise HTTPException(
            status_code=409,
            detail="Only unclaimed Sales-stage leads can be played for claiming.",
        )

    # Do not record completion if the actual file is missing.
    get_audio_file(lead)

    playback = db.scalar(
        select(AudioPlayback).where(
            AudioPlayback.lead_id == lead.id,
            AudioPlayback.user_id == current_user.id,
        )
    )

    if playback is None:
        playback = AudioPlayback(
            lead_id=lead.id,
            user_id=current_user.id,
            completed_at=datetime.utcnow(),
        )
        db.add(playback)
    else:
        playback.completed_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Playback completion acknowledgement recorded.",
        "lead_id": lead.id,
        "completed": True,
    }


@router.post("/{lead_id}/sales/claim")
def claim_sales_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("sales")
    ),
):
    """Claim a lead after recording playback completion."""

    lead = db.get(Lead, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    if lead.status != "sales":
        raise HTTPException(
            status_code=409,
            detail="This lead is no longer available to claim.",
        )

    playback = db.scalar(
        select(AudioPlayback).where(
            AudioPlayback.lead_id == lead.id,
            AudioPlayback.user_id == current_user.id,
        )
    )

    if playback is None:
        raise HTTPException(
            status_code=403,
            detail="Play the complete audio before claiming this lead.",
        )

    # Atomically claim the lead only if it is still available.
    result = db.execute(
        update(Lead)
        .where(
            Lead.id == lead_id,
            Lead.status == "sales",
            Lead.claimed_by_id.is_(None),
        )
        .values(
            status="claimed",
            claimed_by_id=current_user.id,
        )
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Another user has claimed this lead, "
                "or it is no longer available."
            ),
        )

    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead claimed successfully.",
        "lead": format_lead(lead, current_user),
    }
