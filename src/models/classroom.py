from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Classroom:
    """Represents a classroom in the schedule."""
    
    classroom_id: str
    name: str
    capacity: int
    is_lab: bool = False
    building: Optional[str] = None
    floor: Optional[int] = None
    
    def can_accommodate(self, student_count: int) -> bool:
        """Check if the classroom can accommodate the given number of students."""
        return self.capacity >= student_count
    
    def validate(self) -> bool:
        """Validate classroom data."""
        if self.capacity <= 0:
            return False
        if self.floor is not None and self.floor < 0:
            return False
        return True
    
    def __hash__(self):
        return hash(self.classroom_id) 