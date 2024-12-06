from generators.data_generator import DataGenerator
from algorithms.genetic import GeneticScheduler
from algorithms.constraints import ScheduleConstraints
from models.schedule import TimeSlot

def print_schedule(schedule):
    """Print a schedule in a readable format."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1st Period', '2nd Period', '3rd Period', '4th Period']
    
    print("\nGenerated Schedule:")
    print("=" * 80)
    
    for day_idx, day in enumerate(days):
        print(f"\n{day}:")
        print("-" * 40)
        
        for period_idx, period in enumerate(periods):
            time_slot = TimeSlot(day=day_idx, period=period_idx)
            
            print(f"\n{period}:")
            if time_slot in schedule.entries:
                for entry in schedule.entries[time_slot]:
                    groups_str = ", ".join(g.name for g in entry.groups)
                    print(f"  {entry.subject.name} ({'Lecture' if entry.is_lecture else 'Practical'})")
                    print(f"  Groups: {groups_str}")
                    print(f"  Lecturer: {entry.lecturer.name}")
                    print(f"  Classroom: {entry.classroom.name}")
                    print()
            else:
                print("  [No classes scheduled]")

def print_schedule_analysis(schedule, groups, lecturers):
    """Print analysis of the schedule including constraint violations."""
    print("\nSchedule Analysis:")
    print("=" * 80)
    
    # Check all constraints
    all_violations = []
    
    # Check lecturer constraints
    print("\nLecturer Constraints:")
    print("-" * 40)
    for lecturer in lecturers:
        violations = ScheduleConstraints.check_lecturer_hours(schedule, lecturer)
        if violations:
            print(f"\n{lecturer.name}:")
            for violation in violations:
                print(f"- {violation.description}")
        all_violations.extend(violations)
    
    # Check group constraints
    print("\nGroup Constraints:")
    print("-" * 40)
    for group in groups:
        violations = []
        violations.extend(ScheduleConstraints.check_daily_load(schedule, group))
        violations.extend(ScheduleConstraints.check_schedule_gaps(schedule, group))
        violations.extend(ScheduleConstraints.check_subject_distribution(schedule, group))
        
        if violations:
            print(f"\n{group.name}:")
            for violation in violations:
                print(f"- {violation.description}")
        all_violations.extend(violations)
    
    # Check room constraints
    print("\nRoom Constraints:")
    print("-" * 40)
    violations = ScheduleConstraints.check_room_suitability(schedule)
    if violations:
        for violation in violations:
            print(f"- {violation.description}")
    all_violations.extend(violations)
    
    # Print overall quality score
    quality_score = ScheduleConstraints.calculate_quality_score(schedule)
    print(f"\nOverall Quality Score: {quality_score:.2f}")
    print(f"Total Violations: {len(all_violations)}")

def main():
    """Test the schedule generation functionality."""
    # Initialize the generator with a seed for reproducibility
    generator = DataGenerator(seed=42)
    
    # Generate test data
    subjects = generator.generate_subjects(count=5)
    lecturers = generator.generate_lecturers(count=10, subjects=subjects)
    groups = generator.generate_groups(count=3, subjects=subjects)
    classrooms = generator.generate_classrooms(count=7)
    
    # Print generated data
    print("\nGenerated Subjects:")
    for subject in subjects:
        print(f"- {subject.name}: {subject.lecture_hours}L + {subject.practical_hours}P hours")
    
    print("\nGenerated Lecturers:")
    for lecturer in lecturers:
        subjects = lecturer.get_teachable_subjects()
        print(f"- {lecturer.name} can teach {len(subjects)} subjects")
    
    print("\nGenerated Groups:")
    for group in groups:
        print(f"- {group.name}: {group.student_count} students, {len(group.subjects)} subjects")
        if group.subgroups:
            print(f"  Divided into {len(group.subgroups)} subgroups")
    
    print("\nGenerated Classrooms:")
    for classroom in classrooms:
        print(f"- {classroom.name}: capacity={classroom.capacity}, {'lab' if classroom.is_lab else 'lecture room'}")
    
    # Create and run the genetic scheduler
    scheduler = GeneticScheduler(
        subjects=subjects,
        lecturers=lecturers,
        groups=groups,
        classrooms=classrooms,
        population_size=50,  # Smaller population for testing
        elite_size=5,
        mutation_rate=0.1,
        crossover_rate=0.8,
        tournament_size=3
    )
    
    print("\nGenerating initial population...")
    population = scheduler.generate_initial_population()
    
    print("\nEvolving schedules...")
    best_schedule = scheduler.evolve(population, generations=50)  # Fewer generations for testing
    
    # Print the best schedule and its analysis
    print_schedule(best_schedule)
    print_schedule_analysis(best_schedule, groups, lecturers)

if __name__ == "__main__":
    main() 