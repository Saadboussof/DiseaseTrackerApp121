# views/prediction_view.py
import tkinter as tk
from tkinter import ttk, Frame, Label, StringVar, Scale, IntVar
from ui_components import GlowButton, GradientFrame, AnimatedLoadingIndicator

class PredictionView(Frame):
    """View for forecasting future disease trends."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg_dark"])
        self.controller = controller
        self.rowconfigure(0, weight=0)  # Controls area
        self.rowconfigure(1, weight=1)  # Plot area
        self.columnconfigure(0, weight=1)  # Full width

        # Controls Frame
        self.controls_frame = Frame(self, bg=controller.colors["bg_dark"], padx=20, pady=15)
        self.controls_frame.grid(row=0, column=0, sticky="new")
        
        # Title area with animations
        self.title_container = Frame(self.controls_frame, bg=controller.colors["bg_dark"])
        self.title_container.pack(anchor="w", fill="x", expand=True)
        
        # Main title with glow effect
        title_text = "Disease Forecast"
        
        # Title glow (behind title)
        self.title_glow = Label(
            self.title_container, text=title_text,
            fg=controller.colors["accent_teal"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 19, "bold")
        )
        self.title_glow.place(x=1, y=1)
        self._start_title_glow_animation()
        
        # Main title
        self.title_label = Label(
            self.title_container, text=title_text,
            fg=controller.colors["text_primary"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(anchor="w")
        
        # Subtitle
        self.subtitle = StringVar(value="Predictive modeling for future disease patterns")
        self.subtitle_label = Label(
            self.title_container, textvariable=self.subtitle,
            fg=controller.colors["text_secondary"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 10)
        )
        self.subtitle_label.pack(anchor="w", pady=(0, 10))
        
        # Slider Panel (Create a separate frame with slight border effect)
        self.slider_panel = Frame(
            self.controls_frame, 
            bg=controller.colors["bg_card"], 
            padx=15, pady=15,
            highlightbackground=controller.colors["accent_teal"],
            highlightcolor=controller.colors["accent_teal"],
            highlightthickness=1,
            bd=0
        )
        self.slider_panel.pack(fill="x", pady=5)
        
        # Controls inside panel
        self.slider_controls = Frame(self.slider_panel, bg=controller.colors["bg_card"])
        self.slider_controls.pack(fill="x")
        
        # Layout for slider row
        self.slider_controls.columnconfigure(0, weight=0)  # Label
        self.slider_controls.columnconfigure(1, weight=1)  # Slider
        self.slider_controls.columnconfigure(2, weight=0)  # Value
        self.slider_controls.columnconfigure(3, weight=0)  # Button
        
        # Slider Label
        slider_label = Label(
            self.slider_controls, text="Forecast Period:", 
            fg=controller.colors["text_secondary"], 
            bg=controller.colors["bg_card"],
            font=("Segoe UI", 10)
        )
        slider_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Slider for prediction days
        self.days_var = IntVar(value=controller.prediction_days.get())
        self.slider = Scale(
            self.slider_controls,
            from_=7, to=360,
            orient="horizontal",
            variable=self.days_var,
            command=controller.update_prediction_days,
            bg=controller.colors["bg_card"],
            fg=controller.colors["text_primary"],
            troughcolor=controller.colors["bg_dark"],
            activebackground=controller.colors["accent_teal"],
            relief="flat", bd=0,
            highlightthickness=0,
            sliderrelief="flat"
        )
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)
        
        # Value Label
        self.value_label = Label(
            self.slider_controls, 
            text=f"{controller.prediction_days.get()} days",
            fg=controller.colors["text_primary"], 
            bg=controller.colors["bg_card"],
            font=("Segoe UI", 10, "bold"),
            width=7,  # Fixed width for stability
        )
        self.value_label.grid(row=0, column=2, padx=10, sticky="e")

        # Predict Button
        self.predict_button = GlowButton(
            self.slider_controls, text="Run Forecast", 
            command=controller.start_prediction,
            width=140, height=38, 
            icon="🔮", icon_font_size=18, 
            font_size=10,
            start_color=controller.colors["accent_teal"], 
            end_color="#3366FF",  # Gradient to blue for prediction
            state='disabled'  # Initially disabled
        )
        self.predict_button.grid(row=0, column=3, padx=(20, 0))

        # Plot area (use gradient frame)
        self.plot_frame = GradientFrame(
            self, controller.colors["bg_card"], controller.colors["bg_gradient_end"]
        )
        self.plot_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Create animated loading indicator (initially hidden)
        self.loading_indicator = AnimatedLoadingIndicator(
            self.plot_frame, width=150, height=150, color="#3366FF"  # Blue for prediction
        )
        
        # Add initial placeholder
        self.add_placeholder("Complete analysis first, then use the slider to set forecast period")
        
        # Start the subtle animations
        self._animate_slider_highlight()

    def _start_title_glow_animation(self):
        """Animate the glow effect behind the title"""
        def glow_cycle():
            # Create a subtle pulsing glow effect
            colors = [
                self.controller.colors["accent_teal"],  # Teal
                "#3366FF",                             # Blue
                "#6633FF",                             # Purple
                "#3366FF",                             # Blue
                self.controller.colors["accent_teal"],  # Teal
            ]
            
            for color in colors:
                self.title_glow.configure(fg=color)
                self.after(800, lambda: None)  # Animation step delay
            
            # Schedule the next animation cycle
            self.after(800, glow_cycle)
        
        # Start animation cycle
        self.after(1000, glow_cycle)
        
    def _animate_slider_highlight(self):
        """Animate the slider panel highlight"""
        def pulse_border():
            # List of colors for the pulse effect
            colors = [
                self.controller.colors["accent_teal"],  # Normal
                "#3366FF",                             # Blue
                "#6633FF",                             # Purple
                "#3366FF",                             # Blue
                self.controller.colors["accent_teal"],  # Back to normal
            ]
            
            # Apply colors with delay between each
            for color in colors:
                self.slider_panel.config(highlightbackground=color, highlightcolor=color)
                self.after(1000, lambda: None)
            
            # Schedule next pulse after a longer pause
            self.after(5000, pulse_border)
        
        # Start the animation
        self.after(2000, pulse_border)
    
    def add_placeholder(self, message):
        """Adds a placeholder message to the plot frame."""
        # Clear existing content
        for widget in self.plot_frame.winfo_children():
            if widget != self.loading_indicator:  # Keep the loading indicator
                widget.destroy()
        
        # Create placeholder container frame
        placeholder_frame = Frame(self.plot_frame, bg=self.plot_frame.cget("bg"))
        placeholder_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Add icon
        icon_label = Label(
            placeholder_frame, text="🔮", 
            font=("Segoe UI Symbol", 48),
            fg=self.controller.colors["text_secondary"],
            bg=self.plot_frame.cget("bg")
        )
        icon_label.pack(pady=(0, 10))
        
        # Add message
        msg_label = Label(
            placeholder_frame, text=message,
            fg=self.controller.colors["text_secondary"],
            bg=self.plot_frame.cget("bg"),
            font=("Segoe UI", 12),
            wraplength=400
        )
        msg_label.pack()
    
    def show_loading(self, message="Generating forecast..."):
        """Shows the loading indicator and hides other content."""
        # Place loading indicator in center
        self.loading_indicator.place(relx=0.5, rely=0.5, anchor="center")
        
        # Update loading message
        self.loading_indicator.set_message(message)
        
        # Start animation
        self.loading_indicator.start_animation()
        
        # Update subtitle
        self.subtitle.set("Processing prediction model... please wait")
    
    def hide_loading(self):
        """Hides the loading indicator."""
        self.loading_indicator.stop_animation()
        self.loading_indicator.place_forget()
        
        # Restore subtitle
        self.subtitle.set("Predictive modeling for future disease patterns")
    
    def update_subtitle(self, text):
        """Updates the subtitle text."""
        self.subtitle.set(text)

    def get_predict_button(self):
        """Returns the prediction button widget."""
        return self.predict_button

    def get_slider(self):
        """Returns the days slider widget."""
        return self.slider

    def get_value_label(self):
        """Returns the value label widget for the slider."""
        return self.value_label
    
    def get_plot_frame(self):
        """Returns the frame where plots should be displayed."""
        return self.plot_frame