import argparse
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from generators.mock_data import generate_mock_data
from algorithms.genetic import GeneticScheduler
from utils.formatter import (
    format_schedule_table,
    format_violations,
    format_quality_score,
    format_schedule_summary,
    print_header
)
from models.schedule import Schedule, TimeSlot
from models.subject import Subject
from models.lecturer import Lecturer, LecturerConstraints
from models.group import Group
from models.classroom import Classroom
from rich.console import Console

console = Console()

def load_data_from_csv(input_dir: str) -> Tuple[List[Subject], List[Lecturer], List[Group], List[Classroom]]:
    """Load data from CSV files in the input directory.
    
    Expected files:
    - subjects.csv: subject_id,name,lecture_hours,practical_hours,requires_subgroups
    - lecturers.csv: lecturer_id,name,subjects,can_lecture,can_practice,max_hours
    - groups.csv: group_id,name,student_count,subjects,subgroups
    - classrooms.csv: classroom_id,name,capacity,is_lab,building,floor
    """
    input_path = Path(input_dir)
    
    # Load subjects
    subjects: Dict[str, Subject] = {}
    with open(input_path / "subjects.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject = Subject(
                subject_id=row["subject_id"],
                name=row["name"],
                lecture_hours=int(row["lecture_hours"]),
                practical_hours=int(row["practical_hours"]),
                requires_subgroups=row["requires_subgroups"].lower() == "true"
            )
            subjects[subject.subject_id] = subject
    
    # Load lecturers
    lecturers: List[Lecturer] = []
    with open(input_path / "lecturers.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lecturer = Lecturer(
                lecturer_id=row["lecturer_id"],
                name=row["name"]
            )
            
            # Parse subject constraints
            subject_list = row["subjects"].split(";")
            can_lecture = row["can_lecture"].split(";")
            can_practice = row["can_practice"].split(";")
            max_hours = row["max_hours"].split(";")
            
            for i, subject_id in enumerate(subject_list):
                if subject_id in subjects:
                    constraints = LecturerConstraints(
                        can_lecture=can_lecture[i].lower() == "true",
                        can_practice=can_practice[i].lower() == "true",
                        max_hours_per_week=int(max_hours[i])
                    )
                    lecturer.add_subject_constraint(subject_id, constraints)
            
            lecturers.append(lecturer)
    
    # Load groups
    groups: List[Group] = []
    with open(input_path / "groups.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            group = Group(
                group_id=row["group_id"],
                name=row["name"],
                student_count=int(row["student_count"])
            )
            
            # Add subjects
            subject_list = row["subjects"].split(";")
            for subject_id in subject_list:
                if subject_id in subjects:
                    group.add_subject(subjects[subject_id])
            
            # Create subgroups if specified
            if row["subgroups"]:
                group.create_subgroups(int(row["subgroups"]))
            
            groups.append(group)
    
    # Load classrooms
    classrooms: List[Classroom] = []
    with open(input_path / "classrooms.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            classroom = Classroom(
                classroom_id=row["classroom_id"],
                name=row["name"],
                capacity=int(row["capacity"]),
                is_lab=row["is_lab"].lower() == "true",
                building=row["building"],
                floor=int(row["floor"]) if row["floor"] else None
            )
            classrooms.append(classroom)
    
    return list(subjects.values()), lecturers, groups, classrooms

