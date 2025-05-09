# views/analysis_view.py
import tkinter as tk
from tkinter import ttk, Frame, Label, StringVar
from ui_components import GradientFrame, AnimatedLoadingIndicator

class AnalysisView(Frame):
    """View for displaying detailed analysis charts and metrics."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg_dark"])
        self.controller = controller
        self.rowconfigure(0, weight=0)   # Title area
        self.rowconfigure(1, weight=1)   # Plot area
        self.columnconfigure(0, weight=1) # Full width

        # Title area
        self.title_frame = Frame(self, bg=controller.colors["bg_dark"], padx=20, pady=15)
        self.title_frame.grid(row=0, column=0, sticky="ew")
        
        # Main title with shadow effect
        title_text = "Disease Trend Analysis"
        self.title_shadow = Label(
            self.title_frame, text=title_text,
            fg=controller.colors["bg_card"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_shadow.place(x=22, y=12)  # Shadow position
        
        self.title_label = Label(
            self.title_frame, text=title_text,
            fg=controller.colors["text_primary"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(anchor="w")
        
        # Subtitle
        self.subtitle = StringVar(value="Historical data analysis and trends")
        self.subtitle_label = Label(
            self.title_frame, textvariable=self.subtitle,
            fg=controller.colors["text_secondary"], bg=controller.colors["bg_dark"],
            font=("Segoe UI", 10)
        )
        self.subtitle_label.pack(anchor="w", pady=(0, 10))

        # Plot area (use gradient frame)
        self.plot_frame = GradientFrame(
            self, controller.colors["bg_card"], controller.colors["bg_gradient_end"]
        )
        self.plot_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Create animated loading indicator (initially hidden)
        self.loading_indicator = AnimatedLoadingIndicator(
            self.plot_frame, width=150, height=150, color=controller.colors["accent_teal"]
        )
        
        # Add initial placeholder
        self.add_placeholder("Select a disease and click Analyze to view detailed trends")
        
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
            placeholder_frame, text="📊", 
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
    
    def show_loading(self, message="Analyzing data..."):
        """Shows the loading indicator and hides other content."""
        # Place loading indicator in center
        self.loading_indicator.place(relx=0.5, rely=0.5, anchor="center")
        
        # Update loading message
        self.loading_indicator.set_message(message)
        
        # Start animation
        self.loading_indicator.start_animation()
        
        # Update subtitle
        self.subtitle.set("Processing data... please wait")
    
    def hide_loading(self):
        """Hides the loading indicator."""
        self.loading_indicator.stop_animation()
        self.loading_indicator.place_forget()
        
        # Restore subtitle
        self.subtitle.set("Historical data analysis and trends")
    
    def update_subtitle(self, text):
        """Updates the subtitle text."""
        self.subtitle.set(text)

    def get_plot_frame(self):
        """Returns the frame where plots should be displayed."""
        return self.plot_frame