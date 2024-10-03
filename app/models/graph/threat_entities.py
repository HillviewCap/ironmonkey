from __future__ import annotations
from typing import Dict, Any

class GraphEntity:
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

class ThreatActor(GraphEntity):
    def __init__(self, name: str):
        self.label = 'ThreatActor'
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        return {'label': self.label, 'name': self.name}

class Tool(GraphEntity):
    def __init__(self, name: str):
        self.label = 'Tool'
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        return {'label': self.label, 'name': self.name}

# Define other entity classes as needed (e.g., Infrastructure, Campaign)
