from dataclasses import dataclass, field
from typing import List, Dict
from .subject import Subject

@dataclass(frozen=True)
class Subgroup:
    """Represents a subgroup of students."""
    
    subgroup_id: str
    student_count: int
    parent_group_id: str
    
    def __hash__(self):
        return hash(self.subgroup_id)
    
    def __eq__(self, other):
        if not isinstance(other, Subgroup):
            return False
        return self.subgroup_id == other.subgroup_id

@dataclass
class Group:
    """Represents a student group."""
    
    group_id: str
    name: str
    student_count: int
    subjects: Dict[str, Subject] = field(default_factory=dict)
    subgroups: List[Subgroup] = field(default_factory=list)
    
    def add_subject(self, subject: Subject) -> None:
        """Add a subject to the group's curriculum."""
        self.subjects[subject.subject_id] = subject
    
    def create_subgroups(self, count: int) -> None:
        """Create subgroups with approximately equal division."""
        if count <= 0:
            return
        
        base_size = self.student_count // count
        remainder = self.student_count % count
        
        self.subgroups.clear()
        for i in range(count):
            size = base_size + (1 if i < remainder else 0)
            subgroup = Subgroup(
                subgroup_id=f"{self.group_id}/sg{i+1}",
                student_count=size,
                parent_group_id=self.group_id
            )
            self.subgroups.append(subgroup)
    
    def get_subject_hours(self, subject_id: str) -> tuple[int, int]:
        """Get lecture and practical hours for a subject."""
        if subject_id not in self.subjects:
            return (0, 0)
        subject = self.subjects[subject_id]
        return (subject.lecture_hours, subject.practical_hours)
    
    def __hash__(self):
        return hash(self.group_id)
    
    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self.group_id == other.group_id