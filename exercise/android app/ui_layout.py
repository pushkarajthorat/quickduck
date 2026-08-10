KV_LAYOUT = '''
MDScreen:
    md_bg_color: 0.96, 0.96, 0.97, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(12)

        # Top Navigation Bar
        MDLabel:
            text: "HIIT Workout Machine"
            font_style: "H5"
            bold: True
            halign: "center"
            size_hint_y: None
            height: dp(40)

        # Active Exercise Display Card Viewport
        MDCard:
            orientation: 'vertical'
            padding: dp(16)
            size_hint_y: 0.35
            md_bg_color: 1, 1, 1, 1
            radius: [20, ]
            elevation: 1

            MDLabel:
                id: lbl_exercise
                text: "Ready to Start"
                font_style: "H4"
                bold: True
                halign: "center"

            MDLabel:
                id: lbl_reps
                text: "Reps per set: --"
                font_style: "Subtitle1"
                halign: "center"
                theme_text_color: "Hint"

            MDLabel:
                id: lbl_state
                text: "IDLE"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Secondary"

        # Timer & Metrics Layout Deck
        MDBoxLayout:
            orientation: 'vertical'
            spacing: dp(6)
            size_hint_y: 0.35

            MDLabel:
                id: lbl_timer
                text: "00:00"
                font_style: "H2"
                bold: True
                halign: "center"

            MDLabel:
                id: lbl_round
                text: "Round: -- / --"
                halign: "center"
                font_style: "Body1"

            MDLabel:
                id: lbl_total_remaining
                text: "Total Remaining: --:--"
                halign: "center"
                bold: True
                font_style: "Body1"

            MDProgressBar:
                id: progress_bar
                value: 0
                max: 100
                size_hint_y: None
                height: dp(8)

        # Hardware Feature Toggles (Mute Speech Synthesizer)
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(40)
            spacing: dp(12)
            pos_hint: {"center_x": .5}
            adaptive_width: True

            MDCheckbox:
                id: chk_mute
                size_hint: None, None
                size: dp(32), dp(32)
                active: False
            
            MDLabel:
                text: "Mute Voice Feedback"
                valign: "middle"
                adaptive_width: True
                font_style: "Body2"

        # Execution Interactive Bottom Trigger Deck
        MDBoxLayout:
            orientation: 'horizontal'
            spacing: dp(16)
            size_hint_y: None
            height: dp(60)

            MDFillRoundFlatButton:
                id: btn_action
                text: "Start Plan"
                size_hint_x: 0.5
                font_size: "18sp"
                on_release: app.toggle_workout()

            MDRaisedButton:
                id: btn_skip
                text: "Skip Set"
                size_hint_x: 0.5
                font_size: "18sp"
                disabled: True
                on_release: app.skip_exercise()
'''
