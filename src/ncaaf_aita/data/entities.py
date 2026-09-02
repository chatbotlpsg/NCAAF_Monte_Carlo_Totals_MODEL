from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


def norm_team(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    drop = {"university", "college", "the"}
    return " ".join(x for x in s.split() if x not in drop)


@dataclass
class EntityResolver:
    aliases: dict[str, str] = field(default_factory=dict)

    def resolve_team(self, provider_name: str, candidates: list[str]) -> tuple[str | None, str]:
        n = norm_team(provider_name)
        if n in self.aliases:
            return self.aliases[n], "ALIAS"
        exact = {norm_team(c): c for c in candidates}
        if n in exact:
            return exact[n], "EXACT"
        matches = difflib.get_close_matches(n, list(exact), n=2, cutoff=0.92)
        if len(matches) == 1:
            return exact[matches[0]], "FUZZY_FLAGGED"
        return None, "ENTITY_RESOLUTION_FAILED"
