"""Decision trace logging for persona assignment."""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class DecisionTrace:
    """Trace of persona assignment decision."""
    user_id: str
    timestamp: datetime
    assigned_personas: List[str]  # List of persona IDs
    primary_persona: str  # Highest priority persona
    matching_results: Dict[str, Dict[str, Any]]  # persona_id -> {matched: bool, reasons: List[str]}
    features_snapshot: Dict[str, Any]  # Snapshot of features used
    rationale: str  # Plain-language explanation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'assigned_personas': self.assigned_personas,
            'primary_persona': self.primary_persona,
            'matching_results': self.matching_results,
            'features_snapshot': self.features_snapshot,
            'rationale': self.rationale
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionTrace':
        """Create from dictionary."""
        return cls(
            user_id=data['user_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            assigned_personas=data['assigned_personas'],
            primary_persona=data['primary_persona'],
            matching_results=data['matching_results'],
            features_snapshot=data['features_snapshot'],
            rationale=data['rationale']
        )


class DecisionTraceLogger:
    """Logs persona assignment decisions."""
    
    def __init__(self, output_dir: str = "data/persona_traces"):
        """Initialize logger.
        
        Args:
            output_dir: Directory to store trace files
        """
        from pathlib import Path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def log_trace(self, trace: DecisionTrace):
        """Log a decision trace.
        
        Args:
            trace: Decision trace to log
        """
        # Save as JSON file
        trace_file = self.output_dir / f"{trace.user_id}_{trace.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(trace_file, 'w') as f:
            json.dump(trace.to_dict(), f, indent=2, default=str)
        
        # Also save to a consolidated log
        log_file = self.output_dir / "traces_log.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(trace.to_dict(), default=str) + '\n')
    
    def get_traces_for_user(self, user_id: str) -> List[DecisionTrace]:
        """Get all traces for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of decision traces
        """
        traces = []
        log_file = self.output_dir / "traces_log.jsonl"
        
        if not log_file.exists():
            return traces
        
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('user_id') == user_id:
                            traces.append(DecisionTrace.from_dict(data))
                    except json.JSONDecodeError:
                        continue
        
        # Sort by timestamp (newest first)
        traces.sort(key=lambda x: x.timestamp, reverse=True)
        return traces




