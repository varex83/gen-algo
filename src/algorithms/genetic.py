import random
from typing import List, Tuple, Optional, Dict, Set, Callable
from copy import deepcopy
from models.schedule import Schedule, TimeSlot, ScheduleEntry
from models.subject import Subject
from models.lecturer import Lecturer
from models.group import Group
from models.classroom import Classroom
from .constraints import ScheduleConstraints, ConstraintViolation

ProgressCallback = Callable[[int, float], None]

class GeneticScheduler:
    """Implements genetic algorithm for schedule generation."""
    
    def __init__(self, 
                 subjects: List[Subject],
                 lecturers: List[Lecturer],
                 groups: List[Group],
                 classrooms: List[Classroom],
                 population_size: int = 100,
                 elite_size: int = 10,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 tournament_size: int = 3):
        """Initialize the genetic scheduler."""
        self.subjects = subjects
        self.lecturers = lecturers
        self.groups = groups
        self.classrooms = classrooms
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        
        # Track best solutions
        self.best_fitness_history: List[float] = []
        self.best_schedule: Optional[Schedule] = None
        self.best_fitness: float = 0.0
    
    def get_violations(self, schedule: Schedule) -> List[ConstraintViolation]:
        """Get all constraint violations for a schedule."""
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
        
        return violations
    
    def evaluate_schedule(self, schedule: Schedule) -> float:
        """Evaluate the quality of a schedule."""
        return ScheduleConstraints.calculate_quality_score(schedule)
    
    def _tournament_select(self, population_fitness: List[Tuple[Schedule, float]]) -> Schedule:
        """Select a schedule using tournament selection."""
        tournament = random.sample(population_fitness, self.tournament_size)
        return max(tournament, key=lambda x: x[1])[0]
    
    def _crossover(self, parent1: Schedule, parent2: Schedule) -> Schedule:
        """Create a new schedule by combining two parent schedules."""
        child = Schedule()
        
        # Get all time slots from both parents
        all_slots = set(parent1.entries.keys()) | set(parent2.entries.keys())
        
        for slot in all_slots:
            # Randomly choose entries from either parent
            if slot in parent1.entries and slot in parent2.entries:
                entries = parent1.entries[slot] if random.random() < 0.5 else parent2.entries[slot]
            elif slot in parent1.entries:
                entries = parent1.entries[slot]
            else:
                entries = parent2.entries[slot]
            
            # Deep copy the entries to avoid reference issues
            child.entries[slot] = [deepcopy(entry) for entry in entries]
        
        return child
    
    def _mutate(self, schedule: Schedule) -> Schedule:
        """Apply mutation to a schedule."""
        mutated = deepcopy(schedule)
        
        # Get all entries
        entries = []
        for slot, slot_entries in mutated.entries.items():
            for entry in slot_entries:
                entries.append((slot, entry))
        
        if not entries:
            return mutated
        
        # Select a random entry to mutate
        old_slot, entry = random.choice(entries)
        mutated.entries[old_slot].remove(entry)
        if not mutated.entries[old_slot]:
            del mutated.entries[old_slot]
        
        # Try to reschedule the entry
        for _ in range(10):  # Try up to 10 times
            new_slot = TimeSlot(
                day=random.randint(0, 4),
                period=random.randint(0, 3)
            )
            
            # Check if the new slot is valid
            lecturer_slots = mutated.get_lecturer_slots(entry.lecturer)
            group_slots = set()
            for group in entry.groups:
                group_slots.update(mutated.get_group_slots(group))
            
            if new_slot not in lecturer_slots and new_slot not in group_slots:
                if new_slot not in mutated.entries:
                    mutated.entries[new_slot] = []
                mutated.entries[new_slot].append(entry)
                break
        
        return mutated
    
    def generate_initial_population(self) -> List[Schedule]:
        """Generate initial population of schedules."""
        population = []
        attempts = 0
        max_attempts = self.population_size * 10
        
        while len(population) < self.population_size and attempts < max_attempts:
            schedule = self._generate_random_schedule()
            if schedule.validate_hard_constraints():
                population.append(schedule)
            attempts += 1
        
        if len(population) < self.population_size:
            print(f"Warning: Could only generate {len(population)} valid schedules")
        
        return population
    
    def _generate_random_schedule(self) -> Schedule:
        """Generate a random valid schedule."""
        schedule = Schedule()
        
        # Create a list of all required classes
        required_classes = []
        for group in self.groups:
            for subject_id, subject in group.subjects.items():
                # Add lectures
                for _ in range(subject.lecture_hours):
                    required_classes.append((group, subject, True))
                
                # Add practicals
                for _ in range(subject.practical_hours):
                    required_classes.append((group, subject, False))
        
        # Shuffle the classes
        random.shuffle(required_classes)
        
        # Try to schedule each class
        for group, subject, is_lecture in required_classes:
            self._schedule_class(schedule, group, subject, is_lecture)
        
        return schedule
    
    def _schedule_class(self, 
                       schedule: Schedule,
                       group: Group,
                       subject: Subject,
                       is_lecture: bool,
                       max_attempts: int = 20) -> bool:
        """Schedule a single class with multiple attempts."""
        # Find suitable lecturers
        suitable_lecturers = [
            l for l in self.lecturers
            if l.can_teach_subject(subject.subject_id, is_lecture)
        ]
        if not suitable_lecturers:
            return False
        
        # Try different combinations
        for _ in range(max_attempts):
            lecturer = random.choice(suitable_lecturers)
            time_slot = self._find_available_slot(schedule, group, lecturer)
            if not time_slot:
                continue
            
            classroom = self._find_suitable_classroom(
                schedule, time_slot, group.student_count, is_lecture and subject.requires_subgroups
            )
            if not classroom:
                continue
            
            # Create and add schedule entry
            entry = ScheduleEntry(
                subject=subject,
                lecturer=lecturer,
                classroom=classroom,
                groups=[group],
                is_lecture=is_lecture
            )
            
            if time_slot not in schedule.entries:
                schedule.entries[time_slot] = []
            schedule.entries[time_slot].append(entry)
            return True
        
        return False
    
    def _find_available_slot(self,
                           schedule: Schedule,
                           group: Group,
                           lecturer: Lecturer) -> Optional[TimeSlot]:
        """Find an available time slot for a class."""
        # Get occupied slots
        group_slots = schedule.get_group_slots(group)
        lecturer_slots = schedule.get_lecturer_slots(lecturer)
        occupied_slots = group_slots | lecturer_slots
        
        # Get slots by day for the group
        slots_by_day: Dict[int, Set[int]] = {}
        for slot in group_slots:
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = set()
            slots_by_day[slot.day].add(slot.period)
        
        # Try to find a slot that minimizes gaps
        available_slots = []
        for day in range(5):
            day_slots = slots_by_day.get(day, set())
            for period in range(4):
                slot = TimeSlot(day=day, period=period)
                if slot not in occupied_slots:
                    # Calculate gap penalty
                    if not day_slots:
                        gap_penalty = 0
                    else:
                        min_period = min(day_slots)
                        max_period = max(day_slots)
                        if period < min_period:
                            gap_penalty = min_period - period
                        elif period > max_period:
                            gap_penalty = period - max_period
                        else:
                            gap_penalty = 1
                    available_slots.append((slot, gap_penalty))
        
        if not available_slots:
            return None
        
        # Sort by gap penalty and randomly choose from the best options
        available_slots.sort(key=lambda x: x[1])
        best_penalty = available_slots[0][1]
        best_slots = [slot for slot, penalty in available_slots if penalty == best_penalty]
        return random.choice(best_slots)
    
    def _find_suitable_classroom(self,
                               schedule: Schedule,
                               time_slot: TimeSlot,
                               student_count: int,
                               requires_lab: bool) -> Optional[Classroom]:
        """Find a suitable classroom for a class."""
        # Get occupied classrooms
        occupied_classrooms = set()
        if time_slot in schedule.entries:
            occupied_classrooms = {
                entry.classroom for entry in schedule.entries[time_slot]
            }
        
        # Find available classrooms with sufficient capacity
        available_classrooms = [
            c for c in self.classrooms
            if c not in occupied_classrooms and 
            c.can_accommodate(student_count) and
            (not requires_lab or c.is_lab)
        ]
        
        if not available_classrooms:
            return None
        
        # Prefer classrooms that are closer to the required capacity
        available_classrooms.sort(key=lambda c: abs(c.capacity - student_count))
        return available_classrooms[0]
    
    def evolve(self, 
               population: List[Schedule], 
               generations: int = 100,
               progress_callback: Optional[ProgressCallback] = None) -> Schedule:
        """Evolve the population to find the best schedule."""
        self.best_fitness_history = []
        
        for generation in range(generations):
            # Evaluate fitness and sort population
            population_fitness = [
                (schedule, self.evaluate_schedule(schedule))
                for schedule in population
            ]
            population_fitness.sort(key=lambda x: x[1], reverse=True)
            
            # Update best solution
            current_best_fitness = population_fitness[0][1]
            if current_best_fitness > self.best_fitness:
                self.best_fitness = current_best_fitness
                self.best_schedule = deepcopy(population_fitness[0][0])
            
            self.best_fitness_history.append(current_best_fitness)
            
            # Report progress if callback is provided
            if progress_callback:
                progress_callback(generation, current_best_fitness)
            
            # Select elite schedules
            new_population = [
                schedule for schedule, _ in population_fitness[:self.elite_size]
            ]
            
            # Create offspring through crossover and mutation
            while len(new_population) < self.population_size:
                if random.random() < self.crossover_rate:
                    parent1 = self._tournament_select(population_fitness)
                    parent2 = self._tournament_select(population_fitness)
                    child = self._crossover(parent1, parent2)
                else:
                    # If no crossover, clone a parent
                    child = deepcopy(self._tournament_select(population_fitness))
                
                # Apply mutation
                if random.random() < self.mutation_rate:
                    child = self._mutate(child)
                
                if child.validate_hard_constraints():
                    new_population.append(child)
            
            population = new_population
        
        return self.best_schedule if self.best_schedule else population[0]