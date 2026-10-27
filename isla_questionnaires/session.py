import copy
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from .catalog import digest, load_bundle
from .errors import AnswerError, IncompleteQuestionnaire, IntegrityError, ReviewRequired, DefinitionError
from .validation import validate_answer, localized
from .scoring import compute


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    type: str
    options: tuple
    help: str
    number: int
    total: int
    min: float | None = None
    max: float | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Result:
    questionnaire_id: str
    version: str
    status: str
    scores: dict
    content_hash: str
    verification: dict

    def to_dict(self):
        return asdict(self)


class Questionnaire:
    def __init__(self, bundle, *, language=None, parameters=None):
        self._bundle = copy.deepcopy(bundle)
        self._d = self._bundle["questionnaire"]
        self._rules = self._bundle["scoring"]
        self.language = language or self._d["default_language"]
        if self.language not in self._d["languages"]:
            raise DefinitionError(f"Available languages: {self._d['languages']}; no implicit translation")
        self._parameters = dict(parameters or {})
        declared = self._d.get("parameters", {})
        if set(self._parameters) - declared.keys():
            raise DefinitionError("Unknown questionnaire parameter")
        for key, spec in declared.items():
            if spec.get("required") and not str(self._parameters.get(key, "")).strip():
                raise DefinitionError(f"Required parameter: {key}")
            if key in self._parameters and not isinstance(self._parameters[key], str):
                raise DefinitionError(f"{key}: parameter must be text")
        self._answers = {}
        self._events = []
        self._items = {i["id"]: i for i in self._d["items"]}
        self.content_hash = digest(self._bundle)

    @property
    def id(self):
        return self._d["id"]

    @property
    def version(self):
        return self._d["version"]

    @property
    def answers(self):
        return copy.deepcopy(self._answers)

    @property
    def is_complete(self):
        return len(self._answers) == len(self._items)

    @property
    def capabilities(self):
        return {"local_judge": self._rules["mode"] == "automatic" and self._d["status"] == "available",
                "mode": self._rules["mode"], "export": True, "resume": True,
                "status": self._d["status"]}

    def _text(self, value):
        text = localized(value, self.language)
        for name, value in self._parameters.items():
            text = text.replace("{{" + name + "}}", value)
        return text

    def describe(self):
        return {"id": self.id, "name": self._text(self._d["name"]), "version": self.version,
                "language": self.language, "instructions": self._text(self._d["instructions"]),
                "item_count": len(self._items), "answered": len(self._answers),
                "capabilities": self.capabilities, "content_hash": self.content_hash,
                "review_notes": copy.deepcopy(self._d.get("review_notes", [])),
                "notes": copy.deepcopy(self._d.get("notes", []))}

    def audit_definition(self):
        """Inspect the form, keys, unscored items, and provenance before answering."""
        from .validation import validate_definition
        scored = {t['item'] for d in self._rules['dimensions'] for t in d['terms']}
        return {"questionnaire": self.describe(),
                "validation": validate_definition(self._d, self._rules),
                "unscored_items": [i for i in self._items if i not in scored],
                "scoring": copy.deepcopy(self._rules), "provenance": self.provenance()}

    def provenance(self):
        return copy.deepcopy(self._bundle["provenance"])

    def questions(self):
        for number, item in enumerate(self._d["items"], 1):
            yield Question(item["id"], self._text(item["text"]), item["type"],
                           tuple({"value": o["value"], "label": self._text(o["label"])} for o in item.get("options", [])),
                           self._text(item["help"]) if item.get("help") else "", number, len(self._items),
                           item.get("min"), item.get("max"))

    def next_question(self):
        """Peek at the first unanswered question. Repeated reads do not skip items."""
        return next((q for q in self.questions() if q.id not in self._answers), None)

    def submit_answer(self, question_id, value, *, replace=False):
        if type(replace) is not bool:
            raise AnswerError("replace must be a boolean")
        if question_id not in self._items:
            raise AnswerError(f"Unknown question: {question_id}")
        if question_id in self._answers and not replace:
            raise AnswerError("Answer already exists; use replace=True for an audited revision")
        validate_answer(self._items[question_id], value)
        event = {"seq": len(self._events) + 1, "previous": self._events[-1]["hash"] if self._events else self.content_hash,
                 "question_id": question_id, "value": value, "replace": replace}
        event["hash"] = digest(event)
        self._events.append(event)
        self._answers[question_id] = value
        return self.next_question()

    def submit_answers(self, answers, *, replace=False):
        """Validate the complete batch first, so invalid batches never partly apply."""
        if not isinstance(answers, dict) or type(replace) is not bool:
            raise AnswerError("answers must be an item-ID mapping and replace must be boolean")
        for iid, value in answers.items():
            if iid not in self._items:
                raise AnswerError(f"Unknown question: {iid}")
            if iid in self._answers and not replace:
                raise AnswerError(f"Answer already exists: {iid}")
            validate_answer(self._items[iid], value)
        for iid, value in answers.items():
            self.submit_answer(iid, value, replace=replace)
        return self.next_question()

    def _require_complete(self):
        missing = [i for i in self._items if i not in self._answers]
        if missing:
            raise IncompleteQuestionnaire(f"Unanswered items: {', '.join(missing)}")

    def judge(self):
        self._require_complete()
        if self._d["status"] != "available":
            raise ReviewRequired("Scoring is blocked pending resolution of the documented source issues")
        mode = self._rules["mode"]
        scores = compute(self._d, self._rules, self._answers, self.language)[0] if mode == "automatic" else {}
        status = "scored" if mode == "automatic" else "needs_human_review" if mode == "manual" else "export_only"
        return Result(self.id, self.version, status, scores, self.content_hash,
                      copy.deepcopy(self._bundle["provenance"].get("verification", {})))

    def audit_score(self):
        result = self.judge()
        trace = compute(self._d, self._rules, self._answers, self.language)[1] if result.status == "scored" else {}
        return {"result": result.to_dict(), "trace": trace, "events": copy.deepcopy(self._events),
                "scoring": copy.deepcopy(self._rules), "provenance": self.provenance()}

    def export_session(self, path=None):
        value = {"schema_version": 1, "questionnaire_id": self.id, "version": self.version,
                 "language": self.language, "parameters": self._parameters, "content_hash": self.content_hash,
                 "answers": self.answers, "events": copy.deepcopy(self._events)}
        value["session_hash"] = digest(value)
        if path is not None:
            Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return copy.deepcopy(value)

    def print(self, *, format="markdown", file=None):
        """Print AND return the complete answer sheet; never infer a human verdict."""
        if format == "json":
            text = json.dumps({"questionnaire": self.describe(), "questions": [q.to_dict() for q in self.questions()],
                               "session": self.export_session()}, ensure_ascii=False, indent=2)
        elif format == "markdown":
            lines = [f"# {self.describe()['name']}", "", f"ID: {self.id} · version: {self.version} · language: {self.language}",
                     f"Content SHA-256: {self.content_hash}", "", self.describe()["instructions"], ""]
            for q in self.questions():
                lines.extend([f"## {q.number}. {q.text}", "", f"Item ID: {q.id}"])
                if q.help:
                    lines.append(q.help)
                lines.extend(f"- {o['value']}: {o['label']}" for o in q.options)
                lines.extend(["", "Answer: " + str(self._answers.get(q.id, "[unanswered]")), ""])
            text = "\n".join(lines)
        else:
            raise ValueError("Supported formats: markdown, json")
        (file or sys.stdout).write(text + "\n")
        return text


