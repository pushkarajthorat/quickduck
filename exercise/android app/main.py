import os
from datetime import datetime, timedelta

from kivy.lang import Builder
from kivy.app import App
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog

# Import decoupled tracking components from adjacent local files
from state_machine import WorkoutStateMachine
from ui_layout import KV_LAYOUT

# Safe compilation checking layer for platform-specific API endpoints
if platform == "android":
    from jnius import autoclass
    Locale = autoclass('java.util.Locale')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')

class HIITAndroidApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.timer_running = False
        self.clock_event = None
        
        # Local Storage Sandbox Database (Replaces native OS filesystem writing calls)
        self.store = JsonStore('workout_history.json')
        
        # Default Plan Template Data Schema Mapping
        self.workout_data = {
            "workout plan": [
                {"activity": "Pushups", "repetition per set": 15, "work duration per set": 10, "rest duration per set": 5, "rounds": 3},
                {"activity": "Pullups", "repetition per set": 12, "work duration per set": 10, "rest duration per set": 5, "rounds": 3}
            ],
            "alias": "Default General Routine"
        }
        
        self.engine = WorkoutStateMachine(self.workout_data)
        self.init_android_audio_engines()
        
        return Builder.load_string(KV_LAYOUT)

    def init_android_audio_engines(self):
        """Spawns native hardware bindings for system speech on Android devices."""
        self.tts = None
        if platform == "android":
            try:
                def on_init(status):
                    if status == TextToSpeech.SUCCESS:
                        self.tts.setLanguage(Locale.US)
                self.tts = TextToSpeech(App.get_running_app().root_window, on_init)
            except Exception as e:
                print(f"Android Native TTS Binding Failed: {e}")

    def android_speak(self, text):
        """Asynchronously dispatches speech synthesis via Android's TextToSpeech API."""
        if self.root.ids.chk_mute.active:
            return
        if platform == "android" and self.tts:
            self.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, None)
        else:
            print(f"[Desktop Speech Engine Preview]: {text}")

    def toggle_workout(self):
        """Manages runtime timing tracking flags and active UI selection locks."""
        if self.engine.current_state in (WorkoutStateMachine.STATE_IDLE, WorkoutStateMachine.STATE_COMPLETED):
            success, event = self.engine.start_workout()
            if success:
                self.timer_running = True
                self.root.ids.btn_skip.disabled = False
                if event:
                    self.announce_state(event)
                self.clock_event = Clock.schedule_interval(self.run_loop, 1.0)
        elif self.timer_running:
            self.timer_running = False
            if self.clock_event:
                Clock.unschedule(self.clock_event)
            self.root.ids.btn_action.text = "Resume"
        else:
            self.timer_running = True
            self.root.ids.btn_action.text = "Pause"
            self.clock_event = Clock.schedule_interval(self.run_loop, 1.0)

    def skip_exercise(self):
        event = self.engine.skip_current()
        if event:
            self.announce_state(event)
        self.update_ui_display()

    def run_loop(self, dt):
        if not self.timer_running:
            return
        
        transition_event = self.engine.tick()
        self.update_ui_display()
        
        if transition_event:
            self.announce_state(transition_event)
            
        if self.engine.current_state == WorkoutStateMachine.STATE_COMPLETED:
            self.timer_running = False
            if self.clock_event:
                Clock.unschedule(self.clock_event)
            
            # Record tracking parameters directly to sandboxed local app storage
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            self.store.put(date_str, alias=self.workout_data.get("alias"), time=now.strftime("%I:%M:%S %p"))
            
            self.root.ids.btn_action.text = "Restart"
            self.root.ids.btn_skip.disabled = True
            self.root.ids.progress_bar.value = 100
            
            # Call a mobile-responsive modal overlay prompt
            dialog = MDDialog(title="Done!", text="Awesome job! You finished the entire workout plan.")
            dialog.open()

    def announce_state(self, event_type):
        """Assembles dynamic string data contexts to pass to the voice feedback layer."""
        exercise = self.engine.get_current_exercise()
        exercise_name = exercise.get("activity", "Exercise") if exercise else ""
        repetition = exercise.get("repetition per set", 1) if exercise else 0

        if event_type == "START_WORK":
            text = f"Do {repetition} {exercise_name}"
        elif event_type == "START_ROUND":
            text = f"Round {self.engine.current_round}. Do {repetition} {exercise_name}"
        elif event_type == "START_REST":
            text = "Take a rest"
        elif event_type == "COMPLETED":
            text = "Workout complete! Amazing job today."
        else:
            return
        self.android_speak(text)

    def update_ui_display(self):
        """Refreshes visible tracking metric outputs on the device dashboard screen."""
        ids = self.root.ids
        state = self.engine.current_state
        exercise = self.engine.get_current_exercise()
        
        ids.lbl_timer.text = f"{self.engine.time_remaining//60:02d}:{self.engine.time_remaining%60:02d}"
        ids.lbl_state.text = state
        
        total_rem = self.engine.get_total_remaining_time()
        ids.lbl_total_remaining.text = f"Total Remaining: {total_rem//60:02d}:{total_rem%60:02d}"

        if total_rem > 0 and state != WorkoutStateMachine.STATE_COMPLETED:
            progress_pct = ((self.engine.total_workout_duration - total_rem) / self.engine.total_workout_duration) * 100
            ids.progress_bar.value = progress_pct
        else:
            ids.progress_bar.value = 100 if state == WorkoutStateMachine.STATE_COMPLETED else 0

        if exercise:
            ids.lbl_exercise.text = exercise.get("activity", "Unknown")
            ids.lbl_reps.text = f"Reps per set: {exercise.get('repetition per set', '--')}"
            ids.lbl_round.text = f"Round: {self.engine.current_round} / {exercise.get('rounds', 1)}"
        else:
            ids.lbl_exercise.text = "Workout Complete!" if state == WorkoutStateMachine.STATE_COMPLETED else "Ready to Start"

if __name__ == "__main__":
    HIITAndroidApp().run()
