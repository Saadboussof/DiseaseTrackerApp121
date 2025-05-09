# views/dashboard_view.py
import tkinter as tk
from tkinter import ttk, Frame, Label, StringVar
from ui_components import StatsCard, GradientFrame, ParticleBackground, ModernHeader, ThemeToggle

class DashboardView(Frame):
    """Main dashboard view showing overview statistics and visualizations."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg_dark"])
        self.controller = controller  # Keep reference to the main application controller

        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content area
        self.columnconfigure(0, weight=1)  # Main content

        # Create particle background (FIRST, so it's behind everything)
        self.particle_bg = ParticleBackground(self, 
                                             bg_color=controller.colors["bg_dark"],
                                             particle_color=controller.colors["particle_color"])
        self.particle_bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.particle_bg.lower()  # Ensure it's at the back
        
        # Modern animated header
        self.header_frame = ModernHeader(self, 
                                      title="Disease Dashboard", 
                                      subtitle="Live Data & Statistics",
                                      icon="🦠", 
                                      bg=controller.colors["bg_dark"])
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="nw")
        
        # Add theme toggle in header (right aligned)
        self.theme_toggle = ThemeToggle(self.header_frame, initial_theme="dark", 
                                     command=self.on_theme_change,
                                     bg=controller.colors["bg_dark"])
        self.theme_toggle.grid(row=0, column=2, rowspan=2, padx=(20, 0), sticky="ne")
        self.header_frame.columnconfigure(2, weight=1)  # Make the toggle right-aligned

        # Main Content Area (Cards and Status)
        self.content_frame = Frame(self, bg=controller.colors["bg_dark"], padx=20, pady=20)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=0)  # Stats cards
        self.content_frame.rowconfigure(1, weight=1)  # Status area

        # Stats Cards Frame - will hold stat cards in horizontal layout
        self.stats_frame = Frame(self.content_frame, bg=controller.colors["bg_dark"])
        self.stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # Create and arrange stat cards
        self._create_stats_cards()

        # Status area and message display beneath stats
        self.status_area = GradientFrame(self.content_frame, controller.colors["bg_card"], controller.colors["bg_gradient_end"])
        self.status_area.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.status_message = StringVar(value="Select Disease to begin analysis")
        
        # Add larger status label with instruction message
        self.status_label = Label(
            self.status_area, textvariable=self.status_message, 
            font=("Segoe UI", 14), anchor="center",
            bg=controller.colors["bg_card"], fg=controller.colors["text_secondary"]
        )
        self.status_label.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Start particle background animation
        self.particle_bg.start_animation()

    def _create_stats_cards(self):
        """Creates statistic cards for the dashboard."""
        stats_config = [
            {"title": "Confirmed Cases", "value": "0", "fg": "#FC6657"},   # Orange
            {"title": "Active Cases", "value": "0", "fg": "#00CCB8"},      # Teal
            {"title": "Day-to-Day Δ", "value": "0", "fg": "#FF3366"},      # Pink
            {"title": "Moving Average", "value": "0", "fg": "#4B7BEC"}     # Blue
        ]
        
        # Create dictionary to store cards by name
        self.stat_cards = {
            'total_cases': None, 
            'active_cases': None,
            'daily_change': None,
            'moving_average': None
        }
        
        card_names = list(self.stat_cards.keys())
        
        # Arrange cards in a grid to allow for nicer spacing and responsive layout
        for i, stat in enumerate(stats_config):
            card = StatsCard(
                self.stats_frame, 
                title=stat["title"], 
                value=stat["value"],
                fg_value=stat["fg"],
                card_bg=self.controller.colors["bg_card"],
                title_fg=self.controller.colors["text_secondary"]
            )
            col = i % 4  # Four cards per row
            card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            
            # Store reference in both ways
            card_name = card_names[i]
            setattr(self, f"card_{i}", card)
            self.stat_cards[card_name] = card
            
        # Configure column weights to make cards of equal width
        for i in range(4):
            self.stats_frame.columnconfigure(i, weight=1)

    def on_theme_change(self, theme):
        """Handle theme changes from the toggle button"""
        print(f"Theme changed to: {theme}")
        # Here you would implement logic to change application colors
        # This is a placeholder - full implementation would update all colors
        
        # Store theme in the controller for app-wide awareness
        self.controller.current_theme.set(theme)
        
        # Show a notification of the theme change
        self.update_status(f"Theme changed to {theme} mode")

    def update_status(self, message):
        """Updates the status message on the dashboard."""
        self.status_message.set(message)

    def update_stats(self, stats_dict):
        """Updates the statistics cards with new values."""
        if not stats_dict:
            self.clear_stats()
            return
        
        try:
            # Replace any "N/A" values with "0"
            for card_name, default_value in [
                ('total_cases', '0'),
                ('active_cases', '0'),
                ('daily_change', '0'),
                ('moving_average', '0')
            ]:
                # Try to get the formatted value from stats_dict
                if card_name == 'total_cases':
                    card_value = stats_dict.get('total_cases_fmt', default_value)
                elif card_name == 'active_cases':
                    card_value = stats_dict.get('active_cases_fmt', default_value)
                elif card_name == 'daily_change':
                    card_value = stats_dict.get('daily_change_fmt', default_value)
                elif card_name == 'moving_average':
                    card_value = stats_dict.get('moving_avg_fmt', default_value)
                
                # Ensure we never display "N/A"
                if card_value in ["N/A", "--", None]:
                    card_value = default_value
                
                # Set increasing flag for daily change
                if card_name == 'daily_change':
                    is_increasing = stats_dict.get('is_increasing', False)
                    trend = "up" if is_increasing else "down"
                    self.stat_cards[card_name].update_value(card_value, animate=True, trend=trend)
                else:
                    self.stat_cards[card_name].update_value(card_value, animate=True)
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
            self._show_error_in_stats(f"Stats Display Error: {e}")

    def clear_stats(self):
        """Resets all statistic cards to N/A."""
        for i in range(4):
            card = getattr(self, f"card_{i}", None)
            if card:
                card.update_value("N/A", animate=False)
                card.trend_direction = "none"  # Reset trend indicator
                card._draw_trend_indicator()

    def _show_error_in_stats(self, error_message):
        """Displays error message in all stats cards."""
        for i in range(4):
            card = getattr(self, f"card_{i}", None)
            if card:
                if i == 0:  # First card gets the error message
                    card.update_title("ERROR")
                    card.update_value("!", animate=False)
                else:  # Other cards just get cleared
                    card.update_value("--", animate=False)
                card.trend_direction = "none"
                card._draw_trend_indicator()
        
        self.update_status(f"Error: {error_message}")

    def get_plot_frame(self):
        """Returns the frame where plots should be displayed (in this case, status area)."""
        return self.status_area