def save_schedule_to_csv(schedule: Schedule, groups: List, output_dir: str) -> None:
    """Save schedule to CSV files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / timestamp
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save main schedule
    with open(output_path / "schedule.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Day", "Period", "Subject", "Type", "Lecturer", 
            "Groups", "Classroom", "Is Lab"
        ])
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for slot, entries in sorted(schedule.entries.items(), key=lambda x: (x[0].day, x[0].period)):
            for entry in entries:
                writer.writerow([
                    days[slot.day],
                    f"Period {slot.period + 1}",
                    entry.subject.name,
                    "Lecture" if entry.is_lecture else "Practical",
                    entry.lecturer.name,
                    ", ".join(g.name for g in entry.groups),
                    entry.classroom.name,
                    "Yes" if entry.classroom.is_lab else "No"
                ])
    
    # Save group schedules
    for group in groups:
        with open(output_path / f"schedule_{group.name}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time"] + days)
            
            for period in range(4):
                row = [f"Period {period + 1}"]
                for day in range(5):
                    slot = TimeSlot(day=day, period=period)
                    cell = ""
                    if slot in schedule.entries:
                        for entry in schedule.entries[slot]:
                            if group in entry.groups:
                                cell = (
                                    f"{entry.subject.name}\n"
                                    f"{entry.lecturer.name}\n"
                                    f"{entry.classroom.name}\n"
                                    f"({'Lecture' if entry.is_lecture else 'Practical'})"
                                )
                                break
                    row.append(cell)
                writer.writerow(row)
    
    # Save statistics
    with open(output_path / "statistics.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        total_slots = 20
        used_slots = len(schedule.entries)
        utilization = (used_slots / total_slots) * 100
        
        writer.writerow(["Total Time Slots", total_slots])
        writer.writerow(["Used Time Slots", used_slots])
        writer.writerow(["Schedule Utilization", f"{utilization:.1f}%"])

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="University Schedule Generator")
    
    # Data source arguments
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument(
        "--size",
        choices=["small", "medium"],
        default="small",
        help="Dataset size for mock data (default: small)"
    )
    data_group.add_argument(
        "--input-dir",
        type=str,
        help="Directory containing input CSV files (subjects.csv, lecturers.csv, groups.csv, classrooms.csv)"
    )
    
    # Algorithm parameters
    parser.add_argument(
        "--population",
        type=int,
        default=50,
        help="Population size for genetic algorithm (default: 50)"
    )
    
    parser.add_argument(
        "--generations",
        type=int,
        default=100,
        help="Number of generations to evolve (default: 100)"
    )
    
    parser.add_argument(
        "--mutation-rate",
        type=float,
        default=0.1,
        help="Mutation rate (default: 0.1)"
    )
    
    parser.add_argument(
        "--elite-size",
        type=int,
        default=5,
        help="Number of elite schedules to preserve (default: 5)"
    )
    
    parser.add_argument(
        "--tournament-size",
        type=int,
        default=3,
        help="Tournament size for selection (default: 3)"
    )
    
    parser.add_argument(
        "--crossover-rate",
        type=float,
        default=0.8,
        help="Crossover rate (default: 0.8)"
    )
    
    # Output options
    parser.add_argument(
        "--show-lecturer-schedules",
        action="store_true",
        help="Show lecturer schedules"
    )
    
    parser.add_argument(
        "--show-classroom-schedules",
        action="store_true",
        help="Show classroom schedules"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save output CSV files"
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    print_header("University Schedule Generator")
    
    # Generate or load data
    try:
        if args.input_dir:
            console.print(f"\n[cyan]Loading data from {args.input_dir}...[/]")
            subjects, lecturers, groups, classrooms = load_data_from_csv(args.input_dir)
            console.print("[green]Data loaded successfully![/]")
        else:
            console.print(f"\n[cyan]Generating {args.size} dataset...[/]")
            subjects, lecturers, groups, classrooms = generate_mock_data(args.size)
    except Exception as e:
        console.print(f"[red]Error loading data: {str(e)}[/]")
        return
    
    # Initialize genetic scheduler
    scheduler = GeneticScheduler(
        subjects=subjects,
        lecturers=lecturers,
        groups=groups,
        classrooms=classrooms,
        population_size=args.population,
        elite_size=args.elite_size,
        mutation_rate=args.mutation_rate,
        crossover_rate=args.crossover_rate,
        tournament_size=args.tournament_size
    )
    
    # Generate initial population
    console.print("\n[bold cyan]Generating initial population...[/]")
    with console.status("[bold green]Creating initial schedules...") as status:
        population = scheduler.generate_initial_population()
    
    # Run genetic algorithm
    console.print("\n[bold cyan]Running genetic algorithm...[/]")
    with console.status("[bold green]Evolving schedules...") as status:
        def progress_callback(gen: int, fitness: float):
            status.update(f"Generation {gen + 1}/{args.generations} - Best Fitness: {fitness:.2f}")
        
        best_schedule = scheduler.evolve(
            population=population,
            generations=args.generations,
            progress_callback=progress_callback
        )
    
    # Print schedule views
    format_schedule_table(
        best_schedule,
        groups,
        lecturers if args.show_lecturer_schedules else [],
        classrooms if args.show_classroom_schedules else []
    )
    
    # Print schedule summary
    print_header("\nSchedule Statistics")
    format_schedule_summary(best_schedule)
    
    # Print violations if any
    violations = scheduler.get_violations(best_schedule)
    if violations:
        print_header("\nConstraint Violations")
        format_violations(violations)
    
    # Print quality score
    quality_score = scheduler.evaluate_schedule(best_schedule)
    format_quality_score(quality_score)
    
    # Save output to CSV if requested
    if args.output_dir:
        try:
            console.print(f"\n[cyan]Saving results to {args.output_dir}...[/]")
            save_schedule_to_csv(best_schedule, groups, args.output_dir)
            console.print("[green]Results saved successfully![/]")
        except Exception as e:
            console.print(f"[red]Error saving results: {str(e)}[/]")

if __name__ == "__main__":
    main() 