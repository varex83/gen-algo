from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Subject:
    """Represents a subject in the curriculum."""
    
    subject_id: str
    name: str
    lecture_hours: int
    practical_hours: int
    requires_subgroups: bool = False
    
    @property
    def total_hours(self) -> int:
        """Total hours per semester for this subject."""
        return self.lecture_hours + self.practical_hours
    
    def validate(self) -> bool:
        """Validate subject data."""
        if self.lecture_hours < 0 or self.practical_hours < 0:
            return False
        if self.total_hours == 0:
            return False
        return True
    
    def __hash__(self):
        return hash(self.subject_id)
    
    def __eq__(self, other):
        if not isinstance(other, Subject):
            return False
        return self.subject_id == other.subject_id 