import os
import glob
import json
import io
import urllib.request
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime, timedelta

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
        return sum((ex.get("work duration per set", 0) + ex.get("rest duration per set", 0)) * ex.get("rounds", 1) for ex in self.plan)

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
        """Calculates dynamic total remaining time across all remaining blocks and rounds."""
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
        """Decrements time and handles automatic state transitions. Returns event flags."""
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
class WorkoutApp(tk.Tk):
    """macOS optimized Tkinter Interface with Dynamic Plan Selector Dropdown functionality."""
    def __init__(self):
        super().__init__()
        self.title("Mac Workout Tracker")
        self.geometry("550x770")  # Padded height slightly to accommodate selection row comfortably
        self.configure(bg="#F5F5F7")  
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.gif_frames = []
        self.gif_frames_delay = []
        self.gif_idx = 0
        self.gif_loop_id = None
        self.loaded_gif_url = None
        self.timer_running = False

        self.load_workout_json("workout.json")
        self.setup_styles()
        self.create_widgets()
        self.update_ui_display()

    def announce_state(self, event_type):
        """Uses native macOS speech engine ('say') to audibly announce workout changes."""
        exercise = self.engine.get_current_exercise()
        exercise_name = exercise.get("activity", "Exercise") if exercise else ""
        repetition = exercise.get("repetition per set", 1) if exercise else 0
        text_to_speak = ""

        if event_type == "START_WORK":
            text_to_speak = f"Do {repetition} {exercise_name} " if repetition > 1 else f"Do {exercise_name} "
        elif event_type == "START_ROUND":
            text_to_speak = f"Round {self.engine.current_round}. Begin {exercise_name}."
        elif event_type == "START_REST":
            text_to_speak = "Time to rest. Take a break."
        elif event_type == "COMPLETED":
            text_to_speak = "Workout complete! Amazing job today."
        else:
            return

        try:
            subprocess.Popen(["say", text_to_speak], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as error_msg:
            print(f"Speech module skipped: {error_msg}")

    def load_workout_json(self, filename="workout.json"):
        """Locates, opens, parses, and recursively flattens the chosen json workout plan."""
        if filename == "workout.json" and not os.path.exists(filename):
            self.workout_data = {
                "workout plan": [
                    {"activity": "Pushups", "repetition per set": 15, "work duration per set": 10, "rest duration per set": 5, "rounds": 3, "demo gif": "https://giphy.com"},
                    {"activity": "pullups", "repetition per set": 15, "work duration per set": 10, "rest duration per set": 5, "rounds": 3, "demo gif": "https://giphy.com"}
                ]
            }
            with open(filename, "w") as f:
                json.dump(self.workout_data, f, indent=4)
        else:
            try:
                with open(filename, "r") as f:
                    self.workout_data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse JSON file {filename}: {e}")
                self.workout_data = {"workout plan": []}

        def flatten_plan(activities):
            flat_list = []
            for item in activities:
                if "compound activity" in item:
                    nested_flattened = flatten_plan(item["compound activity"])
                    repeats = item.get("repeat", 1)
                    compound_rest = item.get("rest duration per set", 0)
                    
                    for r in range(repeats):
                        for sub_idx, sub_item in enumerate(nested_flattened):
                            cloned_item = dict(sub_item)
                            if sub_idx == len(nested_flattened) - 1 and compound_rest > 0:
                                cloned_item["rest duration per set"] = sub_item.get("rest duration per set", 0) + compound_rest
                            flat_list.append(cloned_item)
                else:
                    flat_list.append(dict(item))
            return flat_list

        raw_plan = self.workout_data.get("workout plan", [])
        flattened_plan = flatten_plan(raw_plan)

        previous_workout = {}
        for workout in flattened_plan:
            previous_workout.update(workout)
            workout.update(previous_workout)

        self.workout_data["workout plan"] = flattened_plan
        self.engine = WorkoutStateMachine(self.workout_data)

    def on_plan_selected(self, event):
        """Fires dynamically when an idle dropdown choice switches to reload application assets."""
        selected_file = self.cmb_plans.get()
        if os.path.exists(selected_file):
            self.load_workout_json(selected_file)
            self.update_ui_display()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("SF Pro Display", 12), padding=8)
        self.style.configure("Action.TButton", font=("SF Pro Display", 13, "bold"))
        self.style.configure("Horizontal.TProgressbar", thickness=12, background="#0A84FF", troughcolor="#E5E5EA")
        self.style.configure("TCombobox", font=("SF Pro Display", 11), padding=4)
    def create_widgets(self):
        self.header_frame = tk.Frame(self, bg="#FFFFFF", height=50, relief="groove", borderwidth=1)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)
        
        self.lbl_title = tk.Label(self.header_frame, text="Workout Tracker Machine", font=("SF Pro Display", 15, "bold"), bg="#FFFFFF", fg="#1D1D1F")
        self.lbl_title.pack(side="left", padx=20, pady=12)
        
        self.display_frame = tk.Frame(self, bg="#F5F5F7")
        self.display_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=15)

        # Dropdown Option Panel Frame Layout
        self.selector_frame = tk.Frame(self.display_frame, bg="#F5F5F7")
        self.selector_frame.pack(pady=5, fill="x")
        
        self.lbl_select = tk.Label(self.selector_frame, text="Choose Routine File:", font=("SF Pro Display", 11, "bold"), bg="#F5F5F7", fg="#515154")
        self.lbl_select.pack(side="left", padx=5)

        # Auto-scans file systems looking for target match extensions
        found_plans = glob.glob("workout*.json")
        if "workout.json" not in found_plans and os.path.exists("workout.json"):
            found_plans.append("workout.json")
        found_plans = sorted(list(set(found_plans)))
        
        self.cmb_plans = ttk.Combobox(self.selector_frame, values=found_plans, state="readonly", width=25)
        self.cmb_plans.pack(side="left", padx=10)
        self.cmb_plans.set("workout.json" if "workout.json" in found_plans else found_plans[0] if found_plans else "")
        self.cmb_plans.bind("<<ComboboxSelected>>", self.on_plan_selected)
        
        self.lbl_exercise = tk.Label(self.display_frame, text="Ready to Start", font=("SF Pro Display", 22, "bold"), bg="#F5F5F7", fg="#1D1D1F")
        self.lbl_exercise.pack(pady=5)
        
        self.lbl_reps = tk.Label(self.display_frame, text="Reps per set: --", font=("SF Pro Display", 13), bg="#F5F5F7", fg="#86868B")
        self.lbl_reps.pack(pady=2)

        self.lbl_state = tk.Label(self.display_frame, text="IDLE", font=("SF Pro Display", 13, "bold"), bg="#F5F5F7", fg="#515154")
        self.lbl_state.pack(pady=5)

        self.gif_canvas = tk.Label(self.display_frame, bg="#E5E5EA", width=250, height=200, relief="sunken", borderwidth=1)
        self.gif_canvas.pack(pady=10)

        self.lbl_timer = tk.Label(self.display_frame, text="00:00", font=("SF Pro Display", 44, "bold"), bg="#F5F5F7", fg="#1D1D1F")
        self.lbl_timer.pack(pady=5)

        self.lbl_round = tk.Label(self.display_frame, text="Round: -- / --", font=("SF Pro Display", 13), bg="#F5F5F7", fg="#86868B")
        self.lbl_round.pack(pady=2)

        self.lbl_total_remaining = tk.Label(self.display_frame, text="Total Remaining: --:--", font=("SF Pro Display", 13, "bold"), bg="#F5F5F7", fg="#86868B")
        self.lbl_total_remaining.pack(pady=2)

        self.lbl_est_completion = tk.Label(self.display_frame, text="Est. Completion: --:--", font=("SF Pro Display", 13), bg="#F5F5F7", fg="#86868B")
        self.lbl_est_completion.pack(pady=2)

        self.progress_bar = ttk.Progressbar(self.display_frame, orient="horizontal", length=320, mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(pady=12)

        self.control_frame = tk.Frame(self, bg="#FFFFFF", height=65, relief="groove", borderwidth=1)
        self.control_frame.grid(row=2, column=0, sticky="ew")
        self.control_frame.grid_propagate(False)

        self.btn_action = ttk.Button(self.control_frame, text="Start Plan", style="Action.TButton", command=self.toggle_workout)
        self.btn_action.pack(side="left", padx=20, pady=12)

        self.btn_skip = ttk.Button(self.control_frame, text="Skip Exercise", style="TButton", command=self.skip_exercise)
        self.btn_skip.pack(side="right", padx=20, pady=12)
        self.btn_skip.configure(state="disabled")

    def download_and_parse_gif(self, url):
        if not url or self.loaded_gif_url == url:
            return
        if self.gif_loop_id:
            self.after_cancel(self.gif_loop_id)
            self.gif_loop_id = None
        self.gif_frames.clear()
        self.gif_frames_delay.clear()
        self.gif_idx = 0
        self.loaded_gif_url = url
        threading.Thread(target=self._async_gif_worker, args=(url,), daemon=True).start()

    def _async_gif_worker(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                img_data = response.read()
            pil_img = Image.open(io.BytesIO(img_data))
            temp_frames = []
            temp_delays = []
            try:
                while True:
                    frame = pil_img.copy().convert("RGBA")
                    frame.thumbnail((250, 200), Image.Resampling.LANCZOS)
                    temp_frames.append(frame)
                    temp_delays.append(frame.info.get('duration', 100))
                    pil_img.seek(pil_img.tell() + 1)
            except EOFError:
                pass
            self.after(0, lambda: self._finalize_gif_loading(temp_frames, temp_delays))
        except Exception as error_msg:
            print(f"Error streaming dynamic GIF media: {error_msg}")
            self.after(0, lambda: self.gif_canvas.configure(image="", text="Preview unavailable"))

    def _finalize_gif_loading(self, frames, delays):
        self.gif_frames = [ImageTk.PhotoImage(f) for f in frames]
        self.gif_frames_delay = delays
        if self.gif_frames:
            self.animate_gif_canvas()

    def animate_gif_canvas(self):
        if not self.gif_frames:
            return
        self.gif_idx = (self.gif_idx + 1) % len(self.gif_frames)
        self.gif_canvas.configure(image=self.gif_frames[self.gif_idx], text="")
        self.gif_loop_id = self.after(self.gif_frames_delay[self.gif_idx], self.animate_gif_canvas)

    def toggle_workout(self):
        if self.engine.current_state in (WorkoutStateMachine.STATE_IDLE, WorkoutStateMachine.STATE_COMPLETED):
            success, event = self.engine.start_workout()
            if success:
                self.timer_running = True
                self.btn_skip.configure(state="normal")
                self.cmb_plans.configure(state="disabled")  # Freezes selection interactions securely
                if event:
                    self.announce_state(event)
                self.run_loop()
        elif self.timer_running:
            self.timer_running = False
            self.btn_action.configure(text="Resume")
        else:
            self.timer_running = True
            self.btn_action.configure(text="Pause")
            self.run_loop()

    def skip_exercise(self):
        event = self.engine.skip_current()
        if event:
            self.announce_state(event)
        self.update_ui_display()

    def run_loop(self):
        if not self.timer_running:
            return
        transition_event = self.engine.tick()
        self.update_ui_display()
        if transition_event:
            self.announce_state(transition_event)
        if self.engine.current_state == WorkoutStateMachine.STATE_COMPLETED:
            self.timer_running = False
            if self.gif_loop_id:
                self.after_cancel(self.gif_loop_id)
            self.gif_canvas.configure(image="", text="Finished!")
            self.btn_action.configure(text="Restart", style="Action.TButton")
            self.btn_skip.configure(state="disabled")
            self.cmb_plans.configure(state="readonly")  # Automatically releases dropdown input locks
            self.progress_bar['value'] = 100
            messagebox.showinfo("Done!", "Awesome job! You finished the entire workout plan.")
            return
        self.after(1000, self.run_loop)

    def update_ui_display(self):
        state = self.engine.current_state
        exercise = self.engine.get_current_exercise()

        minutes = self.engine.time_remaining // 60
        seconds = self.engine.time_remaining % 60
        self.lbl_timer.configure(text=f"{minutes:02d}:{seconds:02d}")
        self.lbl_state.configure(text=state)

        total_rem = self.engine.get_total_remaining_time()
        rem_min = total_rem // 60
        rem_sec = total_rem % 60
        self.lbl_total_remaining.configure(text=f"Total Remaining: {rem_min:02d}:{rem_sec:02d}")

        if total_rem > 0 and state != WorkoutStateMachine.STATE_COMPLETED:
            est_time = datetime.now() + timedelta(seconds=total_rem)
            self.lbl_est_completion.configure(text=f"Est. Completion: {est_time.strftime('%I:%M:%S %p')}")
            
            total_dur = self.engine.total_workout_duration
            progress_pct = ((total_dur - total_rem) / total_dur) * 100 if total_dur > 0 else 0
            self.progress_bar['value'] = progress_pct
        else:
            self.lbl_est_completion.configure(text="Est. Completion: --:--")
            self.progress_bar['value'] = 0 if state == WorkoutStateMachine.STATE_IDLE else 100

        if exercise:
            self.lbl_exercise.configure(text=exercise.get("activity", "Unknown"))
            reps = exercise.get("repetition per set", "--")
            self.lbl_reps.configure(text=f"Reps per set: {reps}" if reps != "--" else "Reps per set: --")
            self.lbl_round.configure(text=f"Round: {self.engine.current_round} / {exercise.get('rounds', 1)}")
            
            gif_url = exercise.get("demo gif", exercise.get("gif", None))
            if gif_url and self.loaded_gif_url != gif_url:
                self.gif_canvas.configure(image="", text="Loading demonstration...")
                self.after(10, lambda: self.download_and_parse_gif(gif_url))
        else:
            self.lbl_exercise.configure(text="Ready to Start" if state == WorkoutStateMachine.STATE_IDLE else "Workout Complete!")
            self.lbl_reps.configure(text="Reps per set: --")
            self.lbl_round.configure(text="Round: -- / --")

        if state in (WorkoutStateMachine.STATE_WORK, WorkoutStateMachine.STATE_REST):
            self.lbl_state.configure(fg="#FF453A" if state == WorkoutStateMachine.STATE_WORK else "#34C759")
            self.btn_action.configure(text="Pause")
        elif state == WorkoutStateMachine.STATE_IDLE:
            self.lbl_state.configure(fg="#515154")
            self.btn_action.configure(text="Start Plan")
        elif state == WorkoutStateMachine.STATE_COMPLETED:
            self.lbl_state.configure(fg="#0A84FF")

if __name__ == "__main__":
    app = WorkoutApp()
    app.mainloop()
