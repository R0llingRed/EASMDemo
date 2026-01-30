"""Scan target filtering with blacklist/whitelist."""
import re
from typing import List, Optional, Set


class ScanFilter:
    """Filter scan targets based on blacklist/whitelist rules."""

    def __init__(
        self,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
    ):
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
        self._whitelist_patterns = self._compile_patterns(self.whitelist)
        self._blacklist_patterns = self._compile_patterns(self.blacklist)

    def _compile_patterns(self, patterns: Set[str]) -> List[re.Pattern]:
        """Compile glob-like patterns to regex."""
        compiled = []
        for p in patterns:
            regex = p.replace(".", r"\.").replace("*", ".*")
            compiled.append(re.compile(f"^{regex}$", re.IGNORECASE))
        return compiled

    def is_allowed(self, target: str) -> bool:
        """Check if target is allowed for scanning."""
        # Blacklist takes precedence
        for pattern in self._blacklist_patterns:
            if pattern.match(target):
                return False

        # If whitelist is defined, target must match
        if self._whitelist_patterns:
            for pattern in self._whitelist_patterns:
                if pattern.match(target):
                    return True
            return False

        return True

    def filter_targets(self, targets: List[str]) -> List[str]:
        """Filter list of targets."""
        return [t for t in targets if self.is_allowed(t)]
