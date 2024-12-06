import random
from typing import List, Tuple
from models.subject import Subject
from models.lecturer import Lecturer, LecturerConstraints
from models.group import Group
from models.classroom import Classroom

class DataGenerator:
    """Generates random test data for the scheduling system."""
    
    def __init__(self, seed: int = None):
        """Initialize the generator with an optional seed."""
        if seed is not None:
            random.seed(seed)
    
    def generate_subjects(self, count: int, hours_range: Tuple[int, int] = (2, 6)) -> List[Subject]:
        """Generate a list of random subjects."""
        subjects = []
        for i in range(count):
            total_hours = random.randint(*hours_range)
            lecture_hours = random.randint(1, total_hours)
            practical_hours = total_hours - lecture_hours
            
            subject = Subject(
                subject_id=f"SUBJ{i+1:03d}",
                name=f"Subject {i+1}",
                lecture_hours=lecture_hours,
                practical_hours=practical_hours,
                requires_subgroups=random.random() < 0.3
            )
            subjects.append(subject)
        return subjects
    
    def generate_lecturers(self, count: int, subjects: List[Subject]) -> List[Lecturer]:
        """Generate a list of random lecturers."""
        lecturers = []
        for i in range(count):
            lecturer = Lecturer(
                lecturer_id=f"LECT{i+1:03d}",
                name=f"Lecturer {i+1}"
            )
            
            # Randomly assign subjects to lecturer
            subject_count = random.randint(1, len(subjects))
            for subject in random.sample(subjects, subject_count):
                constraints = LecturerConstraints(
                    can_lecture=random.random() < 0.7,
                    can_practice=random.random() < 0.8,
                    max_hours_per_week=random.randint(10, 25)
                )
                lecturer.add_subject_constraint(subject.subject_id, constraints)
            
            lecturers.append(lecturer)
        return lecturers
    
    def generate_groups(self, count: int, subjects: List[Subject], 
                       size_range: Tuple[int, int] = (15, 30)) -> List[Group]:
        """Generate a list of random groups."""
        groups = []
        for i in range(count):
            student_count = random.randint(*size_range)
            group = Group(
                group_id=f"GRP{i+1:03d}",
                name=f"Group {i+1}",
                student_count=student_count
            )
            
            # Randomly assign subjects to group
            subject_count = random.randint(len(subjects) // 2, len(subjects))
            for subject in random.sample(subjects, subject_count):
                group.add_subject(subject)
            
            # Create subgroups for some groups
            if random.random() < 0.5:
                group.create_subgroups(random.randint(2, 3))
            
            groups.append(group)
        return groups
    
    def generate_classrooms(self, count: int, 
                          capacity_range: Tuple[int, int] = (20, 100)) -> List[Classroom]:
        """Generate a list of random classrooms."""
        classrooms = []
        buildings = ['A', 'B', 'C']
        
        for i in range(count):
            classroom = Classroom(
                classroom_id=f"ROOM{i+1:03d}",
                name=f"Room {i+1}",
                capacity=random.randint(*capacity_range),
                is_lab=random.random() < 0.3,
                building=random.choice(buildings),
                floor=random.randint(1, 5)
            )
            classrooms.append(classroom)
        return classrooms 