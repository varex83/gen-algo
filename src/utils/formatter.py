from typing import List, Dict, Any
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from models.schedule import Schedule, TimeSlot, ScheduleEntry
from models.subject import Subject
from models.lecturer import Lecturer
from models.group import Group
from models.classroom import Classroom
from algorithms.constraints import ConstraintViolation

console = Console()

def print_header(text: str, style: str = "bold cyan") -> None:
    """Print a formatted header."""
    console.print(f"\n[{style}]{text}[/{style}]")
    console.print("=" * len(text))

def format_subjects_table(subjects: List[Subject]) -> None:
    """Print subjects in a formatted table."""
    table = Table(title="Subjects", show_header=True, header_style="bold magenta")
    table.add_column("Subject ID", style="dim")
    table.add_column("Name")
    table.add_column("Lecture Hours", justify="right")
    table.add_column("Practical Hours", justify="right")
    table.add_column("Requires Subgroups", justify="center")
    
    for subject in subjects:
        table.add_row(
            subject.subject_id,
            subject.name,
            str(subject.lecture_hours),
            str(subject.practical_hours),
            "✓" if subject.requires_subgroups else "✗"
        )
    
    console.print(table)

def format_lecturers_table(lecturers: List[Lecturer]) -> None:
    """Print lecturers in a formatted table."""
    table = Table(title="Lecturers", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Subjects", style="cyan")
    table.add_column("Max Hours/Week", justify="right")
    
    for lecturer in lecturers:
        subjects_info = []
        for subject_id, constraints in lecturer.subject_constraints.items():
            capabilities = []
            if constraints.can_lecture:
                capabilities.append("L")
            if constraints.can_practice:
                capabilities.append("P")
            subjects_info.append(f"{subject_id}({','.join(capabilities)})")
        
        table.add_row(
            lecturer.lecturer_id,
            lecturer.name,
            "\n".join(subjects_info),
            str(max(c.max_hours_per_week for c in lecturer.subject_constraints.values()))
        )
    
    console.print(table)

def format_groups_table(groups: List[Group]) -> None:
    """Print groups in a formatted table."""
    table = Table(title="Groups", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Students", justify="right")
    table.add_column("Subjects")
    table.add_column("Subgroups")
    
    for group in groups:
        subjects_str = ", ".join(s.name for s in group.subjects.values())
        subgroups_str = "\n".join(
            f"{sg.subgroup_id} ({sg.student_count} students)"
            for sg in group.subgroups
        ) if group.subgroups else "None"
        
        table.add_row(
            group.group_id,
            group.name,
            str(group.student_count),
            subjects_str,
            subgroups_str
        )
    
    console.print(table)

def format_classrooms_table(classrooms: List[Classroom]) -> None:
    """Print classrooms in a formatted table."""
    table = Table(title="Classrooms", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Capacity", justify="right")
    table.add_column("Type")
    table.add_column("Location")
    
    for classroom in classrooms:
        table.add_row(
            classroom.classroom_id,
            classroom.name,
            str(classroom.capacity),
            "Lab" if classroom.is_lab else "Lecture Hall",
            f"{classroom.building} Building, Floor {classroom.floor}"
        )
    
    console.print(table)

def format_schedule_by_group(schedule: Schedule, group: Group) -> Table:
    """Format schedule for a specific group."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1st Period', '2nd Period', '3rd Period', '4th Period']
    
    table = Table(
        title=f"Schedule for {group.name}",
        show_header=True,
        header_style="bold magenta",
        title_style="bold blue"
    )
    
    table.add_column("Time")
    for day in days:
        table.add_column(day)
    
    for period_idx, period in enumerate(periods):
        row = [period]
        for day_idx in range(len(days)):
            time_slot = TimeSlot(day=day_idx, period=period_idx)
            cell_content = ""
            
            if time_slot in schedule.entries:
                entries = [
                    entry for entry in schedule.entries[time_slot]
                    if group in entry.groups
                ]
                if entries:
                    entry = entries[0]
                    cell_content = (
                        f"[green]{entry.subject.name}[/green]\n"
                        f"[blue]{entry.lecturer.name}[/blue]\n"
                        f"[yellow]{entry.classroom.name}[/yellow]\n"
                        f"({'Lecture' if entry.is_lecture else 'Practical'})"
                    )
                else:
                    cell_content = "[dim]No class[/dim]"
            else:
                cell_content = "[dim]No class[/dim]"
            
            row.append(cell_content)
        
        table.add_row(*row)
    
    return table

def format_schedule_by_lecturer(schedule: Schedule, lecturer: Lecturer) -> Table:
    """Format schedule for a specific lecturer."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1st Period', '2nd Period', '3rd Period', '4th Period']
    
    table = Table(
        title=f"Schedule for {lecturer.name}",
        show_header=True,
        header_style="bold magenta",
        title_style="bold blue"
    )
    
    table.add_column("Time")
    for day in days:
        table.add_column(day)
    
    for period_idx, period in enumerate(periods):
        row = [period]
        for day_idx in range(len(days)):
            time_slot = TimeSlot(day=day_idx, period=period_idx)
            cell_content = ""
            
            if time_slot in schedule.entries:
                entries = [
                    entry for entry in schedule.entries[time_slot]
                    if entry.lecturer == lecturer
                ]
                if entries:
                    entry = entries[0]
                    groups_str = ", ".join(g.name for g in entry.groups)
                    cell_content = (
                        f"[green]{entry.subject.name}[/green]\n"
                        f"[blue]{groups_str}[/blue]\n"
                        f"[yellow]{entry.classroom.name}[/yellow]\n"
                        f"({'Lecture' if entry.is_lecture else 'Practical'})"
                    )
                else:
                    cell_content = "[dim]No class[/dim]"
            else:
                cell_content = "[dim]No class[/dim]"
            
            row.append(cell_content)
        
        table.add_row(*row)
    
    return table

def format_schedule_by_classroom(schedule: Schedule, classroom: Classroom) -> Table:
    """Format schedule for a specific classroom."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1st Period', '2nd Period', '3rd Period', '4th Period']
    
    table = Table(
        title=f"Schedule for {classroom.name}",
        show_header=True,
        header_style="bold magenta",
        title_style="bold blue"
    )
    
    table.add_column("Time")
    for day in days:
        table.add_column(day)
    
    for period_idx, period in enumerate(periods):
        row = [period]
        for day_idx in range(len(days)):
            time_slot = TimeSlot(day=day_idx, period=period_idx)
            cell_content = ""
            
            if time_slot in schedule.entries:
                entries = [
                    entry for entry in schedule.entries[time_slot]
                    if entry.classroom == classroom
                ]
                if entries:
                    entry = entries[0]
                    groups_str = ", ".join(g.name for g in entry.groups)
                    cell_content = (
                        f"[green]{entry.subject.name}[/green]\n"
                        f"[blue]{entry.lecturer.name}[/blue]\n"
                        f"[yellow]{groups_str}[/yellow]\n"
                        f"({'Lecture' if entry.is_lecture else 'Practical'})"
                    )
                else:
                    cell_content = "[dim]No class[/dim]"
            else:
                cell_content = "[dim]No class[/dim]"
            
            row.append(cell_content)
        
        table.add_row(*row)
    
    return table

def format_schedule_table(schedule: Schedule, groups: List[Group], lecturers: List[Lecturer], classrooms: List[Classroom]) -> None:
    """Print schedule with multiple views."""
    # Print group schedules
    print_header("Group Schedules")
    for group in groups:
        console.print(format_schedule_by_group(schedule, group))
        console.print()
    
    # Print lecturer schedules
    if console.input("\n[yellow]Show lecturer schedules? (y/n): [/]").lower() == 'y':
        print_header("Lecturer Schedules")
        for lecturer in lecturers:
            console.print(format_schedule_by_lecturer(schedule, lecturer))
            console.print()
    
    # Print classroom schedules
    if console.input("\n[yellow]Show classroom schedules? (y/n): [/]").lower() == 'y':
        print_header("Classroom Schedules")
        for classroom in classrooms:
            console.print(format_schedule_by_classroom(schedule, classroom))
            console.print()

def format_schedule_summary(schedule: Schedule) -> None:
    """Print a summary of the schedule."""
    total_slots = 20  # 4 periods * 5 days
    used_slots = len(schedule.entries)
    utilization = (used_slots / total_slots) * 100
    
    table = Table(title="Schedule Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Time Slots", str(total_slots))
    table.add_row("Used Time Slots", str(used_slots))
    table.add_row("Schedule Utilization", f"{utilization:.1f}%")
    
    console.print(table)

def format_violations(violations: List[ConstraintViolation]) -> None:
    """Print constraint violations in a formatted table."""
    if not violations:
        console.print("[green]No constraint violations found![/green]")
        return
    
    # Group violations by type
    violations_by_type: Dict[str, List[ConstraintViolation]] = {}
    for violation in violations:
        if violation.constraint_type not in violations_by_type:
            violations_by_type[violation.constraint_type] = []
        violations_by_type[violation.constraint_type].append(violation)
    
    # Create a table for each type
    for violation_type, type_violations in violations_by_type.items():
        table = Table(
            title=f"{violation_type} Violations",
            show_header=True,
            header_style="bold red"
        )
        table.add_column("Description")
        table.add_column("Severity", justify="right")
        
        for violation in type_violations:
            table.add_row(
                violation.description,
                f"{violation.severity:.2f}"
            )
        
        console.print(table)
        console.print()

def format_quality_score(score: float) -> None:
    """Print quality score with color-coded formatting and gauge."""
    color = "green" if score >= 90 else "yellow" if score >= 70 else "red"
    
    # Create a visual gauge
    gauge_width = 50
    filled = int((score / 100) * gauge_width)
    gauge = "█" * filled + "░" * (gauge_width - filled)
    
    text = Text()
    text.append("\nQuality Score: ", style="bold")
    text.append(f"{score:.2f}", style=f"bold {color}")
    text.append("\n\n")
    text.append(gauge, style=color)
    text.append(f" {score:.1f}%", style=f"bold {color}")
    
    panel = Panel(
        text,
        title="Schedule Quality",
        border_style=color
    )
    console.print(panel) 