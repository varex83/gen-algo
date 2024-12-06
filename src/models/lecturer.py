from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass(frozen=True)
class LecturerConstraints:
    """Represents constraints for a lecturer."""
    
    can_lecture: bool = True
    can_practice: bool = True
    max_hours_per_week: int = 20

@dataclass
class Lecturer:
    """Represents a lecturer in the schedule."""
    
    lecturer_id: str
    name: str
    subject_constraints: Dict[str, LecturerConstraints] = field(default_factory=dict)
    
    def can_teach_subject(self, subject_id: str, is_lecture: bool) -> bool:
        """Check if lecturer can teach a specific subject."""
        if subject_id not in self.subject_constraints:
            return False
        
        constraints = self.subject_constraints[subject_id]
        return constraints.can_lecture if is_lecture else constraints.can_practice
    
    def add_subject_constraint(self, subject_id: str, constraints: LecturerConstraints) -> None:
        """Add or update constraints for a subject."""
        self.subject_constraints[subject_id] = constraints
    
    def get_teachable_subjects(self) -> Set[str]:
        """Get all subjects that the lecturer can teach."""
        return set(self.subject_constraints.keys())
    
    def __hash__(self):
        return hash(self.lecturer_id)
    
    def __eq__(self, other):
        if not isinstance(other, Lecturer):
            return False
        return self.lecturer_id == other.lecturer_id 