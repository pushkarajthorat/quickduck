import datetime
import time
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Exercise(BaseModel):
    """Represents an individual exercise configuration."""
    name: str = Field(..., min_length=1, description="Name of the exercise")
    duration: int = Field(..., gt=0, description="Duration of the exercise in seconds")
    rest_after: int = Field(default=0, ge=0, description="Rest period after exercise in seconds")

    @field_validator('name')
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

class WorkoutPlan(BaseModel):
    """Represents the complete workout plan consisting of sequential exercises."""
    title: str = Field(default="Daily Routine", min_length=1)
    exercises: List[Exercise] = Field(..., min_length=1, description="List of exercises in the session")

    @property
    def total_duration(self) -> int:
        """Calculates total plan duration including all exercises and rest intervals."""
        return sum(ex.duration + ex.rest_after for ex in self.exercises)

class ProgressMetrics(BaseModel):
    """DTO for communicating real-time session progress metrics."""
    current_item: str
    item_type: str  # 'Exercise' or 'Rest'
    item_time_remaining: int
    total_time_remaining: int
    completion_percentage: float
    expected_finish_time: str

class WorkoutEngine:
    """Manages the real-time execution lifecycle and tracking mechanics of a workout session."""
    def __init__(self, plan: WorkoutPlan):
        self.plan = plan
        self.total_workout_seconds = plan.total_duration
        self._elapsed_seconds = 0
        self._is_running = False

    def compute_metrics(self, current_item: str, item_type: str, item_rem: int) -> ProgressMetrics:
        """Calculates tracking calculations based on elapsed execution steps."""
        remaining_seconds = max(0, self.total_workout_seconds - self._elapsed_seconds)
        
        # Calculate completion percentage explicitly on time profile
        if self.total_workout_seconds > 0:
            percentage = (self._elapsed_seconds / self.total_workout_seconds) * 100
        else:
            percentage = 100.0
            
        percentage = min(100.0, max(0.0, percentage))
        
        # Determine prospective real-world timeline completion
        now = datetime.datetime.now()
        estimated_finish = now + datetime.timedelta(seconds=remaining_seconds)
        finish_timestamp = estimated_finish.strftime("%I:%M:%S %p")

        return ProgressMetrics(
            current_item=current_item,
            item_type=item_type,
            item_time_remaining=item_rem,
            total_time_remaining=remaining_seconds,
            completion_percentage=round(percentage, 2),
            expected_finish_time=finish_timestamp
        )

    def run_session(self, callback_handler) -> None:
        """Executes the timeline loop, updating runtime counters sequentially."""
        self._is_running = True
        self._elapsed_seconds = 0
        
        for idx, element in enumerate(self.plan.exercises):
            if not self._is_running:
                break
                
            # 1. Process Active Exercise Phase
            for rem in range(element.duration, 0, -1):
                if not self._is_running:
                    break
                metrics = self.compute_metrics(element.name, "Exercise", rem)
                callback_handler(metrics)
                time.sleep(1)
                self._elapsed_seconds += 1

            # 2. Process Rest Component Phase (if applicable)
            if element.rest_after > 0 and idx < len(self.plan.exercises) - 1:
                for rem in range(element.rest_after, 0, -1):
                    if not self._is_running:
                        break
                    metrics = self.compute_metrics(f"Rest after {element.name}", "Rest", rem)
                    callback_handler(metrics)
                    time.sleep(1)
                    self._elapsed_seconds += 1

        if self._is_running:
            # Send ultimate completion metric framing
            final_metrics = self.compute_metrics("Completed", "Done", 0)
            callback_handler(final_metrics)
        self._is_running = False

    def stop_session(self) -> None:
        """Safely interrupts structural execution flow loop."""
        self._is_running = False
