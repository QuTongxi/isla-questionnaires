"""Strict, dependency-free validation of versioned data and declarative rules."""
import math
from .errors import DefinitionError, AnswerError


def localized(value, language):
    if isinstance(value, str):
        return value
    if not isinstance(value, dict) or language not in value:
        raise DefinitionError(f"Missing {language!r} translation; silent fallback is disabled")
    return value[language]


def validate_answer(item, value):
    kind = item["type"]
    if kind == "text":
        if not isinstance(value, str) or not value.strip():
            raise AnswerError(f"{item['id']}: a nonempty text answer is required")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AnswerError(f"{item['id']}: a finite number is required (booleans are not answers)")
    if kind == "choice":
        allowed = [o["value"] for o in item["options"]]
        if value not in allowed:
            raise AnswerError(f"{item['id']}: choose one of {allowed}")
    elif kind == "number":
        if item.get("integer", False) and value != int(value):
            raise AnswerError(f"{item['id']}: an integer is required")
        if "min" in item and value < item["min"] or "max" in item and value > item["max"]:
            raise AnswerError(f"{item['id']}: answer is outside its defined range")
    else:
        raise DefinitionError(f"Unsupported response type: {kind}")
    return value


def numeric_range(item):
    if item["type"] == "choice":
        vals = [o["value"] for o in item["options"]]
        return min(vals), max(vals)
    if item["type"] == "number" and "min" in item and "max" in item:
        return item["min"], item["max"]
    raise DefinitionError(f"{item['id']}: scoring requires an explicit finite response range")


def validate_definition(definition, scoring):
    def require(condition, message):
        if not condition:
            raise DefinitionError(message)

    require(definition.get("schema_version") == 1 and scoring.get("schema_version") == 1, "Unsupported schema version")
    for key in ("id", "version", "name", "languages", "default_language", "instructions", "items", "status"):
        require(bool(definition.get(key)), f"Missing definition field {key}")
    require(definition["status"] in {"available", "review_required"}, "Unknown release status")
    require(definition["default_language"] in definition["languages"], "Default language is unavailable")
    for lang in definition['languages']:
        require(isinstance(localized(definition['name'],lang),str), 'Invalid questionnaire name')
    require(scoring.get("questionnaire_id") == definition["id"], "Scoring belongs to a different questionnaire")
    require(scoring.get("missing_policy") == "require_complete", "Unsupported missing-answer policy")
    require(scoring.get("mode") in {"automatic", "manual", "export_only"}, "Unknown scoring mode")
    items = {}
    for item in definition["items"]:
        require(isinstance(item.get("id"), str) and item["id"] not in items, "Duplicate or invalid item ID")
        require(item.get("type") in {"choice", "number", "text"}, f"Unsupported item type: {item.get('type')}")
        for lang in definition["languages"]:
            require(bool(localized(item.get("text"), lang)), f"Empty question {item['id']} ({lang})")
            localized(definition["instructions"], lang)
            if item.get("help"):
                localized(item["help"], lang)
        if item["type"] == "choice":
            opts = item.get("options", [])
            require(len(opts) >= 2, f"{item['id']}: at least two choices required")
            vals = [o.get("value") for o in opts]
            require(all(type(v) in (int, float) and math.isfinite(v) for v in vals), "Invalid option value")
            require(len(vals) == len(set(vals)), "Duplicate option values")
            for opt in opts:
                for lang in definition["languages"]:
                    localized(opt.get("label"), lang)
        if item["type"] == "number":
            require(type(item.get('integer',False)) is bool, 'integer must be boolean')
            for bound in ("min", "max"):
                if bound in item:
                    require(type(item[bound]) in (int, float) and math.isfinite(item[bound]), "Invalid numeric bound")
            require(item.get("min", -math.inf) <= item.get("max", math.inf), "Inverted answer range")
        items[item["id"]] = item
    if "expected_items" in definition:
        require(len(items) == definition["expected_items"], "Item count differs from declared form")
    dims = scoring.get("dimensions", [])
    require(scoring["mode"] != "automatic" or bool(dims), "Automatic scoring has no dimensions")
    dim_ids = set()
    for dim in dims:
        require(dim.get("id") and dim["id"] not in dim_ids, "Duplicate or missing dimension ID")
        dim_ids.add(dim["id"])
        require(dim.get("operation") in {"sum", "mean", "centered_mean", "correct_count"}, "Unsupported score operation")
        terms = dim.get("terms", [])
        require(bool(terms), "Empty scoring dimension")
        seen = set()
        for term in terms:
            iid = term.get("item")
            require(iid in items and iid not in seen, f"Unknown or duplicate scored item: {iid}")
            seen.add(iid)
            require(type(term.get("reverse", False)) is bool, "reverse must be boolean")
            weight = term.get("weight", 1)
            require(type(weight) in (int, float) and math.isfinite(weight) and weight > 0, "Invalid item weight")
            if dim["operation"] == "correct_count":
                require(bool(term.get("accepted")), "Missing answer key")
                require(isinstance(term['accepted'],list), 'Answer key must be a list')
                for answer in term['accepted']:
                    try:
                        validate_answer(items[iid],answer)
                    except AnswerError as error:
                        raise DefinitionError(f'Invalid keyed answer: {error}') from error
                require(not term.get("reverse"), "Correctness keys cannot use reverse coding")
            else:
                require(items[iid]["type"] != "text", "Text responses require an explicit answer key or human review")
                numeric_range(items[iid])
        if dim["operation"] == "centered_mean":
            ref = dim.get("reference_items", [])
            require(bool(ref) and len(ref) == len(set(ref)) and set(ref) <= items.keys(), "Invalid centering reference")
            for iid in ref:
                numeric_range(items[iid])
        require(type(dim.get("offset", 0)) in (int, float) and math.isfinite(dim.get("offset", 0)), "Invalid score offset")
        for lang in definition["languages"]:
            localized(dim.get("name"), lang)
            localized(dim.get("description"), lang)
        if dim.get('interpretation'):
            rule=dim['interpretation']
            require(isinstance(rule.get('source'),str) and bool(rule['source']), 'Interpretation needs an explicit source')
            require(isinstance(rule.get('bands'),list) and bool(rule['bands']), 'Interpretation has no bands')
            previous=-math.inf
            for band in rule['bands']:
                require(all(type(band.get(k)) in (int,float) and math.isfinite(band[k]) for k in ['min','max']), 'Invalid interpretation bounds')
                require(previous < band['min'] <= band['max'], 'Overlapping or unordered interpretation bands')
                previous=band['max']
                for lang in definition['languages']:localized(band.get('label'),lang)
    return {"valid": True, "items": len(items), "dimensions": len(dims), "status": definition["status"]}
