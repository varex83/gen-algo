from dataclasses import dataclass
from typing import Dict, List, Set
from models.schedule import Schedule, TimeSlot, ScheduleEntry
from models.lecturer import Lecturer
from models.group import Group

@dataclass
class ConstraintViolation:
    """Represents a constraint violation in the schedule."""
    constraint_type: str
    description: str
    severity: float  # 0.0 to 1.0, where 1.0 is most severe

class ScheduleConstraints:
    """Handles schedule constraints and quality metrics."""
    
    @staticmethod
    def check_lecturer_hours(schedule: Schedule, lecturer: Lecturer) -> List[ConstraintViolation]:
        """Check if lecturer's teaching hours are within limits."""
        violations = []
        slots = schedule.get_lecturer_slots(lecturer)
        
        # Check weekly hours
        weekly_hours = len(slots) * 1.5  # Each slot is 1.5 hours
        for subject_id, constraints in lecturer.subject_constraints.items():
            if weekly_hours > constraints.max_hours_per_week:
                violations.append(
                    ConstraintViolation(
                        constraint_type="lecturer_hours",
                        description=f"Lecturer {lecturer.name} exceeds maximum weekly hours "
                                  f"({weekly_hours} > {constraints.max_hours_per_week})",
                        severity=0.5
                    )
                )
        
        return violations
    
    @staticmethod
    def check_daily_load(schedule: Schedule, group: Group) -> List[ConstraintViolation]:
        """Check if daily class load is reasonable."""
        violations = []
        slots_by_day: Dict[int, List[TimeSlot]] = {}
        
        # Group slots by day
        for slot in schedule.get_group_slots(group):
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = []
            slots_by_day[slot.day].append(slot)
        
        # Check each day's load
        for day, slots in slots_by_day.items():
            daily_hours = len(slots) * 1.5
            if daily_hours > 6.0:  # More than 4 periods (6 hours) per day
                violations.append(
                    ConstraintViolation(
                        constraint_type="daily_load",
                        description=f"Group {group.name} has too many classes on day {day} "
                                  f"({daily_hours} hours)",
                        severity=0.3
                    )
                )
        
        return violations
    
    @staticmethod
    def check_room_suitability(schedule: Schedule) -> List[ConstraintViolation]:
        """Check if rooms are suitable for their assigned classes."""
        violations = []
        
        for slot, entries in schedule.entries.items():
            for entry in entries:
                # Check if labs are conducted in lab rooms when required
                if not entry.is_lecture and entry.subject.requires_subgroups and not entry.classroom.is_lab:
                    violations.append(
                        ConstraintViolation(
                            constraint_type="room_suitability",
                            description=f"Practical class for {entry.subject.name} scheduled in "
                                      f"non-lab room {entry.classroom.name}",
                            severity=0.4
                        )
                    )
        
        return violations
    
    @staticmethod
    def check_schedule_gaps(schedule: Schedule, group: Group) -> List[ConstraintViolation]:
        """Check for undesirable gaps in the schedule."""
        violations = []
        slots_by_day: Dict[int, Set[int]] = {}
        
        # Group slots by day
        for slot in schedule.get_group_slots(group):
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = set()
            slots_by_day[slot.day].add(slot.period)
        
        # Check for gaps in each day's schedule
        for day, periods in slots_by_day.items():
            if periods:  # If there are classes on this day
                min_period = min(periods)
                max_period = max(periods)
                gaps = max_period - min_period + 1 - len(periods)
                
                if gaps > 0:
                    violations.append(
                        ConstraintViolation(
                            constraint_type="schedule_gaps",
                            description=f"Group {group.name} has {gaps} gap(s) on day {day}",
                            severity=0.2 * gaps  # Severity increases with number of gaps
                        )
                    )
        
        return violations
    
    @staticmethod
    def check_subject_distribution(schedule: Schedule, group: Group) -> List[ConstraintViolation]:
        """Check if subjects are well-distributed throughout the week."""
        violations = []
        subject_slots: Dict[str, List[TimeSlot]] = {}
        
        # Group slots by subject
        for slot, entries in schedule.entries.items():
            for entry in entries:
                if group in entry.groups:
                    subject_id = entry.subject.subject_id
                    if subject_id not in subject_slots:
                        subject_slots[subject_id] = []
                    subject_slots[subject_id].append(slot)
        
        # Check distribution of each subject
        for subject_id, slots in subject_slots.items():
            if len(slots) > 1:
                # Check if all classes of the same subject are on the same day
                days = {slot.day for slot in slots}
                if len(days) == 1:
                    violations.append(
                        ConstraintViolation(
                            constraint_type="subject_distribution",
                            description=f"All classes of subject {subject_id} for group {group.name} "
                                      f"are on the same day",
                            severity=0.3
                        )
                    )
        
        return violations
    
    @staticmethod
    def calculate_quality_score(schedule: Schedule) -> float:
        """Calculate overall schedule quality score."""
        if not schedule.validate_hard_constraints():
            return 0.0
        
        base_score = 100.0
        violations: List[ConstraintViolation] = []
        
        # Check all constraints for all groups and lecturers
        for slot, entries in schedule.entries.items():
            for entry in entries:
                # Check lecturer constraints
                violations.extend(
                    ScheduleConstraints.check_lecturer_hours(schedule, entry.lecturer)
                )
                
                # Check group constraints
                for group in entry.groups:
                    violations.extend(ScheduleConstraints.check_daily_load(schedule, group))
                    violations.extend(ScheduleConstraints.check_schedule_gaps(schedule, group))
                    violations.extend(ScheduleConstraints.check_subject_distribution(schedule, group))
        
        # Check room suitability
        violations.extend(ScheduleConstraints.check_room_suitability(schedule))
        
        # Calculate penalty based on violations
        total_penalty = sum(violation.severity for violation in violations)
        
        return max(0.0, base_score - total_penalty) 