def load_questionnaire(identifier, *, language=None, version=None, parameters=None, allow_review=False, data_root=None):
    bundle = load_bundle(identifier, allow_review=allow_review, data_root=data_root)
    if version is not None and version != bundle["questionnaire"]["version"]:
        raise DefinitionError("Requested version is not installed")
    return Questionnaire(bundle, language=language, parameters=parameters)


def restore_session(source, *, data_root=None, allow_review=False):
    data = copy.deepcopy(source) if isinstance(source, dict) else json.loads(Path(source).read_text(encoding="utf-8"))
    required = {"session_hash", "schema_version", "questionnaire_id", "version", "language", "parameters", "content_hash", "answers", "events"}
    if not isinstance(data, dict) or set(data) != required:
        raise IntegrityError("Session fields are missing or unsupported")
    if not isinstance(data["events"], list) or not isinstance(data["answers"], dict) or not isinstance(data["parameters"], dict):
        raise IntegrityError("Invalid session data types")
    given_hash = data.pop("session_hash", None)
    if given_hash != digest(data) or data.get("schema_version") != 1:
        raise IntegrityError("Session integrity/schema check failed")
    q = load_questionnaire(data["questionnaire_id"], language=data["language"], version=data["version"],
                           parameters=data["parameters"], data_root=data_root, allow_review=allow_review)
    if data["content_hash"] != q.content_hash:
        raise IntegrityError("Session was created against different questionnaire content")
    for event in data["events"]:
        if not isinstance(event, dict) or set(event) != {"seq", "previous", "question_id", "value", "replace", "hash"}:
            raise IntegrityError("Malformed answer event")
        body = {k: v for k, v in event.items() if k != "hash"}
        if digest(body) != event["hash"]:
            raise IntegrityError("Invalid answer event hash")
        q.submit_answer(event["question_id"], event["value"], replace=event["replace"])
        if q._events[-1] != event:
            raise IntegrityError("Broken event sequence")
    if q.answers != data["answers"]:
        raise IntegrityError("Answers do not match the event history")
    return q


# Backward-compatible spelling requested in the initial API sketch.
Questionaire = Questionnaire
load_questionaire = load_questionnaire
