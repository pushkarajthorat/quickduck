class WorkoutStateMachine:
    """Manages the states, timers, and transitions of the workout."""
    STATE_IDLE = "IDLE"
    STATE_WORK = "WORK"
    STATE_REST = "REST"
    STATE_COMPLETED = "COMPLETED"

    def __init__(self, plan_data):
        self.plan = plan_data.get("workout plan", [])
        self.current_exercise_idx = 0
        self.current_round = 1
        self.current_state = self.STATE_IDLE
        self.time_remaining = 0
        self.total_workout_duration = self.calculate_initial_total()
        
    def calculate_initial_total(self):
        """Calculates total fixed duration of the plan at launch."""
        return sum(
            (ex.get("work duration per set", 0) + ex.get("rest duration per set", 0)) 
            * ex.get("rounds", 1) for ex in self.plan
        )

    def get_current_exercise(self):
        if 0 <= self.current_exercise_idx < len(self.plan):
            return self.plan[self.current_exercise_idx]
        return None

    def start_workout(self):
        if not self.plan:
            self.current_state = self.STATE_COMPLETED
            return False, None
        self.current_exercise_idx = 0
        self.current_round = 1
        self.transition_to_work()
        return True, "START_WORK"

    def transition_to_work(self):
        exercise = self.get_current_exercise()
        if exercise:
            self.current_state = self.STATE_WORK
            self.time_remaining = exercise.get("work duration per set", 0)

    def transition_to_rest(self):
        exercise = self.get_current_exercise()
        if exercise:
            self.current_state = self.STATE_REST
            self.time_remaining = exercise.get("rest duration per set", 0)

    def get_total_remaining_time(self):
        """Calculates dynamic total remaining time across all blocks and rounds."""
        if self.current_state == self.STATE_COMPLETED:
            return 0
        if self.current_state == self.STATE_IDLE:
            return self.total_workout_duration
        
        total = 0
        for idx, ex in enumerate(self.plan):
            if idx < self.current_exercise_idx:
                continue
            work = ex.get("work duration per set", 0)
            rest = ex.get("rest duration per set", 0)
            rounds = ex.get("rounds", 1)
            
            if idx == self.current_exercise_idx:
                if self.current_state == self.STATE_WORK:
                    total += self.time_remaining + rest
                elif self.current_state == self.STATE_REST:
                    total += self.time_remaining
                total += (rounds - self.current_round) * (work + rest)
            else:
                total += rounds * (work + rest)
        return total

    def tick(self):
        """Decrements time and handles automatic state transitions."""
        if self.current_state in (self.STATE_IDLE, self.STATE_COMPLETED):
            return None

        if self.time_remaining > 0:
            self.time_remaining -= 1
            return None

        exercise = self.get_current_exercise()
        max_rounds = exercise.get("rounds", 1)

        if self.current_state == self.STATE_WORK:
            if self.current_round < max_rounds:
                self.transition_to_rest()
                return "START_REST"
            else:
                self.current_exercise_idx += 1
                if self.current_exercise_idx < len(self.plan):
                    self.current_round = 1
                    self.transition_to_work()
                    return "START_WORK"
                else:
                    self.current_state = self.STATE_COMPLETED
                    return "COMPLETED"
        
        elif self.current_state == self.STATE_REST:
            self.current_round += 1
            self.transition_to_work()
            return "START_ROUND"
        return None

    def skip_current(self):
        """Skips the entire remaining sets of the current exercise."""
        if self.current_state in (self.STATE_IDLE, self.STATE_COMPLETED):
            return None
        self.current_exercise_idx += 1
        if self.current_exercise_idx < len(self.plan):
            self.current_round = 1
            self.transition_to_work()
            return "START_WORK"
        else:
            self.current_state = self.STATE_COMPLETED
            return "COMPLETED"
