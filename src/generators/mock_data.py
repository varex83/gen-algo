from typing import List, Tuple
from models.subject import Subject
from models.lecturer import Lecturer, LecturerConstraints
from models.group import Group
from models.classroom import Classroom
from generators.data_generator import DataGenerator

def generate_mock_data(size: str = 'small') -> Tuple[List[Subject], List[Lecturer], List[Group], List[Classroom]]:
    """Generate mock data for testing the scheduler.
    
    Args:
        size: Either 'small' or 'medium' dataset
        
    Returns:
        Tuple containing lists of subjects, lecturers, groups, and classrooms
    """
    generator = DataGenerator(seed=42)  # Use fixed seed for reproducibility
    
    if size == 'small':
        # Small dataset
        subjects = generator.generate_subjects(count=5, hours_range=(2, 4))
        lecturers = generator.generate_lecturers(count=3, subjects=subjects)
        groups = generator.generate_groups(
            count=2,
            subjects=subjects,
            size_range=(15, 25)
        )
        classrooms = generator.generate_classrooms(
            count=4,
            capacity_range=(20, 40)
        )
    else:
        # Medium dataset
        subjects = generator.generate_subjects(count=10, hours_range=(2, 6))
        lecturers = generator.generate_lecturers(count=6, subjects=subjects)
        groups = generator.generate_groups(
            count=4,
            subjects=subjects,
            size_range=(20, 35)
        )
        classrooms = generator.generate_classrooms(
            count=8,
            capacity_range=(25, 60)
        )
    
    return subjects, lecturers, groups, classrooms