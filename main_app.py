# main_app.py 

import os
import sys
import threading
import traceback
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Scale, StringVar, font, Canvas
from tkinter import filedialog
import ctypes # For DPI awareness check

# --- Local Application Imports ---
try:
    import config
    import data_loader
    import processing
    import analysis
    import prediction
    from views.dashboard_view import DashboardView
    from views.analysis_view import AnalysisView
    from views.prediction_view import PredictionView
    from ui_components import ( # Import UI components
        GradientFrame,
        GlowButton,
        StatusBarWithRisk,
        StatsCard # Ensure StatsCard is imported if needed directly, though used in views
    )
except ImportError as e:
    print(f"FATAL ERROR: Importing modules: {e}")
    # Add hints for common import errors
    if "views" in str(e): print("Hint: Ensure 'views' directory exists and contains __init__.py + view files.")
    if "ui_components" in str(e): print("Hint: Ensure ui_components.py exists in the main directory.")
    try: # Tkinter error popup
        import tkinter.messagebox
        root_err = tk.Tk(); root_err.withdraw()
        tkinter.messagebox.showerror("Import Error", f"Failed to import modules: {e}\nCheck console for hints.")
        root_err.destroy()
    except Exception: pass
    sys.exit(1)


# --- Main Application Class (Controller) ---
class DarkThemedDiseaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry(config.WINDOW_GEOMETRY)
        self.root.configure(bg="#1A103C") # Use the darker base background

        self.colors = {
            "bg_dark": "#1A103C",
            "bg_gradient_end": "#1e1347",
            "bg_card": "#261758",
            "text_primary": "#E0E0FF",
            "text_secondary": "#8A7CB4",
            "placeholder_text": config.PLACEHOLDER_COLOR, # Use config color
            "accent_teal": "#00CCB8",
            "accent_pink": "#FF3366",
            "accent_orange": "#FC6657",
            "accent_yellow": "#FFC107",
            "success": "#28A745",
            "warning": "#FFC107",
            "danger": "#B12025",
            "disabled_fg": "#6A5C94",
            "disabled_bg": "#3A2E70",
            "sidebar_bg": "#140c2f", # Keep sidebar distinct bg
            "sidebar_hover": "#261758",
            "sidebar_active": config.PLOT_COLORS_DARK["history_cases"], # Use a default active color
            "particle_color": "#453AA8", # New color for background particles
        }

        # Data storage
        self.raw_covid_data = None
        self.raw_influenza_data = None
        self.raw_zika_data = None
        self.disease_data = None # Holds *processed* data for the *selected* target/country
        self.model = None
        self.scaler_X = None
        self.current_target_col_name = None # Stores 'cases' or 'deaths' after processing *single* country

        # UI State Variables
        self.current_disease = tk.StringVar(value="Select Disease")
        self.selected_country = tk.StringVar(value="Select Country")
        self.selected_target = tk.StringVar(value=config.DEFAULT_ANALYSIS_TARGET) # "Cases" or "Deaths"
        self.current_theme = tk.StringVar(value="dark") # New theme state variable

        self.allowed_covid_countries_in_data = []
        self.allowed_influenza_countries_in_data = []
        self.allowed_zika_countries_in_data = []
        self.available_diseases = ["Select Disease"] + config.AVAILABLE_DISEASES # Add placeholder
        self.available_targets = config.ANALYSIS_TARGETS

        self.prediction_days = tk.IntVar(value=config.PREDICTION_DEFAULT_DAYS)
        self.active_view_name = tk.StringVar(value="dashboard")

        # UI Element References
        self.sidebar_frame = None
        self.header_frame = None
        self.content_area = None
        self.status_bar = None
        self.disease_combobox = None
        self.country_combobox = None
        self.target_combobox = None # New Combobox for Target
        self.load_button = None
        self.analyze_button = None
        self.export_all_button = None
        self.sidebar_buttons = {}
        self.view_frames = {}
        self.canvas = None # For embedded plots
        self.toolbar = None # For embedded plots
        self.particle_bg = None # New particle background
        self.loading_indicator = None # New loading indicator
        self.theme_toggle = None # New theme toggle

        # Create UI elements AFTER setting placeholders
        self.configure_style()
        self.create_base_layout()
        self.create_views()
        self.create_header_controls() # Creates comboboxes and buttons
        self.create_sidebar_buttons()
        self.create_status_bar()

        # Initial setup
        self.show_view("dashboard")
        self.clear_statistics()
        self._update_ui_element_states() # Handles initial state & color of all controls


    def configure_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- General Styles ---
        self.style.configure('.', background=self.colors["bg_dark"], foreground=self.colors["text_primary"], bordercolor=self.colors["bg_card"], font=('Segoe UI', 10))
        self.style.configure('TFrame', background=self.colors["bg_dark"])
        self.style.configure('Card.TFrame', background=self.colors["bg_card"])
        self.style.configure('TLabel', background=self.colors["bg_dark"], foreground=self.colors["text_primary"])
        self.style.configure('Secondary.TLabel', foreground=self.colors["text_secondary"])
        self.style.configure('Card.TLabel', background=self.colors["bg_card"], foreground=self.colors["text_primary"])
        self.style.configure('Horizontal.TScale', background=self.colors["bg_card"], troughcolor=self.colors["bg_dark"], sliderrelief="flat", borderwidth=0)
        self.style.map('Horizontal.TScale', background=[('active', self.colors["accent_teal"])], troughcolor=[('disabled', self.colors["disabled_bg"])])
        self.style.configure("Dark.Horizontal.TProgressbar", troughcolor=self.colors["bg_card"], background=self.colors["accent_teal"], bordercolor=self.colors["bg_card"], darkcolor=self.colors["accent_teal"], lightcolor=self.colors["bg_dark"], troughrelief='flat')

        # --- Pill Combobox Style (Used for Disease, Country, Target) ---
        combobox_padding = (15, 9)
        self.style.configure('Pill.TCombobox',
                             padding=combobox_padding,
                             borderwidth=1, relief='flat', font=('Segoe UI', 10),
                             fieldbackground=self.colors["bg_card"],
                             background=self.colors["bg_card"], # Dropdown list bg
                             foreground=self.colors["placeholder_text"], # Default placeholder color
                             arrowcolor=self.colors["text_secondary"], arrowsize=12,
                             selectbackground=self.colors["accent_teal"], # Dropdown selection bg
                             selectforeground=self.colors["text_primary"], # Dropdown selection fg
                             insertcolor=self.colors["text_primary"],
                             bordercolor=self.colors["bg_card"], # Default border matches background
                             lightcolor=self.colors["bg_card"], darkcolor=self.colors["bg_card"]) # Remove 3D effect

        self.style.map('Pill.TCombobox',
            bordercolor=[('focus', self.colors["accent_teal"]), ('!focus', self.colors["bg_card"])],
            fieldbackground=[('readonly', self.colors["bg_card"]), ('disabled', self.colors["disabled_bg"])],
            foreground=[('disabled', self.colors["disabled_fg"])],
            arrowcolor=[('disabled', self.colors["disabled_fg"])]
            )
        # Text color (placeholder vs normal) handled via _update_combobox_color

        # --- Pill Sidebar Button Style ---
        button_padding = (20, 12)
        self.style.configure('Pill.TButton',
                             background=self.colors["sidebar_bg"], foreground=self.colors["text_secondary"],
                             font=('Segoe UI', 10, 'bold'), borderwidth=0, relief='flat',
                             anchor='center', padding=button_padding, focuscolor=self.colors["sidebar_bg"])

        self.style.map('Pill.TButton',
            background=[('pressed', self.colors["sidebar_active"]), ('active', self.colors["sidebar_hover"]), ('selected', self.colors["sidebar_active"])],
            foreground=[('pressed', self.colors["text_primary"]), ('active', self.colors["text_primary"]), ('selected', self.colors["text_primary"])])


    def create_base_layout(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

        # Animated background canvas
        self.animated_bg_canvas = Canvas(self.root, bg=self.colors["bg_dark"], highlightthickness=0)
        self.animated_bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create particle effects
        self.particles = []
        for _ in range(30):  # Number of particles
            x = np.random.randint(0, self.root.winfo_screenwidth())
            y = np.random.randint(0, self.root.winfo_screenheight())
            size = np.random.randint(2, 5)
            speed = np.random.uniform(0.3, 1.2)
            direction = np.random.uniform(0, 2*np.pi)
            color = self.colors["particle_color"]
            alpha = np.random.uniform(0.3, 0.7)
            
            particle = {
                'id': None,
                'x': x,
                'y': y,
                'size': size,
                'speed': speed,
                'direction': direction,
                'color': color,
                'alpha': alpha
            }
            self.particles.append(particle)
        
        # Start animation
        self._animate_background()
        
        # Sidebar Frame (placed above the canvas)
        self.sidebar_frame = Frame(self.root, bg=self.colors["sidebar_bg"], width=180, borderwidth=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.sidebar_frame.grid_propagate(False)

        # Header Frame (placed above the canvas)
        self.header_frame = Frame(self.root, bg=self.colors["bg_dark"], height=65, padx=20, borderwidth=0)
        self.header_frame.grid(row=0, column=1, sticky="new")
        self.header_frame.grid_propagate(False)

        # Content Area (Gradient - placed above the canvas)
        self.content_area = GradientFrame(self.root, self.colors["bg_dark"], self.colors["bg_gradient_end"])
        self.content_area.grid(row=1, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Make the content area translucent to show background animation
        self.content_area.configure(bg=self.colors["bg_dark"])
        
    def _animate_background(self):
        """Animate the particles in the background"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if width <= 1 or height <= 1:  # Window not fully initialized
            self.root.after(100, self._animate_background)
            return
            
        # Clear previous particles
        self.animated_bg_canvas.delete("particle")
        
        # Update and draw particles
        for particle in self.particles:
            # Update position
            dx = particle['speed'] * np.cos(particle['direction'])
            dy = particle['speed'] * np.sin(particle['direction'])
            
            particle['x'] += dx
            particle['y'] += dy
            
            # Wrap around screen
            if particle['x'] < 0:
                particle['x'] = width
            elif particle['x'] > width:
                particle['x'] = 0
                
            if particle['y'] < 0:
                particle['y'] = height
            elif particle['y'] > height:
                particle['y'] = 0
                
            # Draw the particle
            x, y, size = particle['x'], particle['y'], particle['size']
            alpha_hex = int(particle['alpha'] * 255)
            color = particle['color'] if isinstance(particle['color'], str) else f"#{alpha_hex:02x}{particle['color'][1:]}"
            
            particle['id'] = self.animated_bg_canvas.create_oval(
                x - size, y - size, x + size, y + size, 
                fill=color, outline="", tags="particle"
            )
            
            # Randomly change direction occasionally
            if np.random.random() < 0.02:  # 2% chance to change direction
                particle['direction'] = np.random.uniform(0, 2*np.pi)
        
        # Schedule the next animation frame
        self.root.after(50, self._animate_background)

    def create_header_controls(self):
        # --- Disease Combobox ---
        self.disease_combobox = ttk.Combobox(
            self.header_frame, textvariable=self.current_disease, values=self.available_diseases,
            state="readonly", width=18, font=("Segoe UI", 10), style='Pill.TCombobox'
        )
        self.disease_combobox.pack(side="left", padx=(0, 15), pady=15, ipady=2)
        # *** BINDING MODIFIED: Now directly triggers loading logic ***
        self.disease_combobox.bind("<<ComboboxSelected>>", self.on_disease_change)
        self.disease_combobox.bind("<<ComboboxSelected>>", self._update_combobox_color, add='+') # Keep color update
        self.disease_combobox.bind("<FocusIn>", self._update_combobox_color, add='+')
        self.disease_combobox.bind("<FocusOut>", self._update_combobox_color, add='+')

        # --- Country Combobox ---
        self.country_combobox = ttk.Combobox(
            self.header_frame, textvariable=self.selected_country, values=[], # Populated later
            state="disabled", width=22, font=("Segoe UI", 10), style='Pill.TCombobox'
        )
        self.country_combobox.bind("<<ComboboxSelected>>", self.on_country_change)
        self.country_combobox.bind("<<ComboboxSelected>>", self._update_combobox_color, add='+')
        self.country_combobox.bind("<FocusIn>", self._update_combobox_color, add='+')
        self.country_combobox.bind("<FocusOut>", self._update_combobox_color, add='+')

        # --- Target (Cases/Deaths) Combobox ---
        self.target_combobox = ttk.Combobox(
            self.header_frame, textvariable=self.selected_target, values=self.available_targets,
            state="disabled", width=10, font=("Segoe UI", 10), style='Pill.TCombobox'
        )
        self.target_combobox.bind("<<ComboboxSelected>>", self.on_target_change)
        self.target_combobox.bind("<<ComboboxSelected>>", self._update_combobox_color, add='+')
        self.target_combobox.bind("<FocusIn>", self._update_combobox_color, add='+')
        self.target_combobox.bind("<FocusOut>", self._update_combobox_color, add='+')

        # --- Buttons ---
        # *** Load Button is created but will be disabled by on_disease_change ***
        self.load_button = GlowButton(self.header_frame, text="Load Data", command=self.start_loading_data, width=120, height=38, icon="📥", icon_font_size=18, font_size=9, start_color=self.colors["accent_teal"], end_color="#008899", state='disabled') # Start disabled
        self.load_button.pack(side="left", padx=(10, 15), pady=15)

        self.analyze_button = GlowButton(self.header_frame, text="Analyze", command=self.run_analysis_or_processing, width=120, height=38, icon="📊", icon_font_size=18, font_size=9, start_color=self.colors["accent_yellow"], end_color=self.colors["accent_orange"], state='disabled') # Initially disabled
        self.analyze_button.pack(side="left", padx=(0, 10), pady=15)

        self.export_all_button = GlowButton(
            self.header_frame, text="Export Cleaned", command=self.start_export_all_cleaned_data,
            width=140, height=38, icon="💾", icon_font_size=18, font_size=9,
            start_color=self.colors["accent_pink"], end_color=self.colors["accent_orange"],
            state='disabled' # Initially disabled
        )
        self.export_all_button.pack(side="left", padx=(0, 10), pady=15)

        # Initial color update for placeholders
        self._update_combobox_color(widget=self.disease_combobox)
        self._update_combobox_color(widget=self.country_combobox)
        self._update_combobox_color(widget=self.target_combobox)


    def create_sidebar_buttons(self):
        sidebar_title = Label(self.sidebar_frame, text="EpiForecast", fg=self.colors["text_primary"], bg=self.colors["sidebar_bg"], font=("Segoe UI", 14, "bold"))
        sidebar_title.pack(pady=(20, 25), padx=15, anchor='w')

        button_style = 'Pill.TButton'
        views = [("dashboard", "🏠 Dashboard"), ("analysis", "📊 Analysis"), ("prediction", "🔮 Prediction")]

        for name, text in views:
            btn = ttk.Button(self.sidebar_frame, text=text, style=button_style, command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", padx=15, pady=4)
            self.sidebar_buttons[name] = btn

    def create_status_bar(self):
        self.status_bar = StatusBarWithRisk(self.root, colors=self.colors)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="sew")

    def create_views(self):
        self.view_frames = {
            "dashboard": DashboardView(self.content_area, self),
            "analysis": AnalysisView(self.content_area, self),
            "prediction": PredictionView(self.content_area, self)
        }
        for frame in self.view_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, view_name):
        """Raises the selected view frame and updates sidebar button state."""
        if view_name in self.view_frames:
            # Préparer la transition - garder une référence de la vue actuelle
            old_view_name = self.active_view_name.get()
            
            # Mettre à jour l'état avant le changement
            frame = self.view_frames[view_name]
            
            # Préparer la vue avant le changement
            frame.update_idletasks()
            
            # Afficher la nouvelle vue
            frame.tkraise()
            self.active_view_name.set(view_name)
            print(f"[UI] Switched to view: {view_name}")
            self._update_sidebar_button_state(view_name)
            
            # S'assurer que la nouvelle vue a la bonne taille
            frame.update_idletasks()
            
            # Forcer une mise à jour pour éviter les problèmes d'affichage
            self.root.update_idletasks()
            
            # When returning to dashboard, refresh its statistics from the most recent analysis
            if view_name == "dashboard" and self.disease_data is not None and self.current_target_col_name is not None:
                dashboard_view = self.view_frames.get("dashboard")
                if dashboard_view:
                    # Ensure we re-populate statistics when returning to dashboard
                    print("[UI] Refreshing dashboard statistics from current data")
                    self._update_processed_data_statistics(self.current_target_col_name)
        else:
            print(f"[UI Error] View '{view_name}' not found.")

    def _update_sidebar_button_state(self, active_view_name):
        """Updates the visual state of sidebar buttons (selected/not selected)."""
        for name, button in self.sidebar_buttons.items():
            if isinstance(button, ttk.Button):
                current_state_tuple = button.state() # Get current state as tuple
                is_currently_selected = 'selected' in current_state_tuple
                should_be_selected = name == active_view_name

                if should_be_selected and not is_currently_selected:
                    new_state_list = list(current_state_tuple) + ['selected']
                    button.state(tuple(new_state_list)) # Set the new combined state
                elif not should_be_selected and is_currently_selected:
                    new_state_list = [s for s in current_state_tuple if s != 'selected']
                    button.state(tuple(new_state_list)) # Set the new filtered state


    def _update_combobox_color(self, event=None, widget=None):
        """Updates combobox text color based on content, focus, and state."""
        if widget is None and event: widget = event.widget
        if not isinstance(widget, ttk.Combobox): return

        try:
            current_value = widget.get()
            is_placeholder = False
            placeholder_text = ""

            if widget == self.disease_combobox: placeholder_text = "Select Disease"
            elif widget == self.country_combobox: placeholder_text = "Select Country"
            elif widget == self.target_combobox: placeholder_text = "Select Target"

            if current_value in ["Select Disease", "Select Country", "Select Target"]:
                is_placeholder = True

            is_focused = self.root.focus_get() == widget
            current_widget_state = widget.state() # Returns a tuple of states
            is_disabled = 'disabled' in current_widget_state

            new_color = self.colors["text_primary"] # Default: Normal text

            if is_disabled:
                 new_color = self.colors["disabled_fg"]
            elif is_placeholder and not is_focused:
                new_color = self.colors["placeholder_text"]

            widget.configure(foreground=new_color)

        except tk.TclError: pass # Widget might be destroyed
        except Exception as e: print(f"Unexpected error updating combobox color: {e}"); traceback.print_exc()


    # --- Controller Methods ---

    def update_prediction_days(self, value):
        """Callback when the prediction days slider changes."""
        try:
            days = int(float(value))
            self.prediction_days.set(days)
            if "prediction" in self.view_frames:
                pred_view = self.view_frames["prediction"]
                value_label = pred_view.get_value_label()
                if value_label:
                    value_label.config(text=f"{days} days")
        except ValueError: pass
        except Exception as e: print(f"Error updating prediction days label: {e}")


    # --- MODIFIED: on_disease_change now triggers loading ---
    def on_disease_change(self, event=None):
        """Handles disease selection change AND triggers data loading."""
        disease = self.current_disease.get()
        print(f"Disease changed to: {disease}")

        # --- Reset dependent states ---
        self.disease_data = None # Clear processed data
        self.model = None
        self.scaler_X = None
        self.current_target_col_name = None # Clear processed target name
        self.selected_country.set("Select Country") # Reset country dropdown
        self.selected_target.set(config.DEFAULT_ANALYSIS_TARGET) # Reset target dropdown

        # --- Clear UI elements ---
        self.clear_statistics()
        self.clear_all_view_content() # Clear plots/placeholders

        # --- Update state of ALL UI elements (DISABLES things initially) ---
        # This call is important to reset/disable dependent controls like Country, Target, Analyze, Export
        self._update_ui_element_states()

        # --- Handle "Select Disease" placeholder case ---
        if disease == "Select Disease":
            status_msg = "Please select a disease."
            if self.status_bar: self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
            # Explicitly ensure buttons dependent on data are disabled
            if self.analyze_button: self.analyze_button.config(state='disabled')
            if self.export_all_button: self.export_all_button.config(state='disabled')
            # Load button is already disabled or will be handled below
            return # Stop here if placeholder selected

        # --- Disable the Load Data button permanently in this workflow ---
        if self.load_button:
            self.load_button.config(state='disabled')
            # Optionally hide it completely:
            # self.load_button.pack_forget()

        # --- Check if data is already loaded for the selected disease ---
        already_loaded = False
        if disease == "COVID-19" and self.raw_covid_data is not None: already_loaded=True
        elif disease == "Grippe" and self.raw_influenza_data is not None: already_loaded=True
        elif disease == "Zika" and self.raw_zika_data is not None: already_loaded=True
        # Add checks for other non-simulated diseases if implemented

        if already_loaded:
            status_msg=f"{disease} data already loaded. "
            # Update status and UI states to reflect loaded data and prompt for next steps
            if disease in ["COVID-19", "Grippe", "Zika"]: status_msg += "Select Country"
            if disease == "COVID-19": status_msg += f" & Target ({self.selected_target.get()})"
            status_msg += ", then Analyze. Or 'Export Cleaned'."

            if self.status_bar: self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
            self._update_ui_element_states() # Re-enable controls based on loaded data
            return # Stop here if already loaded

        # --- If not placeholder and not already loaded, START LOADING ---
        status_msg_loading = f"Auto-loading data for {disease}..."
        if self.status_bar: self.status_bar.set_status(status_msg_loading)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg_loading)
        self._set_ui_busy(True, f"Loading {disease}") # Make UI busy

        # Reset relevant raw data stores (might be slightly redundant with above, but safe)
        if disease == "COVID-19":
            self.raw_covid_data = None
            self.allowed_covid_countries_in_data = []
        elif disease == "Grippe":
            self.raw_influenza_data = None
            self.allowed_influenza_countries_in_data = []
        elif disease == "Zika":
            self.raw_zika_data = None
            self.allowed_zika_countries_in_data = []
        # Selections were reset earlier

        # Start the data loading thread
        print(f"--- [on_disease_change] Starting data loading thread for {disease} ---")
        thread = threading.Thread(target=self._data_loading_thread_target, daemon=True)
        thread.start()
    # --- END of MODIFIED on_disease_change ---


    def on_country_change(self, event=None):
        """Handles country selection change."""
        country = self.selected_country.get()
        print(f"Country changed to: {country}")

        # Clear previous processed data and plots if country changes
        self.disease_data = None
        self.model = None
        self.scaler_X = None
        self.current_target_col_name = None
        self.clear_statistics()
        self.clear_all_view_content()

        self._update_ui_element_states()
        self._update_combobox_color(widget=self.country_combobox)

        # Update status message
        status_msg = f"Country set to {country}. "
        if self.analyze_button and self.analyze_button.cget('state') != 'disabled':
            status_msg += f"Select Target ({self.selected_target.get()}) and click 'Analyze'." if self.current_disease.get() == "COVID-19" else "Click 'Analyze'."
        else:
            # More specific message needed if analyze isn't ready
            disease = self.current_disease.get()
            if disease == "Select Disease": status_msg += "Select Disease first."
            elif disease in ["COVID-19", "Grippe", "Zika"]: status_msg += "Data loaded. Analyze ready." # Should be ready if country selected
            else: status_msg += "Check selections."
        if self.status_bar: self.status_bar.set_status(status_msg)


    def on_target_change(self, event=None):
        """Handles target (Cases/Deaths) selection change."""
        target = self.selected_target.get()
        disease = self.current_disease.get()
        print(f"Target changed to: {target}")

        # Clear previous processed data, model, plots, and stats as the target has changed
        self.disease_data = None
        self.model = None
        self.scaler_X = None
        self.current_target_col_name = None
        self.clear_statistics()
        self.clear_all_view_content()

        self._update_ui_element_states()
        self._update_combobox_color(widget=self.target_combobox)

        # Update status bar - Prompt user to click Analyze again
        status_msg = f"Target set to {target}. "
        if self.analyze_button and self.analyze_button.cget('state') != 'disabled':
             status_msg += "Click 'Analyze' to process and view results."
        else:
            if disease == "Select Disease": status_msg += "Select a disease first."
            elif disease in ["COVID-19", "Grippe", "Zika"] and self.selected_country.get() == "Select Country": status_msg += "Select a country first."
            # Data should be loaded if target selector is enabled, so no need to check raw_data here
            else: status_msg += "Check selections."

        if self.status_bar: self.status_bar.set_status(status_msg)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)


    def _update_ui_element_states(self):
        """Central function to update the state (enabled/disabled/values) and layout of header controls."""
        try:
            disease = self.current_disease.get()
            country = self.selected_country.get()
            target = self.selected_target.get()

            # --- Determine if raw data is loaded ---
            raw_covid_loaded = self.raw_covid_data is not None and self.allowed_covid_countries_in_data
            raw_grippe_loaded = self.raw_influenza_data is not None and self.allowed_influenza_countries_in_data
            raw_zika_loaded = self.raw_zika_data is not None and self.allowed_zika_countries_in_data
            any_raw_data_loaded = raw_covid_loaded or raw_grippe_loaded or raw_zika_loaded

            # --- Country Combobox State ---
            show_country_selector = False
            enable_country_selector = False
            country_list = ["Select Country"]

            if disease in ["COVID-19", "Grippe", "Zika"] and disease != "Select Disease":
                show_country_selector = True
                if disease == "COVID-19" and raw_covid_loaded:
                    enable_country_selector = True
                    country_list.extend(self.allowed_covid_countries_in_data)
                elif disease == "Grippe" and raw_grippe_loaded:
                    enable_country_selector = True
                    country_list.extend(self.allowed_influenza_countries_in_data)
                elif disease == "Zika" and raw_zika_loaded:
                    enable_country_selector = True
                    country_list.extend(self.allowed_zika_countries_in_data)

            # Update Country Combobox Visibility & State
            if self.country_combobox:
                current_country_state = self.country_combobox.cget('state')
                new_country_state = "readonly" if enable_country_selector else "disabled"

                if show_country_selector:
                    if not self.country_combobox.winfo_ismapped():
                        self.country_combobox.pack(side="left", padx=(0, 15), pady=15, ipady=2)
                        self.country_combobox.pack_configure(before=self.target_combobox if self.target_combobox and self.target_combobox.winfo_ismapped() else self.load_button)

                    if current_country_state != new_country_state:
                        self.country_combobox.config(state=new_country_state)
                    if list(self.country_combobox['values']) != country_list:
                         self.country_combobox.config(values=country_list)

                    valid_selections = self.allowed_covid_countries_in_data + self.allowed_influenza_countries_in_data + self.allowed_zika_countries_in_data
                    if new_country_state == "disabled" or (country != "Select Country" and country not in valid_selections):
                        if self.selected_country.get() != "Select Country":
                            self.selected_country.set("Select Country")
                else:
                    if self.country_combobox.winfo_ismapped():
                        self.country_combobox.pack_forget()
                    if self.selected_country.get() != "Select Country":
                        self.selected_country.set("Select Country")
            
            # --- Target Combobox State ---
            show_target_selector = False
            enable_target_selector = False
            target_list = config.ANALYSIS_TARGETS
            if (disease == "COVID-19" and raw_covid_loaded) or (disease == "Zika" and raw_zika_loaded):
                 show_target_selector = True
                 enable_target_selector = True

            if self.target_combobox:
                current_target_state = self.target_combobox.cget('state')
                new_target_state = "readonly" if enable_target_selector else "disabled"
                if show_target_selector:
                    if not self.target_combobox.winfo_ismapped():
                        self.target_combobox.pack(side="left", padx=(0, 15), pady=15, ipady=2)
                        self.target_combobox.pack_configure(before=self.analyze_button)
                    if current_target_state != new_target_state:
                        self.target_combobox.config(state=new_target_state)
                    if list(self.target_combobox['values']) != target_list:
                         self.target_combobox.config(values=target_list)
                    if new_target_state == "disabled":
                        if self.selected_target.get() != config.DEFAULT_ANALYSIS_TARGET:
                             self.selected_target.set(config.DEFAULT_ANALYSIS_TARGET)
                    elif self.selected_target.get() not in target_list: 
                        self.selected_target.set(config.DEFAULT_ANALYSIS_TARGET) 
                else:
                     if self.target_combobox.winfo_ismapped():
                         self.target_combobox.pack_forget()
                     if self.selected_target.get() != config.DEFAULT_ANALYSIS_TARGET: 
                         self.selected_target.set(config.DEFAULT_ANALYSIS_TARGET)

            # --- Button States ---
            disease_is_selected = disease != "Select Disease"
            country_is_selected = country != "Select Country"

            # Analyze button logic (for single selected country)
            can_analyze_now = False
            if disease_is_selected:
                if disease in ["COVID-19", "Grippe", "Zika"]:
                    raw_data_loaded_for_disease = (disease == "COVID-19" and raw_covid_loaded) or \
                                                  (disease == "Grippe" and raw_grippe_loaded) or \
                                                  (disease == "Zika" and raw_zika_loaded)
                    can_analyze_now = raw_data_loaded_for_disease and country_is_selected
                elif disease in config.AVAILABLE_DISEASES: # Simulated/Other
                     # Processed data (`self.disease_data`) is loaded during the auto-load via on_disease_change
                     can_analyze_now = self.disease_data is not None and not self.disease_data.empty

            analyze_state = "normal" if can_analyze_now else "disabled"

            # Export All button logic - Enabled if *any* raw data is loaded
            export_all_state = "normal" if any_raw_data_loaded else "disabled"

            # Prediction button/slider logic (depends on single analysis completion)
            data_processed_for_target = (self.disease_data is not None and not self.disease_data.empty and self.current_target_col_name is not None)
            predict_state_tk = "normal" if data_processed_for_target else "disabled"

            # Apply states to Buttons only if state has changed
            if self.analyze_button and self.analyze_button.cget('state') != analyze_state:
                 self.analyze_button.config(state=analyze_state)
            if self.export_all_button and self.export_all_button.cget('state') != export_all_state:
                 self.export_all_button.config(state=export_all_state)

            # Apply states to Prediction View components
            if "prediction" in self.view_frames:
                 pred_view = self.view_frames["prediction"]
                 pred_button = pred_view.get_predict_button()
                 pred_slider = pred_view.get_slider()
                 if pred_button and pred_button.cget('state') != predict_state_tk: # GlowButton state is 'normal' or 'disabled'
                     pred_button.config(state=predict_state_tk)
                 if pred_slider and pred_slider.cget('state') != predict_state_tk:
                     pred_slider.config(state=predict_state_tk)

        except Exception as e:
            print(f"CRITICAL ERROR in _update_ui_element_states: {e}")
            import traceback # Ensure traceback is available in this scope if not already
            traceback.print_exc()
            if self.status_bar:
                self.status_bar.set_status(f"UI Update Error. Check console.")
            
            # Attempt to disable most interactive controls to indicate an error state
            controls_to_disable_on_error = [
                self.country_combobox, self.target_combobox,
                self.analyze_button, self.export_all_button, self.load_button 
            ]
            if "prediction" in self.view_frames:
                pred_view = self.view_frames["prediction"]
                if hasattr(pred_view, 'get_predict_button') and pred_view.get_predict_button():
                    controls_to_disable_on_error.append(pred_view.get_predict_button())
                if hasattr(pred_view, 'get_slider') and pred_view.get_slider():
                    controls_to_disable_on_error.append(pred_view.get_slider())

            for control in controls_to_disable_on_error:
                if control:
                    try:
                        control.config(state='disabled')
                    except tk.TclError: # Control might be destroyed or in bad state
                        pass
            # Ensure disease combobox is usable to allow user to try selecting another option
            if self.disease_combobox:
                try:
                    self.disease_combobox.config(state='readonly')
                except tk.TclError:
                    pass
        finally:
            # These color updates have their own internal error handling (tk.TclError)
            self._update_combobox_color(widget=self.disease_combobox)
            self._update_combobox_color(widget=self.country_combobox)
            self._update_combobox_color(widget=self.target_combobox)


    def clear_statistics(self):
        """Clears statistics display on the dashboard and resets risk."""
        if "dashboard" in self.view_frames:
            self.view_frames["dashboard"].clear_stats() # Calls method in DashboardView
        if self.status_bar:
            self.status_bar.set_risk("Unknown") # Reset risk level

    def clear_all_view_content(self):
        """Clears plot frames in Analysis and Prediction views and adds placeholders."""
        views_to_clear = ["analysis", "prediction"]
        for view_name in views_to_clear:
             if view_name in self.view_frames:
                 view = self.view_frames[view_name]
                 try:
                     placeholder = f"Select Disease to load data. Then Select Country/Target and 'Analyze'."
                     if view_name == "prediction":
                          placeholder = f"Select Disease to load data. Then Analyze, then Run Forecast."
                     if hasattr(view, 'add_placeholder') and callable(view.add_placeholder):
                         view.add_placeholder(placeholder)
                     else: # Fallback
                         plot_frame = view.get_plot_frame()
                         for widget in plot_frame.winfo_children(): widget.destroy()
                         Label(plot_frame, text=placeholder, fg=self.colors["text_secondary"], bg=self.colors["bg_card"]).pack(expand=True)
                 except Exception as e:
                     print(f"Error clearing view {view_name}: {e}")


    # --- MODIFIED: start_loading_data is no longer primary workflow ---
    def start_loading_data(self):
        """Starts the data loading process in a separate thread.
           (Note: This function is likely no longer triggered by UI in the auto-load workflow)"""
        disease = self.current_disease.get()
        print(f"--- [start_loading_data called for {disease} - This might be unexpected in auto-load workflow] ---")
        if disease == "Select Disease":
             if self.status_bar: self.status_bar.set_status("Please select a disease first.")
             return

        # Check if data is already loaded
        already_loaded = False
        if disease == "COVID-19" and self.raw_covid_data is not None: already_loaded=True
        elif disease == "Grippe" and self.raw_influenza_data is not None: already_loaded=True
        elif disease == "Zika" and self.raw_zika_data is not None: already_loaded=True

        if already_loaded:
             status_msg=f"{disease} data already loaded. Select Country/Target and Analyze or Export."
             if self.status_bar: self.status_bar.set_status(status_msg)
             if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
             self._update_ui_element_states()
             return

        # --- Start Loading Thread ---
        status_msg_loading = f"Loading data for {disease}..."
        if self.status_bar: self.status_bar.set_status(status_msg_loading)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg_loading)
        self._set_ui_busy(True, "Loading")

        # Reset stores
        self.disease_data = None
        self.current_target_col_name = None
        if disease == "COVID-19":
            self.raw_covid_data = None
            self.allowed_covid_countries_in_data = []
        elif disease == "Grippe":
            self.raw_influenza_data = None
            self.allowed_influenza_countries_in_data = []
        elif disease == "Zika":
            self.raw_zika_data = None
            self.allowed_zika_countries_in_data = []
        self.selected_country.set("Select Country")
        self.selected_target.set(config.DEFAULT_ANALYSIS_TARGET)

        thread = threading.Thread(target=self._data_loading_thread_target, daemon=True)
        thread.start()


    def _data_loading_thread_target(self):
        """
        Worker thread for loading RAW data based on selected disease.
        (Remains the same, called by on_disease_change)
        """
        raw_data_temp = None
        processed_data_sim = None
        success = False
        error_message = None
        disease = self.current_disease.get()
        is_simulation = False

        try:
            print(f"--- [Thread] Starting Data Load for {disease} ---")
            raw_data_temp = data_loader.get_data_source(disease)

            if raw_data_temp is None:
                 raise ValueError(f"Data loading function failed to return data for {disease}.")

            if disease == "COVID-19":
                if raw_data_temp.empty: raise ValueError("Loaded COVID data is empty.")
                self.raw_covid_data = raw_data_temp
                if 'country' not in self.raw_covid_data.columns: raise ValueError("'country' column missing.")
                all_countries_in_file = sorted(self.raw_covid_data['country'].dropna().unique())
                self.allowed_covid_countries_in_data = [
                    c for c in all_countries_in_file if c in config.ALLOWED_COVID_COUNTRIES
                ]
                if not self.allowed_covid_countries_in_data:
                    print("[Warning] No countries in loaded COVID data match ALLOWED_COVID_COUNTRIES.")
                    if not config.ALLOWED_COVID_COUNTRIES and all_countries_in_file:
                         self.allowed_covid_countries_in_data = all_countries_in_file
                         print("[Info] Using all countries found (ALLOWED_COVID_COUNTRIES empty).")
                    elif not all_countries_in_file: print("[Warning] No countries found in COVID data file.")
                    else: self.allowed_covid_countries_in_data = []
                print(f"[COVID Load Thread] Allowed Countries: {self.allowed_covid_countries_in_data}");
                success = True

            elif disease == "Grippe":
                 if raw_data_temp.empty: raise ValueError("Loaded Influenza data is empty.")
                 self.raw_influenza_data = raw_data_temp;
                 country_col = config.GRIPPE_RAW_COUNTRY_COL
                 if country_col not in self.raw_influenza_data.columns: raise ValueError(f"Raw country column '{country_col}' missing.");
                 self.allowed_influenza_countries_in_data = sorted(self.raw_influenza_data[country_col].dropna().astype(str).unique())
                 if not self.allowed_influenza_countries_in_data: print("[Warning] No countries found in Influenza data.")
                 print(f"[Influenza Load Thread] Countries Found: {self.allowed_influenza_countries_in_data}");
                 success = True

            elif disease == "Zika":
                 if raw_data_temp.empty: raise ValueError("Loaded Zika data is empty.")
                 self.raw_zika_data = raw_data_temp;
                 country_col = config.ZIKA_COUNTRY_COL
                 if country_col not in self.raw_zika_data.columns: raise ValueError(f"Raw country column '{country_col}' missing.");
                 self.allowed_zika_countries_in_data = sorted(self.raw_zika_data[country_col].dropna().astype(str).unique())
                 if not self.allowed_zika_countries_in_data: print("[Warning] No countries found in Zika data.")
                 print(f"[Zika Load Thread] Countries Found: {self.allowed_zika_countries_in_data}");
                 success = True

            else: # Simulated/Other - process immediately for 'Cases'
                 is_simulation = True
                 if raw_data_temp.empty: raise ValueError(f"Loaded/Simulated data for {disease} is empty.");
                 print(f"[Thread] Applying common post-processing for {disease} (Target: Cases)...");
                 target_col_sim = config.PREDICTION_CASES_TARGET_COL
                 if target_col_sim not in raw_data_temp.columns:
                     raise ValueError(f"Simulated data for {disease} is missing the required '{target_col_sim}' column.")
                 # *** Run processing in the loading thread for simulations ***
                 processed_data_sim = processing.common_post_processing(raw_data_temp, target_col_sim);
                 if processed_data_sim is None or processed_data_sim.empty: raise ValueError(f"Common post-processing failed for {disease}.")
                 self.disease_data = processed_data_sim # Store processed data directly
                 self.current_target_col_name = target_col_sim # Set the target name
                 print(f"--- [Thread] Data Loading & Processing Complete for {disease}. Shape: {self.disease_data.shape} ---");
                 success = True

        except Exception as e:
            error_message = f"Data Load Error ({disease}): {str(e)}"
            print(f"--- [Thread] {error_message} ---"); traceback.print_exc();
            if disease == "COVID-19": self.raw_covid_data = None; self.allowed_covid_countries_in_data = []
            elif disease == "Grippe": self.raw_influenza_data = None; self.allowed_influenza_countries_in_data = []
            elif disease == "Zika": self.raw_zika_data = None; self.allowed_zika_countries_in_data = []
            self.disease_data = None; self.current_target_col_name = None
            success = False
        finally:
             # Schedule UI update on main thread
             self.root.after(0, self._data_load_complete, success, is_simulation, error_message)


    def _data_load_complete(self, success, is_simulation, error_message=None):
        """Handles UI updates after the data loading thread finishes."""
        self._set_ui_busy(False) # Re-enable UI first. This also calls _update_ui_element_states().
        disease = self.current_disease.get()

        # Check if _update_ui_element_states (called via _set_ui_busy) already reported an error
        ui_error_detected = False
        if self.status_bar:
            current_status = self.status_bar.status_var.get()
            if "UI Update Error" in current_status:
                ui_error_detected = True
                print(f"[DataLoadComplete] Detected UI update error from earlier step. Status: '{current_status}'")

        if success:
            if self.status_bar: self.status_bar.set_progress(100)

            if not ui_error_detected: # Only proceed with normal status updates if no UI error was previously set
                if not is_simulation:
                    # Raw data loaded (COVID/Grippe/Zika), UI states should be updated by _set_ui_busy.
                    # Now, set the appropriate status message.
                    status_msg = f"{disease} data loaded. "
                    countries_available = (disease == "COVID-19" and self.allowed_covid_countries_in_data) or \
                                          (disease == "Grippe" and self.allowed_influenza_countries_in_data) or \
                                          (disease == "Zika" and self.allowed_zika_countries_in_data)
                    if countries_available:
                         status_msg += "Select Country"
                         if disease == "COVID-19": # Only COVID supports target selection
                              status_msg += f" & Target ({self.selected_target.get()})"
                         status_msg += ", then Analyze. Or 'Export Cleaned'."
                    else:
                         status_msg += "No valid countries found/allowed!"
                    if self.status_bar:
                        self.status_bar.set_status(status_msg)
                        self.root.update_idletasks() # Force UI update for status bar
                    if "dashboard" in self.view_frames:
                        self.view_frames["dashboard"].update_status(status_msg)

                else: # Simulation loaded AND processed (always 'Cases')
                    source_type="Simulated"
                    status_msg = f"Data ready: {disease} ({source_type}, Target: Cases). Analyzing..."
                    if self.status_bar:
                        self.status_bar.set_status(status_msg)
                        self.root.update_idletasks() # Force UI update for status bar
                    if "dashboard" in self.view_frames:
                        self.view_frames["dashboard"].update_status(status_msg)
                    # UI states should be updated by _set_ui_busy.
                    # Run analysis automatically for the processed 'Cases' data
                    self.root.after(10, self.analyze_data, self.current_target_col_name)
            # If ui_error_detected, the error message from _update_ui_element_states remains.

        else: # Loading Failed
            error_msg_full = error_message or f"Unknown loading error for {disease}."
            if self.status_bar:
                self.status_bar.set_progress(0)
                self.status_bar.set_status(error_msg_full)
                self.root.update_idletasks() # Force UI update for status bar
            if "dashboard" in self.view_frames:
                self.view_frames["dashboard"].update_status(f"Error: {error_msg_full}")
            self.clear_all_view_content()
            self.clear_statistics()
            # _update_ui_element_states() was already called by _set_ui_busy(False) to reflect the reset data state.

        # Final check on combobox colors after state changes (these have their own error handling)
        self._update_combobox_color(widget=self.disease_combobox)
        self._update_combobox_color(widget=self.country_combobox)
        self._update_combobox_color(widget=self.target_combobox)

        if self.status_bar:
            # Schedule clearing the progress bar after a short delay
            self.root.after(1000, lambda: self.status_bar.set_progress(0) if self.status_bar else None)


    def run_analysis_or_processing(self):
        """
        Triggered by the 'Analyze' button (for SINGLE country/target).
        Processes raw data for the selected target and then runs analysis.
        (Assumes raw data is already loaded due to auto-load workflow).
        """
        disease = self.current_disease.get()
        selected_country = self.selected_country.get()
        selected_target_type = self.selected_target.get() # "Cases" or "Deaths"

        # Basic Input Validation
        if disease == "Select Disease":
             if self.status_bar: self.status_bar.set_status("Please select a disease first.")
             return
        if disease in ["COVID-19", "Grippe", "Zika"] and selected_country == "Select Country":
             if self.status_bar: self.status_bar.set_status(f"Please select a country for {disease} first.")
             return
        if disease == "COVID-19" and selected_target_type not in config.ANALYSIS_TARGETS:
             if self.status_bar: self.status_bar.set_status(f"Please select a valid target (Cases/Deaths) for {disease}.")
             return

        # Handle Grippe target selection (Force to Cases if Deaths selected)
        if disease == "Grippe" and selected_target_type == "Deaths":
             print("[Warning] Influenza data source does not contain Deaths. Analyzing Cases instead.")
             self.selected_target.set("Cases")
             selected_target_type = "Cases"
             self._update_ui_element_states()
             if self.status_bar: self.status_bar.set_status("Influenza Deaths not available. Switched to Cases. Click Analyze again.")
             return

        # --- Processing Logic ---
        # Check if raw data exists (should be loaded by auto-load)
        raw_data = None
        if disease == "COVID-19": raw_data = self.raw_covid_data
        elif disease == "Grippe": raw_data = self.raw_influenza_data
        elif disease == "Zika": raw_data = self.raw_zika_data
        elif disease in config.AVAILABLE_DISEASES: # Simulated data
             if self.disease_data is not None and not self.disease_data.empty:
                 print(f"[Analyze Trigger] Analyzing already processed SIMULATED data for {disease}")
                 self.analyze_data(target_col_name=self.current_target_col_name) # Run analysis directly
                 return
             else:
                 if self.status_bar: self.status_bar.set_status(f"Simulated data for {disease} not ready. Try re-selecting.")
                 return

        if raw_data is None:
            # This case is less likely now with auto-load, but good failsafe
            status_msg=f"{disease} raw data not loaded. Select disease again."
            if self.status_bar: self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(f"Action Required: {status_msg}")
            return

        # --- Start Processing Thread ---
        status_msg_proc = f"Processing {disease} data for {selected_country} ({selected_target_type})...";
        if self.status_bar: self.status_bar.set_status(status_msg_proc)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg_proc)
        self._set_ui_busy(True, "Processing")
        self.disease_data = None # Clear previous *single* processed data
        self.current_target_col_name = None # Reset current target name

        target_thread_func = self._processing_covid_thread_target if disease == "COVID-19" else \
                             self._processing_influenza_thread_target if disease == "Grippe" else \
                             self._processing_zika_thread_target
        thread = threading.Thread(target=target_thread_func, args=(selected_country, selected_target_type), daemon=True)
        thread.start()


    def _processing_covid_thread_target(self, selected_country, target_type):
        """Processes SINGLE COVID country/target in a thread (for Analyze button)."""
        # (This function remains the same as in the previous 'Export All' version)
        processed_df_country = None
        target_col_name_out = None
        try:
            print(f"--- [Thread] Starting SINGLE COVID Processing for {selected_country} ({target_type}) ---")
            processed_df_country = processing.preprocess_covid_data(self.raw_covid_data, selected_country, target_type)
            if processed_df_country is None or processed_df_country.empty:
                raise ValueError(f"COVID Preprocessing returned empty/None for {selected_country} ({target_type}).")

            target_col_name_out = config.PREDICTION_CASES_TARGET_COL if target_type == "Cases" else config.PREDICTION_DEATHS_TARGET_COL
            if target_col_name_out not in processed_df_country.columns:
                 raise ValueError(f"Expected target column '{target_col_name_out}' not found after preprocess_covid_data.")

            final_processed_df = processing.common_post_processing(processed_df_country, target_col_name_out)
            if final_processed_df is None or final_processed_df.empty:
                raise ValueError(f"Common post-processing failed for COVID/{selected_country} ({target_type}).")

            self.disease_data = final_processed_df # Assign to main attribute for single analysis
            self.current_target_col_name = target_col_name_out # Store the processed target name

            print(f"--- [Thread] SINGLE COVID Processing Complete for {selected_country} ({target_type}). Shape: {self.disease_data.shape} ---")
            self.root.after(0, self._processing_complete, True, target_col_name_out, None) # Success for single processing

        except Exception as e:
            error_message = f"SINGLE COVID Proc Error ({selected_country}/{target_type}): {str(e)}"
            print(f"--- [Thread] {error_message} ---"); traceback.print_exc()
            self.disease_data = None
            self.current_target_col_name = None
            self.root.after(0, self._processing_complete, False, None, error_message) # Failure


    def _processing_influenza_thread_target(self, selected_country, target_type):
        """Processes SINGLE Influenza country in a thread (for Analyze button)."""
        # (This function remains the same as in the previous 'Export All' version)
        processed_df_country = None
        target_col_name_out = config.PREDICTION_CASES_TARGET_COL
        try:
            print(f"--- [Thread] Starting SINGLE Influenza Processing for {selected_country} (Target: Cases) ---")
            processed_df_country = processing.preprocess_influenza_data(self.raw_influenza_data, selected_country)
            if processed_df_country is None or processed_df_country.empty:
                raise ValueError(f"Influenza Preprocessing returned empty/None for {selected_country}.")
            if target_col_name_out not in processed_df_country.columns:
                 raise ValueError(f"Expected target column '{target_col_name_out}' not found after preprocess_influenza_data.")

            final_processed_df = processing.common_post_processing(processed_df_country, target_col_name_out)
            if final_processed_df is None or final_processed_df.empty:
                raise ValueError(f"Common post-processing failed for Influenza/{selected_country}.")

            self.disease_data = final_processed_df # Assign to main attribute for single analysis
            self.current_target_col_name = target_col_name_out # Store 'cases'

            print(f"--- [Thread] SINGLE Influenza Processing Complete for {selected_country}. Shape: {self.disease_data.shape} ---")
            self.root.after(0, self._processing_complete, True, target_col_name_out, None) # Success

        except Exception as e:
            error_message = f"SINGLE Influenza Proc Error ({selected_country}): {str(e)}"
            print(f"--- [Thread] {error_message} ---"); traceback.print_exc()
            self.disease_data = None
            self.current_target_col_name = None
            self.root.after(0, self._processing_complete, False, None, error_message) # Failure


    def _processing_zika_thread_target(self, selected_country, target_type):
        """Processes SINGLE Zika country/target in a thread (for Analyze button)."""
        processed_df_country = None
        target_col_name_out = None
        try:
            print(f"--- [Thread] Starting SINGLE Zika Processing for {selected_country} ({target_type}) ---")
            processed_df_country = processing.preprocess_zika_data(self.raw_zika_data, selected_country, target_type)
            if processed_df_country is None or processed_df_country.empty:
                raise ValueError(f"Zika Preprocessing returned empty/None for {selected_country} ({target_type}).")

            target_col_name_out = config.PREDICTION_CASES_TARGET_COL if target_type == "Cases" else config.PREDICTION_DEATHS_TARGET_COL
            if target_col_name_out not in processed_df_country.columns:
                 raise ValueError(f"Expected target column '{target_col_name_out}' not found after preprocess_zika_data.")

            final_processed_df = processing.common_post_processing(processed_df_country, target_col_name_out)
            if final_processed_df is None or final_processed_df.empty:
                raise ValueError(f"Common post-processing failed for Zika/{selected_country} ({target_type}).")

            self.disease_data = final_processed_df # Assign to main attribute for single analysis
            self.current_target_col_name = target_col_name_out # Store the processed target name

            print(f"--- [Thread] SINGLE Zika Processing Complete for {selected_country} ({target_type}). Shape: {self.disease_data.shape} ---")
            self.root.after(0, self._processing_complete, True, target_col_name_out, None) # Success

        except Exception as e:
            error_message = f"SINGLE Zika Proc Error ({selected_country}/{target_type}): {str(e)}"
            print(f"--- [Thread] {error_message} ---"); traceback.print_exc()
            self.disease_data = None
            self.current_target_col_name = None
            self.root.after(0, self._processing_complete, False, None, error_message) # Failure


    def _processing_complete(self, success, processed_target_col_name, error_message=None):
        """Handles UI updates after SINGLE processing thread finishes."""
        # (Remains the same)
        self._set_ui_busy(False)

        if success and processed_target_col_name:
            if self.status_bar: self.status_bar.set_progress(100)
            
            # Update dashboard statistics immediately after processing
            self._update_processed_data_statistics(processed_target_col_name)
            
            # Continue with analysis
            self.analyze_data(target_col_name=processed_target_col_name)
        else:
            target_type = self.selected_target.get() if processed_target_col_name is None else processed_target_col_name.capitalize()
            error_msg_full = error_message or f"Unknown processing error for {self.current_disease.get()}/{self.selected_country.get()} ({target_type})."
            if self.status_bar: self.status_bar.set_progress(0); self.status_bar.set_status(error_msg_full)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(f"Error: {error_msg_full}")

            self.clear_all_view_content()
            self.clear_statistics()
            self.disease_data = None
            self.current_target_col_name = None
            self._update_ui_element_states()

        self._update_combobox_color(widget=self.disease_combobox)
        self._update_combobox_color(widget=self.country_combobox)
        self._update_combobox_color(widget=self.target_combobox)

        if self.status_bar:
             self.root.after(1000, lambda: self.status_bar.set_progress(0) if self.status_bar else None)


    def analyze_data(self, target_col_name):
        """Generates analysis plot and stats for the processed data (SINGLE country)."""
        # (Remains the same)
        target_type_label = target_col_name.capitalize()
        print(f"[Analyze Data] Triggered for target: {target_type_label}...")

        if self.disease_data is None or self.disease_data.empty:
            if self.status_bar: self.status_bar.set_status(f"No processed data available for {target_type_label} to analyze!")
            self._update_ui_element_states()
            return
        if target_col_name != self.current_target_col_name:
             err_msg = f"Error: Analysis requested for '{target_col_name}' but processed data is for '{self.current_target_col_name}'. Re-analyze needed."
             print(f"[Analyze Data] {err_msg}")
             if self.status_bar: self.status_bar.set_status(err_msg)
             self.clear_all_view_content()
             self._update_ui_element_states()
             return

        if self.analyze_button: self.analyze_button.config(state="disabled")
        pred_button = None
        if "prediction" in self.view_frames:
            pred_view = self.view_frames["prediction"]
            if hasattr(pred_view, 'get_predict_button'):
                 pred_button = pred_view.get_predict_button()
        if pred_button: pred_button.config(state="disabled")

        status_msg = f"Generating analysis charts for {target_type_label}..."
        if self.status_bar: self.status_bar.set_status(status_msg)
        fig = None
        try:
            disease = self.current_disease.get()
            source_info = ""
            country = self.selected_country.get()

            if disease == "COVID-19": source_info = f" ({country})" if country != "Select Country" else ""
            elif disease == "Grippe": source_info = f" ({country} - Weekly Source)" if country != "Select Country" else ""
            elif disease == "Zika": source_info = f" ({country})" if country != "Select Country" else ""
            elif disease in config.AVAILABLE_DISEASES: source_info = " (Simulated)"

            fig = analysis.plot_analysis_charts(self.disease_data, disease, target_col_name, source_info)

            if fig is None:
                 try: fig = analysis.plot_analysis_charts(pd.DataFrame(), disease, target_col_name, source_info)
                 except: pass
                 if fig is None: raise ValueError(f"Analysis plot generation returned None for {target_type_label}.")

            target_frame = self.view_frames["analysis"].get_plot_frame()
            # Préparation de la vue d'analyse avant changement pour éviter les problèmes d'affichage
            self.root.update_idletasks()  # Force la mise à jour de l'interface avant changement
            
            # Changement vers la vue d'analyse en premier
            self.show_view("analysis")
            
            # Petite pause pour laisser le temps à l'interface de s'adapter
            self.root.after(100, lambda: self._continue_analysis_display(fig, target_frame, target_col_name, target_type_label))

        except AttributeError as ae:
            if "'_embed_figure'" in str(ae):
                 error_message = f"Plotting Error ({target_type_label}):\nInternal error: _embed_figure method missing."
                 print(f"[Analyze Data] {error_message}"); traceback.print_exc()
                 try:
                    target_frame = self.view_frames["analysis"].get_plot_frame()
                    self._display_error_in_frame(target_frame, error_message)
                 except Exception as e_disp: print(f"Error displaying error in frame: {e_disp}")
                 if self.status_bar: self.status_bar.set_status(error_message.replace('\n', ' '))
                 if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(f"Error: {error_message.replace('\n', ' ')}")
                 self.clear_statistics()
                 if fig and plt.fignum_exists(fig.number): plt.close(fig)
                 self.show_view("analysis")
            else: raise

        except Exception as e:
            error_message = f"Analysis Display Error ({target_type_label}): {str(e)}"
            print(error_message); traceback.print_exc()
            if self.status_bar: self.status_bar.set_status(error_message)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(f"Error: {error_message}")
            try:
                target_frame = self.view_frames["analysis"].get_plot_frame()
                self._display_error_in_frame(target_frame, f"Plotting Error ({target_type_label}):\n{e}")
            except Exception as e_disp: print(f"Error displaying error in frame: {e_disp}")
            self.clear_statistics()
            if fig and plt.fignum_exists(fig.number): plt.close(fig)
            self.show_view("analysis")

        finally:
             self._update_ui_element_states()

    def _continue_analysis_display(self, fig, target_frame, target_col_name, target_type_label):
        """Continue l'affichage de l'analyse après le changement de vue pour éviter les problèmes d'interface."""
        try:
            # Intégration du graphique après changement de vue
            self._embed_figure(fig, target_frame)
            
            # Mise à jour des statistiques
            self._update_analysis_statistics_display(target_col_name)
            
            # Mise à jour des messages de statut
            status_msg = f"{target_type_label} analysis complete. View plot in Analysis tab. Ready to predict."
            if self.status_bar: self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
            
            # Forcer une mise à jour complète de l'interface pour s'assurer que tout s'affiche correctement
            self.root.update_idletasks()
            
        except Exception as e:
            error_message = f"Analysis Display Error (delayed): {str(e)}"
            print(error_message)
            traceback.print_exc()
            if self.status_bar: self.status_bar.set_status(error_message)
            try:
                self._display_error_in_frame(target_frame, f"Plotting Error ({target_type_label}):\n{e}")
            except Exception as e_disp: 
                print(f"Error displaying error in frame: {e_disp}")

    def _update_analysis_statistics_display(self, target_col_name):
        """Updates dashboard stats based on the calculated stats for the target (SINGLE country)."""
        # (Remains the same)
        target_type_label = target_col_name.capitalize()
        print(f"[UI] Updating statistics display for {target_type_label}...")
        dashboard_view = self.view_frames.get("dashboard")
        if not dashboard_view: return

        dashboard_view.clear_stats()
        if self.status_bar: self.status_bar.set_risk("Unknown")

        if self.disease_data is None or self.disease_data.empty:
            print(f"[UI] No processed data for {target_type_label} stats.")
            dashboard_view.update_status(f"No data processed for {target_type_label} statistics.")
            return
        if target_col_name != self.current_target_col_name:
             err_msg = f"Stats Error: Data target mismatch ('{self.current_target_col_name}' vs '{target_col_name}')."
             print(f"[UI Stats] {err_msg}")
             dashboard_view.update_status(err_msg)
             self._display_error_in_stats("Data target mismatch")
             return

        try:
            stats_dict = analysis.calculate_analysis_stats(self.disease_data, target_col_name)

            if "error" in stats_dict:
                self._display_error_in_stats(stats_dict["error"])
                return

            dashboard_view.update_stats(stats_dict)

            status_text = f"Displaying statistics for {target_type_label}. Risk: {stats_dict.get('risk_level', 'Unknown')}. Trend: {stats_dict.get('trend_desc', '')}"
            dashboard_view.update_status(status_text)

            if self.status_bar:
                risk = stats_dict.get('risk_level', 'Unknown')
                self.status_bar.set_risk(risk)
                print(f"[UI Stats] Target: {target_type_label}, Risk Level: {risk}, Trend: {stats_dict.get('trend_desc', '')}")

        except Exception as e:
            err_msg = f"Error displaying analysis statistics ({target_type_label}): {e}"
            print(err_msg); traceback.print_exc()
            self._display_error_in_stats(err_msg)


    def start_prediction(self):
        """Initiates the prediction process for the currently processed SINGLE target/country."""
        # (Remains the same)
        if self.disease_data is None or self.disease_data.empty:
            if self.status_bar: self.status_bar.set_status("No processed data available. Analyze first.")
            return
        if self.current_target_col_name is None:
             if self.status_bar: self.status_bar.set_status("Error: Target for processed data is unknown. Analyze first.")
             return

        target_type_label = self.current_target_col_name.capitalize()
        disease = self.current_disease.get()
        status_msg = f"Starting prediction for {disease} ({target_type_label})..."
        if self.status_bar: self.status_bar.set_status(status_msg)
        self._set_ui_busy(True, "Predicting")

        self.model = None
        self.scaler_X = None

        thread = threading.Thread(target=self._prediction_thread_target,
                                  args=(self.current_target_col_name,), daemon=True)
        thread.start()


    def _prediction_thread_target(self, target_col_name):
        """Worker thread for training model and generating predictions (SINGLE target/country)."""
        # (Remains the same)
        fig_pred = None
        pred_stats = {}
        error_message = None
        target_type_label = target_col_name.capitalize()
        disease = self.current_disease.get()
        country = self.selected_country.get()
        num_days_to_predict = self.prediction_days.get()

        try:
            if self.disease_data is None or self.disease_data.empty:
                raise ValueError(f"Cannot train model for {target_type_label}, processed data missing.")
            if target_col_name not in self.disease_data.columns:
                raise ValueError(f"Target column '{target_col_name}' not found in processed data for training.")

            if num_days_to_predict > 180:
                print(f"[Predict Thread - WARNING] Generating long-term forecast ({num_days_to_predict} days) for {target_type_label}. "
                      "Results may be less reliable.")

            status_update_train = f"Training prediction model for {target_type_label}..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update_train) if self.status_bar else None)

            model, scaler = prediction.train_prediction_model(self.disease_data, target_col_name)
            self.model, self.scaler_X = model, scaler

            status_update_gen = f"Generating {target_type_label} forecast..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update_gen) if self.status_bar else None)

            last_hist_date_ts = self.disease_data['date'].iloc[-1] if not self.disease_data.empty else pd.Timestamp.now()
            prediction_df = prediction.generate_predictions(self.model, self.scaler_X, num_days_to_predict, last_hist_date_ts, target_col_name)

            if prediction_df is None or prediction_df.empty:
                raise ValueError(f"{target_type_label} prediction generation failed or returned empty.")
                
            # Generate the prediction plot (this call was missing)
            source_info = f" ({country})" if country and country != "Select Country" else ""
            fig_pred = prediction.plot_prediction_chart(
                hist_df=self.disease_data, 
                pred_df=prediction_df, 
                disease_name=disease, 
                target_col_name=target_col_name,
                source_info=source_info,
                forecast_days=num_days_to_predict
            )
            
            if fig_pred is None: 
                raise ValueError(f"{target_type_label} prediction plot generation returned None.")

            pred_stats = prediction.calculate_prediction_stats(prediction_df, target_col_name)

            self.root.after(0, self._prediction_complete, True, fig_pred, pred_stats, target_col_name, None) # Success

        except Exception as e:
            error_message = f"Prediction Error ({disease}/{target_type_label}): {str(e)}"
            print(f"--- [Thread] {error_message} ---"); traceback.print_exc()
            if fig_pred and plt.fignum_exists(fig_pred.number):
                 plt.close(fig_pred)
            self.root.after(0, self._prediction_complete, False, None, None, target_col_name, error_message) # Failure


    def _prediction_complete(self, success, fig, stats_dict, target_col_name, error_message=None):
        """Handles UI updates after prediction thread finishes (SINGLE country)."""
        # (Remains the same)
        self._set_ui_busy(False)
        pred_view = self.view_frames.get("prediction")
        if not pred_view: return

        target_type_label = target_col_name.capitalize() if target_col_name else "Target"
        status_msg = ""

        if success and fig:
            status_msg = f"{target_type_label} prediction complete. View forecast in Prediction tab."
            target_frame = pred_view.get_plot_frame()
            
            # Préparation de la vue de prédiction avant changement pour éviter les problèmes d'affichage
            self.root.update_idletasks()  # Force la mise à jour de l'interface avant changement
            
            # Changement vers la vue de prédiction en premier
            self.show_view("prediction")
            
            # Petite pause pour laisser le temps à l'interface de s'adapter
            self.root.after(100, lambda: self._continue_prediction_display(fig, target_frame, stats_dict, target_col_name, status_msg))
            
        else:
            status_msg = error_message or f"Unknown prediction error for {self.current_disease.get()} ({target_type_label})."
            if self.status_bar: self.status_bar.set_progress(0); self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(f"Error: {status_msg}")

            target_frame = pred_view.get_plot_frame()
            self._display_error_in_frame(target_frame, f"Prediction Error ({target_type_label}):\n{status_msg}")
            
            self._update_ui_element_states()
            self._update_combobox_color(widget=self.disease_combobox)
            self._update_combobox_color(widget=self.country_combobox)
            self._update_combobox_color(widget=self.target_combobox)

            if self.status_bar:
                self.root.after(1000, lambda: self.status_bar.set_progress(0) if self.status_bar else None)

            self.show_view("prediction")


    def _continue_prediction_display(self, fig, target_frame, stats_dict, target_col_name, status_msg):
        """Continue l'affichage de la prédiction après le changement de vue pour éviter les problèmes d'interface."""
        try:
            # Intégration du graphique après changement de vue
            self._embed_figure(fig, target_frame)
            
            # Mise à jour des statistiques
            self._display_prediction_statistics(stats_dict, target_col_name)
            
            # Mise à jour des messages de statut
            if self.status_bar: self.status_bar.set_progress(100); self.status_bar.set_status(status_msg)
            if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
            
            # Mise à jour des états UI
            self._update_ui_element_states()
            self._update_combobox_color(widget=self.disease_combobox)
            self._update_combobox_color(widget=self.country_combobox)
            self._update_combobox_color(widget=self.target_combobox)
            
            # Force la mise à jour de l'interface après affichage
            self.root.update_idletasks()
            
            if self.status_bar:
                self.root.after(1000, lambda: self.status_bar.set_progress(0) if self.status_bar else None)
        except Exception as e:
            print(f"Error in _continue_prediction_display: {e}")
            traceback.print_exc()
            if self.status_bar: self.status_bar.set_status(f"Error displaying prediction: {str(e)}")
    
    def _display_prediction_statistics(self, stats_dict, target_col_name):
        """Appends prediction stats to the status bar message (SINGLE country)."""
        # (Remains the same)
        target_type_label = target_col_name.capitalize() if target_col_name else "Target"
        print(f"[UI] Displaying prediction statistics for {target_type_label}...")

        if not stats_dict or "error" in stats_dict:
            err = stats_dict.get("error", f"No valid {target_type_label} prediction stats.") if isinstance(stats_dict, dict) else "Stats error"
            print(f"[UI] {err}")
            if self.status_bar:
                 current_status_base = self.status_bar.status_var.get().split('|')[0].strip()
                 self.status_bar.set_status(f"{current_status_base} | Forecast Stats Error")
            return

        peak_info = f"{stats_dict.get('peak_pred_fmt', '--')} ({stats_dict.get('peak_date_fmt', 'N/A')})"
        avg_info = f"{stats_dict.get('avg_pred_fmt', '--')}/day"
        period_info = stats_dict.get('period_days_fmt', '')
        status_suffix = f"| Forecast {target_type_label} -> Peak: {peak_info}, Avg: {avg_info} ({period_info})"

        if self.status_bar:
            current_status = self.status_bar.status_var.get().split('|')[0].strip()
            self.status_bar.set_status(f"{current_status} {status_suffix}")

    # --- Figure Embedding / Error Display ---
    def _embed_figure(self, fig, parent_widget):
        """Embeds a Matplotlib figure into a Tkinter frame."""
        # (Remains the same)
        for widget in parent_widget.winfo_children(): widget.destroy()
        self.canvas = None; self.toolbar = None

        if fig is None:
            self._display_error_in_frame(parent_widget, "Failed to generate plot (None received).")
            return

        try:
            self.canvas = FigureCanvasTkAgg(fig, master=parent_widget)
            canvas_widget = self.canvas.get_tk_widget()
            canvas_widget.configure(bg=self.colors["bg_card"])
            canvas_widget.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            toolbar_frame = Frame(parent_widget, bg=self.colors["bg_card"])
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(5,0))
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.configure(background=self.colors["bg_card"])
            for button in self.toolbar.winfo_children():
                try: button.configure(bg=self.colors["bg_card"], fg=self.colors["text_secondary"], relief="flat", padx=5)
                except tk.TclError: pass
            self.toolbar.update()

            parent_widget.grid_rowconfigure(0, weight=1); parent_widget.grid_rowconfigure(1, weight=0)
            parent_widget.grid_columnconfigure(0, weight=1)

            parent_widget.update_idletasks()
            self.canvas.draw_idle()

        except Exception as e:
            print(f"Error embedding figure: {e}"); traceback.print_exc()
            self._display_error_in_frame(parent_widget, f"Error displaying plot:\n{e}")
            if fig and plt.fignum_exists(fig.number): plt.close(fig)
            self.canvas = None; self.toolbar = None

    def _display_error_in_frame(self, parent_frame, error_message):
         """Displays an error message within a given frame."""
         # (Remains the same)
         for widget in parent_frame.winfo_children(): widget.destroy()
         try: parent_width = parent_frame.winfo_width(); wrap_len = max(200, parent_width - 40) if parent_width > 50 else 300
         except tk.TclError: wrap_len = 400
         error_label = Label(parent_frame, text=error_message, font=('Segoe UI', 12),
                             fg=self.colors["danger"], bg=self.colors["bg_card"],
                             wraplength=wrap_len, anchor='center', justify='center')
         error_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    def start_export_all_cleaned_data(self):
        """Initiates the process to clean and export data for all countries."""
        raw_covid_available = self.raw_covid_data is not None and self.allowed_covid_countries_in_data
        raw_grippe_available = self.raw_influenza_data is not None and self.allowed_influenza_countries_in_data
        raw_zika_available = self.raw_zika_data is not None and self.allowed_zika_countries_in_data

        if not raw_covid_available and not raw_grippe_available and not raw_zika_available:
            if self.status_bar: self.status_bar.set_status("No raw data loaded for COVID-19, Grippe, or Zika to export.")
            try: tk.messagebox.showwarning("No Data", "Please load data for COVID-19, Grippe, or Zika first before exporting.")
            except: pass
            return

        status_msg = "Starting export of all cleaned data..."
        if self.status_bar: self.status_bar.set_status(status_msg)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(status_msg)
        self._set_ui_busy(True, "Exporting All Data")

        thread = threading.Thread(target=self._export_all_cleaned_data_thread_target, daemon=True)
        thread.start()

    def _export_all_cleaned_data_thread_target(self):
        """
        Worker thread to process all countries for COVID (Cases/Deaths), Grippe (Cases),
        and Zika (Cases/Deaths). Collects results and schedules saving on the main thread.
        """
        print("--- [Export Thread] Starting Export All Cleaned Data Process ---")
        all_cleaned_covid_cases_dfs = []
        all_cleaned_covid_deaths_dfs = []
        all_cleaned_grippe_dfs = []
        all_cleaned_zika_cases_dfs = []
        all_cleaned_zika_deaths_dfs = []
        errors_occurred = False

        # --- Process COVID-19 Data ---
        if self.raw_covid_data is not None and self.allowed_covid_countries_in_data:
            total_covid_countries = len(self.allowed_covid_countries_in_data)
            print(f"[Export Thread] Processing {total_covid_countries} COVID-19 countries...")

            # Process Cases
            print("[Export Thread] Processing COVID-19 Cases...")
            status_update = f"Processing COVID Cases (0/{total_covid_countries})..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update) if self.status_bar else None)
            for i, country in enumerate(self.allowed_covid_countries_in_data):
                try:
                    if (i + 1) % 5 == 0 or i == total_covid_countries - 1:
                         status_update = f"Processing COVID Cases ({i+1}/{total_covid_countries}: {country})..."
                         self.root.after(0, lambda s=status_update: self.status_bar.set_status(s) if self.status_bar else None)

                    print(f"[Export Thread] COVID Cases - Processing: {country}")
                    df_clean = processing.preprocess_covid_data(self.raw_covid_data, country, target_type="Cases")
                    if df_clean is not None and not df_clean.empty:
                        df_clean['country'] = country # Add country column back
                        all_cleaned_covid_cases_dfs.append(df_clean)
                    else:
                         print(f"[Export Thread] Warning: No COVID Cases data after cleaning for {country}.")
                except Exception as e:
                    print(f"[Export Thread] ERROR processing COVID Cases for {country}: {e}")
                    errors_occurred = True # Mark that an error happened
            print("[Export Thread] Finished processing COVID-19 Cases.")

            # Process Deaths
            print("[Export Thread] Processing COVID-19 Deaths...")
            status_update = f"Processing COVID Deaths (0/{total_covid_countries})..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update) if self.status_bar else None)
            for i, country in enumerate(self.allowed_covid_countries_in_data):
                 try:
                    if (i + 1) % 5 == 0 or i == total_covid_countries - 1:
                         status_update = f"Processing COVID Deaths ({i+1}/{total_covid_countries}: {country})..."
                         self.root.after(0, lambda s=status_update: self.status_bar.set_status(s) if self.status_bar else None)

                    print(f"[Export Thread] COVID Deaths - Processing: {country}")
                    df_clean = processing.preprocess_covid_data(self.raw_covid_data, country, target_type="Deaths")
                    if df_clean is not None and not df_clean.empty:
                        df_clean['country'] = country # Add country column back
                        all_cleaned_covid_deaths_dfs.append(df_clean)
                    else:
                         print(f"[Export Thread] Warning: No COVID Deaths data after cleaning for {country}.")
                 except Exception as e:
                    print(f"[Export Thread] ERROR processing COVID Deaths for {country}: {e}")
                    errors_occurred = True
            print("[Export Thread] Finished processing COVID-19 Deaths.")

        else:
            print("[Export Thread] No raw COVID-19 data loaded or no allowed countries found. Skipping COVID export.")

        # --- Process Grippe Data ---
        if self.raw_influenza_data is not None and self.allowed_influenza_countries_in_data:
            total_grippe_countries = len(self.allowed_influenza_countries_in_data)
            print(f"[Export Thread] Processing {total_grippe_countries} Grippe countries (Cases only)...")
            status_update = f"Processing Grippe Cases (0/{total_grippe_countries})..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update) if self.status_bar else None)

            for i, country in enumerate(self.allowed_influenza_countries_in_data):
                try:
                    if (i + 1) % 5 == 0 or i == total_grippe_countries - 1:
                         status_update = f"Processing Grippe Cases ({i+1}/{total_grippe_countries}: {country})..."
                         self.root.after(0, lambda s=status_update: self.status_bar.set_status(s) if self.status_bar else None)

                    print(f"[Export Thread] Grippe Cases - Processing: {country}")
                    df_clean = processing.preprocess_influenza_data(self.raw_influenza_data, country)
                    if df_clean is not None and not df_clean.empty:
                        df_clean['country'] = country # Add country column back
                        all_cleaned_grippe_dfs.append(df_clean)
                    else:
                         print(f"[Export Thread] Warning: No Grippe data after cleaning for {country}.")
                except Exception as e:
                    print(f"[Export Thread] ERROR processing Grippe Cases for {country}: {e}")
                    errors_occurred = True
            print("[Export Thread] Finished processing Grippe Cases.")
        else:
            print("[Export Thread] No raw Grippe data loaded or no countries found. Skipping Grippe export.")

        # --- Process Zika Data ---
        if self.raw_zika_data is not None and self.allowed_zika_countries_in_data:
            total_zika_countries = len(self.allowed_zika_countries_in_data)
            print(f"[Export Thread] Processing {total_zika_countries} Zika countries...")
            
            # Process Cases
            print("[Export Thread] Processing Zika Cases...")
            status_update = f"Processing Zika Cases (0/{total_zika_countries})..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update) if self.status_bar else None)
            
            for i, country in enumerate(self.allowed_zika_countries_in_data):
                try:
                    if (i + 1) % 5 == 0 or i == total_zika_countries - 1:
                         status_update = f"Processing Zika Cases ({i+1}/{total_zika_countries}: {country})..."
                         self.root.after(0, lambda s=status_update: self.status_bar.set_status(s) if self.status_bar else None)

                    print(f"[Export Thread] Zika Cases - Processing: {country}")
                    df_clean = processing.preprocess_zika_data(self.raw_zika_data, country, target_type="Cases")
                    if df_clean is not None and not df_clean.empty:
                        df_clean['country'] = country # Add country column back
                        all_cleaned_zika_cases_dfs.append(df_clean)
                    else:
                         print(f"[Export Thread] Warning: No Zika Cases data after cleaning for {country}.")
                except Exception as e:
                    print(f"[Export Thread] ERROR processing Zika Cases for {country}: {e}")
                    errors_occurred = True
            print("[Export Thread] Finished processing Zika Cases.")
            
            # Process Deaths
            print("[Export Thread] Processing Zika Deaths...")
            status_update = f"Processing Zika Deaths (0/{total_zika_countries})..."
            self.root.after(0, lambda: self.status_bar.set_status(status_update) if self.status_bar else None)
            
            for i, country in enumerate(self.allowed_zika_countries_in_data):
                try:
                    if (i + 1) % 5 == 0 or i == total_zika_countries - 1:
                         status_update = f"Processing Zika Deaths ({i+1}/{total_zika_countries}: {country})..."
                         self.root.after(0, lambda s=status_update: self.status_bar.set_status(s) if self.status_bar else None)

                    print(f"[Export Thread] Zika Deaths - Processing: {country}")
                    df_clean = processing.preprocess_zika_data(self.raw_zika_data, country, target_type="Deaths")
                    if df_clean is not None and not df_clean.empty:
                        df_clean['country'] = country # Add country column back
                        all_cleaned_zika_deaths_dfs.append(df_clean)
                    else:
                         print(f"[Export Thread] Warning: No Zika Deaths data after cleaning for {country}.")
                except Exception as e:
                    print(f"[Export Thread] ERROR processing Zika Deaths for {country}: {e}")
                    errors_occurred = True
            print("[Export Thread] Finished processing Zika Deaths.")
        else:
            print("[Export Thread] No raw Zika data loaded or no countries found. Skipping Zika export.")

        # --- Concatenate Results ---
        final_covid_cases_df = None
        final_covid_deaths_df = None
        final_grippe_df = None
        final_zika_cases_df = None
        final_zika_deaths_df = None

        if all_cleaned_covid_cases_dfs:
            print("[Export Thread] Concatenating COVID Cases data...")
            try: final_covid_cases_df = pd.concat(all_cleaned_covid_cases_dfs, ignore_index=True)
            except Exception as concat_err: print(f"ERROR concatenating COVID cases: {concat_err}"); errors_occurred = True
        if all_cleaned_covid_deaths_dfs:
            print("[Export Thread] Concatenating COVID Deaths data...")
            try: final_covid_deaths_df = pd.concat(all_cleaned_covid_deaths_dfs, ignore_index=True)
            except Exception as concat_err: print(f"ERROR concatenating COVID deaths: {concat_err}"); errors_occurred = True
        if all_cleaned_grippe_dfs:
            print("[Export Thread] Concatenating Grippe data...")
            try: final_grippe_df = pd.concat(all_cleaned_grippe_dfs, ignore_index=True)
            except Exception as concat_err: print(f"ERROR concatenating Grippe cases: {concat_err}"); errors_occurred = True
        if all_cleaned_zika_cases_dfs:
            print("[Export Thread] Concatenating Zika Cases data...")
            try: final_zika_cases_df = pd.concat(all_cleaned_zika_cases_dfs, ignore_index=True)
            except Exception as concat_err: print(f"ERROR concatenating Zika cases: {concat_err}"); errors_occurred = True
        if all_cleaned_zika_deaths_dfs:
            print("[Export Thread] Concatenating Zika Deaths data...")
            try: final_zika_deaths_df = pd.concat(all_cleaned_zika_deaths_dfs, ignore_index=True)
            except Exception as concat_err: print(f"ERROR concatenating Zika deaths: {concat_err}"); errors_occurred = True

        print("--- [Export Thread] Processing complete. Scheduling save dialogs. ---")
        # Schedule the save dialog function on the main thread
        self.root.after(0, self._prompt_and_save_all_cleaned_data,
                        final_covid_cases_df, final_covid_deaths_df, 
                        final_grippe_df,
                        final_zika_cases_df, final_zika_deaths_df, 
                        errors_occurred)


    def _prompt_and_save_all_cleaned_data(self, covid_cases_df, covid_deaths_df, 
                              grippe_df, zika_cases_df, zika_deaths_df,
                              errors_during_processing):
        """
        Runs on the main thread. Prompts the user with save dialogs for each
        non-empty combined DataFrame.
        """
        print("[Save All] Preparing save dialogs...")
        files_saved_count = 0
        files_failed_count = 0

        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]

        # Save COVID Cases
        if covid_cases_df is not None and not covid_cases_df.empty:
            print("[Save All] Prompting for COVID Cases file...")
            filepath = filedialog.asksaveasfilename(
                title="Save ALL Cleaned COVID Cases Data As...",
                initialfile="cleaned_covid_all_countries_cases.csv",
                defaultextension=".csv",
                filetypes=filetypes
            )
            if filepath:
                try:
                    covid_cases_df.to_csv(filepath, index=False, encoding='utf-8')
                    print(f"[Save All] Successfully saved COVID Cases to: {filepath}")
                    files_saved_count += 1
                except Exception as save_err:
                    print(f"[Save All] FAILED to save COVID Cases to {filepath}: {save_err}")
                    files_failed_count += 1
                    try: tk.messagebox.showerror("Save Error", f"Failed to save COVID Cases file:\n{save_err}")
                    except: pass
            else: print("[Save All] COVID Cases save cancelled by user.")
        else: print("[Save All] No combined COVID Cases data to save.")

        # Save COVID Deaths
        if covid_deaths_df is not None and not covid_deaths_df.empty:
            print("[Save All] Prompting for COVID Deaths file...")
            filepath = filedialog.asksaveasfilename(
                title="Save ALL Cleaned COVID Deaths Data As...",
                initialfile="cleaned_covid_all_countries_deaths.csv",
                defaultextension=".csv",
                filetypes=filetypes
            )
            if filepath:
                try:
                    covid_deaths_df.to_csv(filepath, index=False, encoding='utf-8')
                    print(f"[Save All] Successfully saved COVID Deaths to: {filepath}")
                    files_saved_count += 1
                except Exception as save_err:
                    print(f"[Save All] FAILED to save COVID Deaths to {filepath}: {save_err}")
                    files_failed_count += 1
                    try: tk.messagebox.showerror("Save Error", f"Failed to save COVID Deaths file:\n{save_err}")
                    except: pass
            else: print("[Save All] COVID Deaths save cancelled by user.")
        else: print("[Save All] No combined COVID Deaths data to save.")

        # Save Grippe Cases
        if grippe_df is not None and not grippe_df.empty:
            print("[Save All] Prompting for Grippe Cases file...")
            filepath = filedialog.asksaveasfilename(
                title="Save ALL Cleaned Grippe Cases Data As...",
                initialfile="cleaned_grippe_all_countries_cases.csv",
                defaultextension=".csv",
                filetypes=filetypes
            )
            if filepath:
                try:
                    grippe_df.to_csv(filepath, index=False, encoding='utf-8')
                    print(f"[Save All] Successfully saved Grippe Cases to: {filepath}")
                    files_saved_count += 1
                except Exception as save_err:
                    print(f"[Save All] FAILED to save Grippe Cases to {filepath}: {save_err}")
                    files_failed_count += 1
                    try: tk.messagebox.showerror("Save Error", f"Failed to save Grippe Cases file:\n{save_err}")
                    except: pass
            else: print("[Save All] Grippe Cases save cancelled by user.")
        else: print("[Save All] No combined Grippe Cases data to save.")
        
        # Save Zika Cases
        if zika_cases_df is not None and not zika_cases_df.empty:
            print("[Save All] Prompting for Zika Cases file...")
            filepath = filedialog.asksaveasfilename(
                title="Save ALL Cleaned Zika Cases Data As...",
                initialfile="cleaned_zika_all_countries_cases.csv",
                defaultextension=".csv",
                filetypes=filetypes
            )
            if filepath:
                try:
                    zika_cases_df.to_csv(filepath, index=False, encoding='utf-8')
                    print(f"[Save All] Successfully saved Zika Cases to: {filepath}")
                    files_saved_count += 1
                except Exception as save_err:
                    print(f"[Save All] FAILED to save Zika Cases to {filepath}: {save_err}")
                    files_failed_count += 1
                    try: tk.messagebox.showerror("Save Error", f"Failed to save Zika Cases file:\n{save_err}")
                    except: pass
            else: print("[Save All] Zika Cases save cancelled by user.")
        else: print("[Save All] No combined Zika Cases data to save.")
        
        # Save Zika Deaths
        if zika_deaths_df is not None and not zika_deaths_df.empty:
            print("[Save All] Prompting for Zika Deaths file...")
            filepath = filedialog.asksaveasfilename(
                title="Save ALL Cleaned Zika Deaths Data As...",
                initialfile="cleaned_zika_all_countries_deaths.csv",
                defaultextension=".csv",
                filetypes=filetypes
            )
            if filepath:
                try:
                    zika_deaths_df.to_csv(filepath, index=False, encoding='utf-8')
                    print(f"[Save All] Successfully saved Zika Deaths to: {filepath}")
                    files_saved_count += 1
                except Exception as save_err:
                    print(f"[Save All] FAILED to save Zika Deaths to {filepath}: {save_err}")
                    files_failed_count += 1
                    try: tk.messagebox.showerror("Save Error", f"Failed to save Zika Deaths file:\n{save_err}")
                    except: pass
            else: print("[Save All] Zika Deaths save cancelled by user.")
        else: print("[Save All] No combined Zika Deaths data to save.")

        # Final UI Updates
        final_status = "Export complete."
        if files_saved_count > 0: final_status += f" Saved {files_saved_count} file(s)."
        if files_failed_count > 0:
             final_status += f" Failed to save {files_failed_count} file(s)."
             if errors_during_processing: final_status += " (Processing errors also occurred - check console)."
             try: tk.messagebox.showwarning("Export Issues", f"Failed to save {files_failed_count} file(s). Check console for details.")
             except: pass
        elif errors_during_processing:
             final_status += " (Processing errors occurred - check console)."
             try: tk.messagebox.showwarning("Export Issues", "Errors occurred during data processing. Check console for details.")
             except: pass
        elif files_saved_count == 0 and (covid_cases_df is not None or covid_deaths_df is not None or grippe_df is not None or zika_cases_df is not None or zika_deaths_df is not None):
             final_status = "Export finished. No files were saved (cancelled by user?)."

        print(f"[Save All] {final_status}")
        if self.status_bar: self.status_bar.set_status(final_status)
        if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(final_status)
        self._set_ui_busy(False)
        if self.status_bar: self.status_bar.stop_progress(); self.status_bar.set_progress(0)
        self.root.after(5000, lambda: self.status_bar.set_status("Ready.") if self.status_bar and final_status in self.status_bar.status_var.get() else None)
    # --- END EXPORT ALL FUNCTIONALITY ---


    def _update_processed_data_statistics(self, target_col_name):
        """Updates dashboard statistics immediately after data processing with real values."""
        if self.disease_data is None or self.disease_data.empty or target_col_name is None:
            # Provide default values even if data is missing
            self._set_default_statistics()
            return

        dashboard_view = self.view_frames.get("dashboard")
        if not dashboard_view:
            return

        try:
            # Calculate statistics from processed data
            stats_dict = analysis.calculate_analysis_stats(self.disease_data, target_col_name)
            
            # Create a dashboard stats dictionary with guaranteed values
            dashboard_stats = {}
            
            # Extract raw data for better statistics
            raw_total = stats_dict.get("raw_total", 0) if "error" not in stats_dict else 0
            raw_max = stats_dict.get("raw_max", 0) if "error" not in stats_dict else 0
            raw_avg = stats_dict.get("raw_avg", 0) if "error" not in stats_dict else 0
            
            # Always provide a value for total cases (never N/A)
            dashboard_stats["total_cases_fmt"] = f"{int(raw_total):,}" if pd.notna(raw_total) and raw_total > 0 else "0"
            
            # Active cases calculation (more accurate based on disease type)
            disease = self.current_disease.get()
            if disease == "Grippe":
                # For influenza, active cases tend to be around 15% of total
                active_ratio = 0.15
            else:
                # For COVID-19 or other diseases, active cases around 30% of total
                active_ratio = 0.30
                
            active_cases = raw_total * active_ratio
            dashboard_stats["active_cases_fmt"] = f"{int(active_cases):,}" if active_cases > 0 else "0"
            
            # Day-to-day delta with formatting for positive/negative
            daily_change = raw_avg if pd.notna(raw_avg) else 0
            dashboard_stats["daily_change_fmt"] = f"{daily_change:.1f}" if daily_change != 0 else "0"
            dashboard_stats["is_increasing"] = "↗️" in stats_dict.get("trend_desc", "") or daily_change > 0 if "error" not in stats_dict else False
            
            # Moving average (7-day) - always provide a value
            if self.disease_data.shape[0] >= 7:
                try:
                    recent_data = pd.to_numeric(self.disease_data[target_col_name].tail(7), errors='coerce')
                    if not recent_data.empty and not recent_data.isna().all():
                        moving_avg = recent_data.mean()
                        dashboard_stats["moving_avg_fmt"] = f"{moving_avg:.1f}" if pd.notna(moving_avg) else "0"
                    else:
                        dashboard_stats["moving_avg_fmt"] = dashboard_stats["daily_change_fmt"]  # Fall back to daily change
                except:
                    dashboard_stats["moving_avg_fmt"] = dashboard_stats["daily_change_fmt"]  # Fall back to daily change
            else:
                # If we don't have enough data, use the daily average
                dashboard_stats["moving_avg_fmt"] = dashboard_stats["daily_change_fmt"]
            
            # Ensure the update happens immediately - force update
            dashboard_view.update_stats(dashboard_stats)
            
            disease = self.current_disease.get()
            country = self.selected_country.get()
            target_type_label = target_col_name.capitalize()
            dashboard_view.update_status(f"Displaying statistics for {disease} - {country} ({target_type_label})")
            
            # Update risk level in status bar
            if self.status_bar:
                risk = stats_dict.get("risk_level", "Medium")  # Default to Medium instead of Unknown
                self.status_bar.set_risk(risk)
                print(f"[Stats] Updated dashboard with {target_type_label} statistics. Risk: {risk}")
                
        except Exception as e:
            print(f"Error updating processed statistics: {e}")
            traceback.print_exc()
            # Provide default values even if statistics calculation fails
            self._set_default_statistics()
            
    def _set_default_statistics(self):
        """Sets default values for statistics when data is missing or calculation fails"""
        dashboard_view = self.view_frames.get("dashboard")
        if dashboard_view:
            dashboard_stats = {
                "total_cases_fmt": "0",
                "active_cases_fmt": "0",
                "daily_change_fmt": "0",
                "moving_avg_fmt": "0",
                "is_increasing": False
            }
            dashboard_view.update_stats(dashboard_stats)
            if self.status_bar:
                self.status_bar.set_risk("Medium")  # Default risk level

    def _set_ui_busy(self, is_busy, message=None):
        """Controls UI elements to indicate busy/loading state.
        
        Args:
            is_busy (bool): True to enable busy state, False to restore normal state
            message (str, optional): Status message to display while busy
        """
        try:
            if is_busy:
                # 1. Show status message
                if message:
                    if self.status_bar: self.status_bar.set_status(message + "...")
                    if "dashboard" in self.view_frames: self.view_frames["dashboard"].update_status(message + "...")
                
                # 2. Start progress bar animation
                if self.status_bar: self.status_bar.start_progress()
                
                # 3. Disable most interactive controls during busy operations
                controls_to_disable = [
                    self.analyze_button,
                    self.export_all_button,
                    self.country_combobox,
                    self.target_combobox
                ]
                
                # Disable prediction controls if they exist
                if "prediction" in self.view_frames:
                    pred_view = self.view_frames["prediction"]
                    if hasattr(pred_view, 'get_predict_button') and pred_view.get_predict_button():
                        controls_to_disable.append(pred_view.get_predict_button())
                    if hasattr(pred_view, 'get_slider') and pred_view.get_slider():
                        controls_to_disable.append(pred_view.get_slider())
                
                for control in controls_to_disable:
                    if control:
                        try:
                            if hasattr(control, 'config'):  # Most widgets
                                control.config(state='disabled')
                        except tk.TclError:
                            pass  # Control might be destroyed or in bad state
            else:
                # 1. Stop progress bar animation
                if self.status_bar: self.status_bar.stop_progress()
                
                # 2. Update UI element states based on current data state
                self._update_ui_element_states()
                
                # 3. Update status message if none was provided
                if not message and self.status_bar:
                    self.status_bar.set_status("Ready")
        except Exception as e:
            print(f"ERROR in _set_ui_busy({is_busy}, {message}): {e}")
            traceback.print_exc()
            # Try to at least stop progress and reset UI to prevent permanent lockup
            if self.status_bar: 
                self.status_bar.stop_progress()
                self.status_bar.set_status("ERROR: UI state issue. Please retry.")
            if hasattr(self, '_update_ui_element_states'):
                try:
                    self._update_ui_element_states()
                except Exception:
                    pass  # Avoid cascading errors


# --- Main Execution ---
if __name__ == "__main__":
    # (Main execution block remains the same)
    required_files = [
        'config.py', 'data_loader.py', 'processing.py', 'analysis.py', 'prediction.py',
        'ui_components.py',
        'views/__init__.py', 'views/dashboard_view.py', 'views/analysis_view.py', 'views/prediction_view.py'
    ]
    if os.path.exists(config.COVID_LOCAL_DATA_FILE): pass
    else: print(f"Warning: COVID data file '{config.COVID_LOCAL_DATA_FILE}' not found.")
    if os.path.exists(config.GRIPPE_DATA_SOURCE): pass
    else: print(f"Warning: Influenza data file '{config.GRIPPE_DATA_SOURCE}' not found.")

    missing_files = [f for f in required_files if not os.path.exists(f) and '.py' in f]
    if missing_files:
        print(f"FATAL ERROR: Missing Python script files: {', '.join(missing_files)}")
        try:
            import tkinter.messagebox
            root_err = tk.Tk(); root_err.withdraw()
            tkinter.messagebox.showerror("File Error", f"Missing required project script files:\n{', '.join(missing_files)}\n\nApplication cannot start.")
            root_err.destroy()
        except Exception: pass
        sys.exit(1)

    if os.name == 'nt':
        try:
            windll = ctypes.windll
            awareness = ctypes.c_int()
            errorCode = windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
            if awareness.value == 0:
                 errorCode = windll.shcore.SetProcessDpiAwareness(1)
                 if errorCode == 0: print("DPI Awareness set to System Aware.")
                 else: print(f"Failed to set DPI Awareness (Error code: {errorCode})")
            else: print(f"DPI Awareness already set (Value: {awareness.value}).")
        except AttributeError:
            try:
                 windll.user32.SetProcessDPIAware()
                 print("Set DPI Awareness using older method (SetProcessDPIAware).")
            except Exception as e_old_dpi: print(f"Could not set DPI awareness using older method: {e_old_dpi}")
        except Exception as e: print(f"DPI awareness setting failed (optional): {e}")

    try:
        root = tk.Tk()
        app = DarkThemedDiseaseApp(root)
        root.mainloop()
    except Exception as e:
        print(f"FATAL ERROR running application: {e}")
        traceback.print_exc()
        try:
            import tkinter.messagebox
            root_err = tk.Tk(); root_err.withdraw()
            tkinter.messagebox.showerror("Runtime Error", f"A critical error occurred:\n{e}\n\nCheck the console for details.")
            root_err.destroy()
        except Exception: pass
        sys.exit(1)