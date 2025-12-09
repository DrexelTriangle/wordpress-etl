from typing import TypedDict

class PolicyDict(TypedDict):
    auto_threshold: float
    manual_threshold: float
    discard_threshold: float
