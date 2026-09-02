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

    def resolve_team(self, provider_name: str, candidates: list[str], *, allow_mascot_prefix: bool = True) -> tuple[str | None, str]:
        """Resolve a provider team name to a canonical model key without unsafe shortening.

        Exact/alias resolution is preferred. Mascot-prefix resolution is allowed only
        when the provider adds at most two trailing mascot words, and the longest
        candidate prefix is unique. This prevents errors such as Arkansas-Pine Bluff
        being silently mapped to Arkansas.
        """
        n = norm_team(provider_name)
        if not n:
            return None, "ENTITY_RESOLUTION_FAILED"
        if n in self.aliases:
            return self.aliases[n], "ALIAS"
        exact = {norm_team(c): c for c in candidates if norm_team(c)}
        if n in exact:
            return exact[n], "EXACT"

        if allow_mascot_prefix:
            n_words = n.split()
            prefix = []
            for cn, original in exact.items():
                c_words = cn.split()
                if len(c_words) < 1:
                    continue
                # Provider may be canonical school name + one/two mascot words.
                if n.startswith(cn + " ") and 1 <= len(n_words) - len(c_words) <= 2:
                    prefix.append((len(c_words), original))
            if prefix:
                longest = max(x[0] for x in prefix)
                winners = [original for length, original in prefix if length == longest]
                if len(winners) == 1:
                    return winners[0], "UNIQUE_LONGEST_MASCOT_PREFIX"

        matches = difflib.get_close_matches(n, list(exact), n=2, cutoff=0.94)
        if len(matches) == 1:
            return exact[matches[0]], "FUZZY_FLAGGED"
        return None, "ENTITY_RESOLUTION_FAILED"
