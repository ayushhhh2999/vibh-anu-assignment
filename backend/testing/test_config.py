import getpass
import os
from pathlib import Path
import tempfile
import wave

from dotenv import dotenv_values


TEST_ENV = Path(__file__).resolve().parents[2] / "test_kit" / ".env.test"
TEST_VALUES = dotenv_values(TEST_ENV)
BASE_URL = os.getenv("VIBANU_TEST_API_URL") or TEST_VALUES.get(
    "VIBANU_TEST_API_URL", "http://127.0.0.1:8000"
)


def test_password(role: str) -> str:
    name = f"E2E_{role.upper()}_PASSWORD"
    password = os.getenv(name) or TEST_VALUES.get(name)
    if password:
        return password
    return getpass.getpass(f"{role.title()} password: ")


def audio_fixture_path() -> Path:
    configured_path = os.getenv("VIBANU_TEST_AUDIO_PATH")
    if configured_path:
        path = Path(configured_path)
        if not path.is_file():
            raise FileNotFoundError(f"Configured test audio fixture does not exist: {path}")
        return path

    work_dir = Path(os.getenv("VIBANU_TEST_WORKDIR", tempfile.gettempdir()))
    work_dir.mkdir(parents=True, exist_ok=True)
    fixture = work_dir / "vibhanu-backend-test.wav"
    with wave.open(str(fixture), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 8000)
    return fixture