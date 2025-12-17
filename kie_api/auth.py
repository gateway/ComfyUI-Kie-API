from pathlib import Path


KIE_KEY_PATH = Path(__file__).resolve().parent.parent / "config" / "kie_key.txt"


def _load_api_key() -> str:
    try:
        api_key = KIE_KEY_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "KIE API key not found. Please create config/kie_key.txt with your API key."
        ) from exc
    if not api_key:
        raise RuntimeError("KIE API key file is empty. Please add your key to config/kie_key.txt.")
    return api_key
