"""Deterministic operations only; no eval, model calls, or inferred cutoffs."""
from .validation import numeric_range, localized


def compute(definition, specification, answers, language):
    items = {i["id"]: i for i in definition["items"]}
    scores, trace = {}, {}
    for dim in specification["dimensions"]:
        contributions = []
        total = minimum = maximum = weight_sum = 0.0
        for term in dim["terms"]:
            iid = term["item"]
            raw = answers[iid]
            weight = term.get("weight", 1)
            if dim["operation"] == "correct_count":
                def norm(v):
                    return str(v).strip().casefold() if isinstance(v, str) else v
                coded = int(any(norm(raw) == norm(a) for a in term["accepted"]))
                lo, hi = 0, 1
            else:
                lo, hi = numeric_range(items[iid])
                coded = lo + hi - raw if term.get("reverse", False) else raw
            total += coded * weight
            weight_sum += weight
            minimum += lo * weight
            maximum += hi * weight
            contributions.append({"item_id": iid, "raw": raw, "reverse": term.get("reverse", False),
                                  "coded": coded, "weight": weight, "contribution": coded * weight})
        value = total
        if dim["operation"] in {"mean", "centered_mean"}:
            value, minimum, maximum = (v / weight_sum for v in (value, minimum, maximum))
        center = None
        if dim["operation"] == "centered_mean":
            ref = dim["reference_items"]
            center = sum(answers[i] for i in ref) / len(ref)
            value -= center
            # Bounds for a centered score depend jointly on all reference answers.
            # Do not present the uncentered range as a centered norm.
            minimum = maximum = None
        offset = dim.get("offset", 0)
        value += offset
        if minimum is not None:
            minimum += offset
            maximum += offset
        scores[dim["id"]] = {"name": localized(dim["name"], language), "value": value,
                            "range": [minimum, maximum] if minimum is not None else None,
                            "item_count": len(contributions), "operation": dim["operation"],
                            "description": localized(dim["description"], language)}
        interpretation = None
        if dim.get('interpretation'):
            rule=dim['interpretation']
            band=next((b for b in rule['bands'] if b['min'] <= value <= b['max']),None)
            if band is not None:
                interpretation={'label':localized(band['label'],language),
                                'score_interval':[band['min'],band['max']],
                                'source':rule['source']}
                scores[dim['id']]['interpretation']=interpretation
        trace[dim["id"]] = {"terms": contributions, "weighted_sum": total, "weight_sum": weight_sum,
                            "reference_mean": center, "offset": offset, "result": value,
                            "interpretation": interpretation}
    return scores, trace
