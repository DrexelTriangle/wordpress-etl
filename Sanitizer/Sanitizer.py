from abc import ABC, abstractmethod
import json
import os
from pathlib import Path

_CRITICAL_CONFLICT_LOGS = {"auth_conflicts", "gauth_conflicts"}


def _truthy_env(name):
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")

class Sanitizer(ABC):
    def __init__(self, data: list, policies: dict):
        self.data = data
        self.policies = policies
        self.changes = []
        self.conflicts = []

    @abstractmethod
    def _normalizeData(self):
        raise NotImplementedError

    @abstractmethod
    def sanitize(self):
        raise NotImplementedError
    
    @abstractmethod
    def _logChange(self):
        raise NotImplementedError

    @abstractmethod
    def _logConflict(self):
        raise NotImplementedError
    
    def _serializeChanges(self):
        serialized = []
        for change in self.changes:
            if isinstance(change, list):
                serialized.append([
                    item.data if hasattr(item, "data") else item
                    for item in change
                ])
            else:
                serialized.append(change.data if hasattr(change, "data") else change)
        return serialized

    def _serializeConflicts(self):
        serialized = []
        for conflict in self.conflicts:
            if isinstance(conflict, list):
                serialized.append([
                    item.data if hasattr(item, "data") else item
                    for item in conflict
                ])
            else:
                serialized.append(conflict.data if hasattr(conflict, "data") else conflict)
        return serialized

    def _log(self, filename, conflictName):
        write_noncritical_logs = _truthy_env("WP_SANITIZER_NONCRITICAL_LOGS")
        write_conflicts = conflictName in _CRITICAL_CONFLICT_LOGS or write_noncritical_logs
        if not write_noncritical_logs and not write_conflicts:
            return

        logDir = Path("logs")
        logDir.mkdir(parents=True, exist_ok=True)
        if write_noncritical_logs:
            changesPath = logDir / f"{filename}.json"
            changesPath.parent.mkdir(parents=True, exist_ok=True)
            with changesPath.open("w+", encoding="utf-8") as file:
                json.dump(
                    {
                        "changes": self._serializeChanges(),
                    },
                    file,
                    indent=4,
                )
        if not write_conflicts:
            return

        conflictsPath = logDir / f"{conflictName}.json"
        conflictsPath.parent.mkdir(parents=True, exist_ok=True)
        existing_conflicts = []
        if conflictsPath.exists():
            try:
                with conflictsPath.open("r", encoding="utf-8") as file:
                    payload = json.load(file)
                existing_conflicts = payload.get("conflicts", payload) if isinstance(payload, dict) else payload
                if not isinstance(existing_conflicts, list):
                    existing_conflicts = []
            except (OSError, json.JSONDecodeError):
                existing_conflicts = []
        new_conflicts = self._serializeConflicts()
        if existing_conflicts:
            seen = set()
            merged = []
            for conflict in existing_conflicts + new_conflicts:
                key = json.dumps(conflict, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(conflict)
            new_conflicts = merged
        with conflictsPath.open("w+", encoding="utf-8") as file:
            json.dump(
                {
                    "conflicts": new_conflicts,
                },
                file,
                indent=4,
            )
