from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from .subject import Subject
from .lecturer import Lecturer
from .group import Group, Subgroup
from .classroom import Classroom

@dataclass
class TimeSlot:
    """Represents a time slot in the schedule."""
    day: int  # 0-4 (Monday to Friday)
    period: int  # 0-3 (four periods per day)
    
    def __hash__(self):
        return hash((self.day, self.period))

@dataclass
class ScheduleEntry:
    """Represents a single entry in the schedule."""
    subject: Subject
    lecturer: Lecturer
    classroom: Classroom
    groups: List[Group]
    subgroups: Optional[List[Subgroup]] = None
    is_lecture: bool = True

@dataclass
class Schedule:
    """Represents a complete schedule."""
    entries: Dict[TimeSlot, List[ScheduleEntry]] = field(default_factory=dict)
    
    def add_entry(self, time_slot: TimeSlot, entry: ScheduleEntry) -> None:
        """Add a schedule entry to a time slot."""
        if time_slot not in self.entries:
            self.entries[time_slot] = []
        self.entries[time_slot].append(entry)
    
    def get_lecturer_slots(self, lecturer: Lecturer) -> Set[TimeSlot]:
        """Get all time slots where a lecturer is teaching."""
        slots = set()
        for slot, entries in self.entries.items():
            if any(entry.lecturer == lecturer for entry in entries):
                slots.add(slot)
        return slots
    
    def get_group_slots(self, group: Group) -> Set[TimeSlot]:
        """Get all time slots where a group has classes."""
        slots = set()
        for slot, entries in self.entries.items():
            if any(group in entry.groups for entry in entries):
                slots.add(slot)
        return slots
    
    def get_classroom_slots(self, classroom: Classroom) -> Set[TimeSlot]:
        """Get all time slots where a classroom is in use."""
        slots = set()
        for slot, entries in self.entries.items():
            if any(entry.classroom == classroom for entry in entries):
                slots.add(slot)
        return slots
    
    def validate_hard_constraints(self) -> bool:
        """Validate that all hard constraints are met."""
        # Check each time slot
        for slot, entries in self.entries.items():
            # Track resources in use for this slot
            lecturers_in_use = set()
            groups_in_use = set()
            classrooms_in_use = set()
            
            for entry in entries:
                # Check lecturer conflicts
                if entry.lecturer in lecturers_in_use:
                    return False
                lecturers_in_use.add(entry.lecturer)
                
                # Check group conflicts
                for group in entry.groups:
                    if group in groups_in_use:
                        return False
                    groups_in_use.add(group)
                
                # Check classroom conflicts
                if entry.classroom in classrooms_in_use:
                    # Only allow sharing if it's the same lecturer and subject
                    sharing_allowed = any(
                        e.lecturer == entry.lecturer and 
                        e.subject == entry.subject and
                        e.is_lecture
                        for e in entries if e.classroom == entry.classroom
                    )
                    if not sharing_allowed:
                        return False
                classrooms_in_use.add(entry.classroom)
                
                # Check classroom capacity
                total_students = sum(g.student_count for g in entry.groups)
                if not entry.classroom.can_accommodate(total_students):
                    return False
        
        return True 