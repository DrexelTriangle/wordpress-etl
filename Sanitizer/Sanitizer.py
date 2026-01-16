from abc import ABC, abstractmethod
from datetime import datetime
import json
import os

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
    def _autoResolve(self):
        raise NotImplementedError

    @abstractmethod
    def _manualResolve(self):
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
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, filename+".json"), "w+", encoding="utf-8") as file:
            json.dump(
                {
                    "changes": self._serializeChanges(),
                },
                file,
                indent=4,
            )
        conflicts_path = os.path.join(log_dir, conflictName+".json")
        existing_conflicts = []
        if os.path.exists(conflicts_path):
            try:
                with open(conflicts_path, "r", encoding="utf-8") as file:
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
        with open(conflicts_path, "w+", encoding="utf-8") as file:
            json.dump(
                {
                    "conflicts": new_conflicts,
                },
                file,
                indent=4,
            )
