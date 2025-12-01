from abc import ABC, abstractmethod
from datetime import datetime
import json
import os

class Sanitizer(ABC):
    def __init__(self, data: list, policies: dict, logDir: str = "./logs"):
        self.data = data
        self.policies = policies
        self.logDir = logDir
        self.changes = []
        self.conflicts = []

    @abstractmethod
    def normalizeData(self):
        raise NotImplementedError

    @abstractmethod
    def autoResolve(self):
        raise NotImplementedError

    @abstractmethod
    def manualResolve(self):
        raise NotImplementedError

    @abstractmethod
    def sanitize(self):
        raise NotImplementedError

    def _recordChange(self, obj, field, old, new):
        change = {
            "id": obj["id"],
            "field": field,
            "old": old,
            "new": new
        }
        self.conflicts.append(change)

    def _recordConflict(self, obj, field, reason, details):
        conflict = {
            "id": obj["id"],
            "field": field,
            "reason": reason,
            "details": details
        }

    def _log(self, filename=(datetime.now().strftime("%H:%M:%S") + "_sanitization_report.json")):
        os.makedirs(self.logDir, exist_ok=True)
        with open(os.path.join(self.logDir, filename), "w+", encoding="utf-8") as file:
            json.dump({"Changes": self.changes}, {"conflicts": self.conflicts})
