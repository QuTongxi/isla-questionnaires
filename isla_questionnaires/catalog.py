"""Load bundled files only. The source repositories are never imported."""
import hashlib
import json
import re
from importlib.resources import files
from pathlib import Path
from .errors import DefinitionError, IntegrityError, ReviewRequired
from .validation import validate_definition


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def data_directory():
    return Path(str(files("isla_questionnaires").joinpath("data")))


def list_questionnaires(*, include_review=False, data_root=None):
    root = Path(data_root) if data_root else data_directory()
    entries = json.loads((root / "catalog.json").read_text(encoding="utf-8"))["questionnaires"]
    return [e for e in entries if include_review or e["status"] == "available"]


def load_bundle(identifier, *, data_root=None, allow_review=False):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier):
        raise DefinitionError("Invalid questionnaire identifier")
    root = Path(data_root) if data_root else data_directory()
    matches = [e for e in list_questionnaires(include_review=True, data_root=root) if e["id"] == identifier]
    if not matches:
        raise DefinitionError(f"Unknown questionnaire: {identifier}")
    entry = matches[0]
    bundle = {}
    for name in ("questionnaire", "scoring", "provenance"):
        path = root / identifier / f"{name}.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"][name]:
            raise IntegrityError(f"Changed {name}.json for {identifier}; rebuild and review the catalog")
        bundle[name] = json.loads(raw)
    d = bundle["questionnaire"]
    if d["id"] != identifier or d["version"] != entry["version"] or d["status"] != entry["status"]:
        raise IntegrityError("Catalog/definition identity mismatch")
    validate_definition(d, bundle["scoring"])
    for source in bundle["provenance"].get("files", []):
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise IntegrityError("Source evidence path escapes the package")
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise IntegrityError(f"Source evidence changed: {source['path']}")
    if d["status"] == "review_required" and not allow_review:
        raise ReviewRequired(f"{identifier}: " + "; ".join(d.get("review_notes", [])))
    return bundle
