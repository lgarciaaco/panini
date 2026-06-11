"""Loads and queries the sticker catalog."""
import json
import os
from functools import lru_cache
from typing import Optional

_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")


@lru_cache(maxsize=1)
def load() -> list[dict]:
    path = os.path.normpath(_CATALOG_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Catalog not found at {path}. Run: python scripts/build_catalog.py"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def by_code(code: str) -> Optional[dict]:
    code = code.upper().replace(" ", "")
    return next((s for s in load() if s["code"] == code), None)


def all_codes() -> set[str]:
    return {s["code"] for s in load()}


def by_team(team_code: str) -> list[dict]:
    return [s for s in load() if s.get("team_code") == team_code.upper()]


def teams() -> list[str]:
    seen, result = set(), []
    for s in load():
        tc = s.get("team_code")
        if tc and tc != "FWC" and tc not in seen:
            seen.add(tc)
            result.append(tc)
    return result


def groups() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for s in load():
        grp = s.get("group")
        tc = s.get("team_code")
        if grp and tc and tc != "FWC":
            result.setdefault(grp, [])
            if tc not in result[grp]:
                result[grp].append(tc)
    return result


def team_meta(team_code: str) -> dict:
    stickers = by_team(team_code)
    if not stickers:
        return {}
    s = stickers[0]
    return {
        "team_code": team_code,
        "team_name": s["team_name"],
        "flag": s["flag"],
        "group": s["group"],
        "total": len(stickers),
    }
