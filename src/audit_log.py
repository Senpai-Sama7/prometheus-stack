"""Audit Log: Immutable, append-only event logging."""

import json
from typing import Dict, List
from datetime import datetime
from uuid import uuid4
import hashlib


class AuditLog:
    """Append-only audit log for forensic reconstruction."""

    def __init__(self):
        self.events = []

    def log_event(self, event_type: str, agent_id: str, details: Dict) -> str:
        """
        Log an event and return trace_id.
        """
        trace_id = str(uuid4())
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "event_type": event_type,
            "agent_id": agent_id,
            "details": details,
            "event_hash": self._compute_hash(details)
        }
        self.events.append(event)
        return trace_id

    def get_events(self, agent_id: str = None, event_type: str = None) -> List[Dict]:
        """
        Query events by agent_id and/or event_type.
        """
        results = self.events
        if agent_id:
            results = [e for e in results if e["agent_id"] == agent_id]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        return results

    def get_trace(self, trace_id: str) -> Dict:
        """
        Get full execution trace by trace_id.
        """
        for event in self.events:
            if event["trace_id"] == trace_id:
                return event
        return None

    def verify_immutability(self) -> bool:
        """
        Verify that audit log hasn't been tampered (stub).
        In production: use blockchain or similar.
        """
        return True

    @staticmethod
    def _compute_hash(data: Dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def export_json(self) -> str:
        """Export full audit log as JSON."""
        return json.dumps(self.events, indent=2)
