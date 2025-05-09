# ui_components.py
"""Contains shared custom Tkinter UI component classes with enhanced styling."""

import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Scale, StringVar, font, Canvas
import traceback # Added for error reporting in GlowButton command
import time # For animations
import math
import random

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
except ImportError:
    print("FATAL ERROR: Pillow library not found. Please install it: pip install Pillow")
    try: # Attempt to show Tkinter error if possible
        import tkinter.messagebox
        root_err = tk.Tk(); root_err.withdraw()
        tkinter.messagebox.showerror("Import Error", "Pillow not found.\nPlease install it using:\npip install Pillow")
        root_err.destroy()
    except Exception: pass
    import sys
    sys.exit(1)

# --- GradientFrame Class ---
class GradientFrame(Canvas):
    """A canvas that creates a gradient background."""
    def __init__(self, parent, color1="#1A103C", color2="#261758", **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self._color1 = color1
        self._color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        """Draw the gradient background on canvas resize."""
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1: return

        gradient_img = Image.new('RGBA', (width, height), color=self._color1)
        draw = ImageDraw.Draw(gradient_img)
        r1, g1, b1 = self._hex_to_rgb(self._color1)
        r2, g2, b2 = self._hex_to_rgb(self._color2)

        # Draw the gradient (vertical)
        for y in range(height):
            factor = y / height
            r = r1 + (r2 - r1) * factor
            g = g1 + (g2 - g1) * factor
            b = b1 + (b2 - b1) * factor
            color = self._rgb_to_hex(int(r), int(g), int(b))
            draw.line([(0, y), (width, y)], fill=color)

        self._gradient = ImageTk.PhotoImage(gradient_img)
        self.create_image(0, 0, anchor="nw", image=self._gradient, tags=("gradient",))
        self.tag_lower("gradient")

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        if len(h) == 8: h = h[:6] # Strip alpha if present
        if len(h) != 6: raise ValueError(f"Invalid hex color format: {hex_color}")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r, g, b):
        return f'#{r:02x}{g:02x}{b:02x}'

# --- GlowButton Class ---
class GlowButton(tk.Frame):
    """A custom button with gradient and glow effect, emphasizing the icon."""
    def __init__(self, parent, text, command=None, fg="#FFFFFF",
                 start_color="#00CCB8", end_color="#FF3366", width=135, height=40,
                 corner_radius=20, font_size=9, icon_font_size=22, icon=None, state='normal', **kwargs): # Add state
        parent_bg = parent.cget('bg')
        super().__init__(parent, bg=parent_bg, **kwargs)
        self.start_color = start_color
        self.end_color = end_color
        self.fg = fg
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.command = command
        self.font_size = font_size
        self.icon_font_size = icon_font_size
        self.icon_char = icon # Store the provided icon character
        self.is_disabled = state == 'disabled' # Initialize based on state

        self.canvas = Canvas(self, width=width, height=height, bg=parent_bg,
                             highlightthickness=0)
        self.canvas.pack()

        self._create_button_elements(text)
        self._bind_events()
        self._set_state(state) # Apply initial state

    def _create_button_elements(self, text):
        """Creates the button images and text/icon canvas items."""
        self.normal_image = self._create_gradient_image(self.start_color, self.end_color, glow=False)
        self.hover_image = self._create_gradient_image(self.start_color, self.end_color, glow=True)
        self.active_image = self._create_gradient_image(self.end_color, self.start_color, glow=False) # Clicked gradient reverse
        self.disabled_image = self._create_gradient_image("#555555", "#444444", glow=False) # Disabled grey gradient

        self.button_image = self.disabled_image if self.is_disabled else self.normal_image # Set initial image based on state
        self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.button_image)

        # Positioning logic
        icon_padding_left = self.width * 0.18 # Distance from left edge for icon center
        icon_x_pos = icon_padding_left
        text_padding_left = self.width * 0.40 if self.icon_char else self.width * 0.5 # Start of text / Center if no icon
        text_x_pos = text_padding_left
        anchor_txt = "w" if self.icon_char else "center" # Anchor text left if icon, else center

        # Create Icon Item (if icon provided)
        self.icon_text = None
        if self.icon_char:
             self.icon_text = self.canvas.create_text(
                 icon_x_pos, self.height // 2, text=self.icon_char,
                 fill=self.fg, font=("Segoe UI Symbol", self.icon_font_size), # Use specific font if needed
                 anchor="center"
             )

        # Create Text Item
        self.text_item = self.canvas.create_text(
            text_x_pos, self.height // 2, text=text, fill=self.fg,
            font=("Segoe UI", self.font_size, "bold"), anchor=anchor_txt
        )

    def _create_gradient_image(self, start_color, end_color, glow=False):
        """Creates a rounded gradient PIL Image."""
        padding = 10 if glow else 0 # Padding around the button for the glow effect
        img_width = self.width + 2 * padding
        img_height = self.height + 2 * padding

        # Base image (transparent)
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Gradient calculation
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)

        # Draw the horizontal gradient within the button area (excluding padding)
        for x in range(self.width):
            progress = x / max(1, self.width - 1) # Avoid division by zero if width is 1
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
            gradient_color = (r, g, b, 255) # Opaque gradient color
            # Draw line from top to bottom of button area at current x
            draw.line([(x + padding, padding), (x + padding, self.height + padding - 1)], fill=gradient_color, width=1)

        # Create the rounded rectangle mask for the button shape
        mask = Image.new('L', (img_width, img_height), 0) # Black background (transparent)
        mask_draw = ImageDraw.Draw(mask)
        # Draw white rounded rectangle in the button area (opaque)
        mask_draw.rounded_rectangle(
            (padding, padding, self.width + padding, self.height + padding),
            radius=self.corner_radius, fill=255
        )

        # Apply the mask to the gradient image
        img.putalpha(mask)

        if glow:
            # Create a slightly larger, blurred mask for the glow effect
            glow_mask = Image.new('L', (img_width, img_height), 0)
            glow_draw = ImageDraw.Draw(glow_mask)
            glow_radius_factor = 1.5 # How much larger the glow shape is
            # Draw a semi-transparent filled rounded rectangle slightly larger than the button
            glow_draw.rounded_rectangle(
                (padding - glow_radius_factor, padding - glow_radius_factor,
                 self.width + padding + glow_radius_factor, self.height + padding + glow_radius_factor),
                radius=self.corner_radius + glow_radius_factor, fill=150 # semi-transparent white
            )
            # Apply Gaussian blur to the glow mask
            glow_mask_blurred = glow_mask.filter(ImageFilter.GaussianBlur(radius=6))

            # Create the colored glow layer (transparent initially)
            # Using a fixed bright teal glow color for hover effect
            glow_color_rgb = self._hex_to_rgb("#00FFE0")
            glow_layer = Image.new('RGBA', (img_width, img_height), (*glow_color_rgb, 0))
            # Apply the blurred mask as the alpha channel of the glow layer
            glow_layer.putalpha(glow_mask_blurred)

            # Composite the glow layer *under* the main button image
            final_image = Image.alpha_composite(glow_layer, img)
            return ImageTk.PhotoImage(final_image)
        else:
            # No glow, just return the masked gradient image
            return ImageTk.PhotoImage(img)

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        if len(h) == 8: h = h[:6] # Strip alpha if present
        if len(h) != 6: raise ValueError(f"Invalid hex color format: {hex_color}")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _bind_events(self):
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _unbind_events(self):
        self.canvas.unbind("<Enter>")
        self.canvas.unbind("<Leave>")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")

    def _on_enter(self, event):
        # Only change image - don't resize or move the button
        if not self.is_disabled: 
            self.canvas.itemconfig(self.image_item, image=self.hover_image)

    def _on_leave(self, event):
        # Only change image - don't resize or move the button
        if not self.is_disabled: 
            self.canvas.itemconfig(self.image_item, image=self.normal_image)

    def _on_click(self, event):
        # Only change image - don't resize or move the button
        if not self.is_disabled: 
            self.canvas.itemconfig(self.image_item, image=self.active_image)

    def _on_release(self, event):
        if not self.is_disabled:
            x, y = event.x, event.y
            # Check if release happened within button bounds
            if 0 <= x < self.width and 0 <= y < self.height:
                self.canvas.itemconfig(self.image_item, image=self.hover_image) # Return to hover state if still inside
                if self.command:
                    try:
                        self.command()
                    except Exception as cmd_err:
                        print(f"Error executing GlowButton command: {cmd_err}")
                        traceback.print_exc()
            else:
                 self.canvas.itemconfig(self.image_item, image=self.normal_image) # Return to normal if outside

    def set_text(self, text):
        """Updates the button's text label."""
        text_padding_left = self.width * 0.40 if self.icon_char else self.width * 0.5
        text_x_pos = text_padding_left
        anchor = "w" if self.icon_char else "center"
        self.canvas.itemconfig(self.text_item, text=text, anchor=anchor)
        self.canvas.coords(self.text_item, text_x_pos, self.height // 2)

    def configure(self, **kwargs):
        """Configures button properties like state, text, command, etc."""
        if 'state' in kwargs: self._set_state(kwargs.pop('state'))
        if 'text' in kwargs: self.set_text(kwargs.pop('text'))
        if 'command' in kwargs: self.command = kwargs.pop('command')
        # Allow changing font sizes dynamically if needed
        if 'font_size' in kwargs:
            self.font_size = kwargs.pop('font_size')
            self.canvas.itemconfig(self.text_item, font=("Segoe UI", self.font_size, "bold"))
        if 'icon_font_size' in kwargs:
            self.icon_font_size = kwargs.pop('icon_font_size')
            if self.icon_text:
                 self.canvas.itemconfig(self.icon_text, font=("Segoe UI Symbol", self.icon_font_size))
        # Pass any remaining standard Tk Frame options to the superclass
        super().configure(**kwargs)

    # Provide config method as an alias for configure
    def config(self, **kwargs): self.configure(**kwargs)

    # Add cget method to retrieve configuration values
    def cget(self, key):
        if key == 'state':
            return 'disabled' if self.is_disabled else 'normal'
        elif key == 'text':
             return self.canvas.itemcget(self.text_item, 'text')
        elif key == 'command':
             return self.command
        # Add other properties if needed
        else:
            # Try getting from the canvas or frame itself
            try: return self.canvas.cget(key)
            except tk.TclError:
                try: return super().cget(key)
                except tk.TclError: return None # Or raise error

    def _set_state(self, state):
        """Sets the button state (normal or disabled)."""
        if state == 'disabled':
            if not self.is_disabled: # Only change if not already disabled
                self.is_disabled = True
                self.canvas.itemconfig(self.image_item, image=self.disabled_image)
                # Change text/icon color to grey
                disabled_fg = "#888888"
                self.canvas.itemconfig(self.text_item, fill=disabled_fg)
                if self.icon_text: self.canvas.itemconfig(self.icon_text, fill=disabled_fg)
                self._unbind_events() # Disable interactions
        else: # 'normal' or any other value treated as normal
            if self.is_disabled: # Only change if not already enabled
                self.is_disabled = False
                self.canvas.itemconfig(self.image_item, image=self.normal_image)
                 # Restore original text/icon color
                self.canvas.itemconfig(self.text_item, fill=self.fg)
                if self.icon_text: self.canvas.itemconfig(self.icon_text, fill=self.fg)
                self._bind_events() # Re-enable interactions

# --- StatsCard Class ---
class StatsCard(tk.Frame):
    """A card to display a statistic with title and value."""
    def __init__(self, parent, title="Statistic", value="N/A", fg_value="#FC6657", card_bg="#261758", title_fg="#8A7CB4", **kwargs):
        # Use provided colors or defaults
        self.card_bg = card_bg
        self.title_fg = title_fg
        self.value_fg = fg_value
        super().__init__(parent, bg=self.card_bg, padx=20, pady=15, **kwargs)
        
        # Add shadow and rounded corners with canvas
        self.canvas = Canvas(self, bg=self.card_bg, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.title = title
        self.title_label = Label(self, text=title.upper(), fg=self.title_fg, bg=self.card_bg, font=("Segoe UI", 9, "bold"))
        self.title_label.pack(anchor="w", pady=(0, 2))
        self.value_var = StringVar(value=value)
        self.value_label = Label(self, textvariable=self.value_var, fg=self.value_fg, bg=self.card_bg, font=("Segoe UI", 22, "bold"))
        self.value_label.pack(anchor="w")
        
        # Animated value indicator (small triangle)
        self.trend_indicator = tk.Canvas(self, width=14, height=14, bg=self.card_bg, highlightthickness=0)
        self.trend_indicator.pack(anchor="w", pady=(5, 0))
        self.trend_direction = "none"  # none, up, down
        self._draw_trend_indicator()
        
        # Schedule pulsing animation
        self._start_pulse_animation()

    def _draw_trend_indicator(self):
        """Draws the trend indicator triangle"""
        self.trend_indicator.delete("all")
        
        if self.trend_direction == "up":
            # Green upward triangle
            self.trend_indicator.create_polygon(7, 2, 14, 12, 0, 12, fill="#28A745")
        elif self.trend_direction == "down":
            # Red downward triangle
            self.trend_indicator.create_polygon(7, 12, 14, 2, 0, 2, fill="#B12025")
        # "none" direction doesn't draw anything
    
    def _start_pulse_animation(self):
        """Start subtle pulsing animation for the value"""
        def pulse():
            # Create subtle pulsing effect for the value
            current_font = self.value_label.cget("font")
            if isinstance(current_font, str):
                font_obj = font.Font(font=current_font)
            else:
                font_obj = current_font
                
            # Pulse by slightly changing the font size
            size = font_obj.cget("size")
            new_size = size + 1
            
            # Update font
            self.value_label.configure(font=(font_obj.cget("family"), new_size, "bold"))
            
            # Return to normal after short delay
            self.after(150, lambda: self.value_label.configure(font=(font_obj.cget("family"), size, "bold")))
            
            # Schedule next pulse in a few seconds
            self.after(5000, pulse)
            
        # Start the pulse effect
        self.after(2000, pulse)

    def update_value(self, value, animate=True, trend=None):
        """Updates the displayed value with animation."""
        old_value = self.value_var.get()
        
        # First, ensure no N/A values are displayed
        if value in ("N/A", "--", "None", "") or value is None:
            value = "0"
            
        try:
            # Try to determine if it's a numeric change we can animate
            old_numeric = float(old_value) if old_value not in ("N/A", "--") else 0
            new_numeric = float(value) if value not in ("N/A", "--") else 0
            
            if animate and abs(new_numeric - old_numeric) > 0:
                # Set trend indicator
                if trend:
                    self.trend_direction = trend
                elif new_numeric > old_numeric:
                    self.trend_direction = "up"
                elif new_numeric < old_numeric:
                    self.trend_direction = "down"
                else:
                    self.trend_direction = "none"
                    
                self._draw_trend_indicator()
                    
                # Calculate steps for animation
                steps = 10
                increment = (new_numeric - old_numeric) / steps
                
                # Perform animation
                def update_step(step):
                    if step <= steps:
                        intermediate = old_numeric + (increment * step)
                        # Format with same precision as the target value
                        if isinstance(value, int):
                            display_val = int(intermediate)
                        else:
                            display_val = round(intermediate, 2)
                        self.value_var.set(str(display_val))
                        self.after(30, lambda: update_step(step + 1))
                    else:
                        self.value_var.set(str(value))
                
                update_step(1)
            else:
                # Direct update without animation
                self.value_var.set(str(value))
        except (ValueError, TypeError):
            # Not a numeric value, just update directly
            # Make sure we're not showing N/A
            if value in ("N/A", "--", "None", "") or value is None:
                value = "0"
            self.value_var.set(str(value))

    def update_title(self, new_title):
        """Updates the displayed title."""
        self.title = new_title
        self.title_label.config(text=new_title.upper())

# --- StatusBarWithRisk Class ---
class StatusBarWithRisk(tk.Frame):
    """A status bar with integrated risk indicator."""
    def __init__(self, parent, colors, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.configure(bg=self.colors["bg_dark"], pady=5, padx=10) # Use main dark bg

        # Right-aligned elements (Risk Indicator)
        self.risk_frame = tk.Frame(self, bg=self.colors["bg_dark"], padx=10)
        self.risk_frame.pack(side="right")

        self.risk_label = Label(self.risk_frame, text="Risk Level:", fg=self.colors["text_secondary"], bg=self.colors["bg_dark"], font=("Segoe UI", 9))
        self.risk_label.pack(side="left", padx=(0, 5))

        self.risk_value_var = StringVar(value="Unknown") # Default to Unknown
        self.risk_value_label = Label(self.risk_frame, textvariable=self.risk_value_var, fg=self.colors["text_primary"], bg=self.colors["text_secondary"], font=("Segoe UI", 9, "bold"), padx=10, pady=2)

        # --- CORRECTED LINE ---
        # Remove bordercolor, rely on relief and borderwidth
        self.risk_value_label.configure(relief="raised", borderwidth=1)
        # --- END CORRECTION ---

        self.risk_value_label.pack(side="left")

        # Left-aligned elements (Status Text & Progress Bar)
        self.status_frame = tk.Frame(self, bg=self.colors["bg_dark"])
        self.status_frame.pack(side="left", fill="x", expand=True, padx=(0, 20)) # Fill available space

        self.status_var = StringVar(value="Ready...")
        self.status_label = Label(self.status_frame, textvariable=self.status_var, fg=self.colors["text_secondary"], bg=self.colors["bg_dark"], anchor="w", font=("Segoe UI", 9))
        self.status_label.pack(side="left", fill="x", expand=True) # Label expands

        # Progress bar (fixed width, right-aligned within the status_frame)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, orient='horizontal', length=180, mode='determinate', variable=self.progress_var, style="Dark.Horizontal.TProgressbar")
        self.progress_bar.pack(side="right", padx=(10, 0)) # Pack to the right of the label

        # Set initial risk color
        self.set_risk("Unknown")

    def set_status(self, text):
        """Sets the text of the status label."""
        self.status_var.set(text)

    def set_risk(self, level):
        """Sets the risk level indicator text and color."""
        level_str = str(level).lower()
        if level_str == "low":
            color = self.colors["success"]; txt = "Low"
        elif level_str == "high":
            color = self.colors["danger"]; txt = "High"
        elif level_str == "medium":
            color = self.colors["warning"]; txt = "Medium"
        elif level_str == "error": # Specific state for errors
             color = self.colors["danger"]; txt = "Error"
        else: # Default / Unknown
            color = self.colors["text_secondary"]; txt = "Unknown"

        self.risk_value_var.set(txt)
        # Update background color ONLY
        self.risk_value_label.config(bg=color)

    def start_progress(self):
        """Starts the indeterminate progress bar animation."""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(15) # Adjust speed if needed

    def stop_progress(self):
        """Stops the progress bar animation and resets it."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(0)

    def set_progress(self, value):
        """Sets the progress bar to a specific value (0-100)."""
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(max(0, min(100, value))) # Clamp value between 0 and 100

# --- ParticleBackground Class ---
class ParticleBackground(Canvas):
    """Creates an animated particle background effect"""
    def __init__(self, parent, bg_color="#1A103C", particle_color="#453AA8", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.configure(bg=bg_color)
        
        self.bg_color = bg_color
        self.particle_color = particle_color
        self.particles = []
        self.animation_running = False
        self.num_particles = 30
        
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event):
        """Reset particles when window is resized"""
        self.width = event.width
        self.height = event.height
        self._initialize_particles()
        
        if not self.animation_running:
            self.start_animation()
    
    def _initialize_particles(self):
        """Create random particles"""
        self.delete("all")  # Clear canvas
        self.particles = []
        
        for i in range(self.num_particles):
            # Create particles with random properties
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.uniform(2, 6)
            speed = random.uniform(0.3, 1.0)
            direction = random.uniform(0, 2 * math.pi)
            
            # Calculate velocity components
            dx = math.cos(direction) * speed
            dy = math.sin(direction) * speed
            
            # Create oval for particle
            particle_id = self.create_oval(
                x-size/2, y-size/2, x+size/2, y+size/2,
                fill=self._adjust_particle_color(size),
                outline="",
                tags="particle"
            )
            
            self.particles.append({
                'id': particle_id,
                'x': x, 'y': y,
                'dx': dx, 'dy': dy,
                'size': size
            })
    
    def _adjust_particle_color(self, size):
        """Creates a slightly different color based on particle size"""
        base_color = self._hex_to_rgb(self.particle_color)
        # Adjust brightness based on size
        adjustment = int((size - 2) * 15)  # -15 to +15 adjustment
        
        new_r = min(255, max(0, base_color[0] + adjustment))
        new_g = min(255, max(0, base_color[1] + adjustment))
        new_b = min(255, max(0, base_color[2] + adjustment))
        
        return f'#{new_r:02x}{new_g:02x}{new_b:02x}'
    
    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    def start_animation(self):
        """Start particle animation"""
        self.animation_running = True
        self._animate()
    
    def stop_animation(self):
        """Stop particle animation"""
        self.animation_running = False
    
    def _animate(self):
        """Animate particles"""
        if not self.animation_running:
            return
            
        for p in self.particles:
            # Update position
            p['x'] += p['dx']
            p['y'] += p['dy']
            
            # Wrap around screen edges
            if p['x'] < -10:
                p['x'] = self.width + 10
            elif p['x'] > self.width + 10:
                p['x'] = -10
                
            if p['y'] < -10:
                p['y'] = self.height + 10
            elif p['y'] > self.height + 10:
                p['y'] = -10
            
            # Move the oval
            self.coords(
                p['id'], 
                p['x']-p['size']/2, p['y']-p['size']/2, 
                p['x']+p['size']/2, p['y']+p['size']/2
            )
        
        # Schedule next animation frame
        self.after(50, self._animate)
        
    def lower(self, tagOrId=None):
        """Override to support both widget lowering and canvas item lowering"""
        if tagOrId:
            # If a tag or ID is provided, use canvas tag_lower
            Canvas.tag_lower(self, tagOrId)
        else:
            # If no arguments, use Tkinter's widget lowering 
            # Call the tk directly with proper arguments to avoid infinite recursion
            self.tk.call('lower', self._w)

# --- AnimatedLoadingIndicator Class ---
class AnimatedLoadingIndicator(Canvas):
    """Creates an animated chart loading indicator"""
    def __init__(self, parent, width=100, height=100, color="#00CCB8", **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        self.configure(bg=parent.cget("bg"))
        
        self.width = width
        self.height = height
        self.color = color
        self.animation_running = False
        self.angle = 0
        
        # Text message below spinner
        self.message = "Loading data..."
        self.create_text(width/2, height*0.7, text=self.message, fill="#8A7CB4", font=("Segoe UI", 10))
        
    def set_message(self, message):
        """Update the loading message"""
        self.message = message
        self.delete("message")
        self.create_text(self.width/2, self.height*0.7, text=self.message, fill="#8A7CB4", 
                        font=("Segoe UI", 10), tags="message")
    
    def start_animation(self):
        """Start the loading animation"""
        self.animation_running = True
        self._animate()
    
    def stop_animation(self):
        """Stop the loading animation"""
        self.animation_running = False
        
    def _animate(self):
        """Animate the loading indicator"""
        if not self.animation_running:
            return
            
        self.delete("spinner")
        
        # Center coordinates
        cx, cy = self.width/2, self.height*0.4
        radius = min(self.width, self.height) * 0.3
        
        # Draw arcs of the spinner with varying thickness
        for i in range(8):
            start_angle = self.angle + i * 45
            extent = 30
            thickness = int(10 - i * 1.1)  # Decreasing thickness
            
            # Skip if thickness becomes too small
            if thickness < 1:
                continue
                
            # Calculate arc coordinates
            x0 = cx - radius
            y0 = cy - radius
            x1 = cx + radius
            y1 = cy + radius
            
            # Adjust color based on position in sequence
            r, g, b = self._hex_to_rgb(self.color)
            opacity = 255 - i * 30
            color = f"#{r:02x}{g:02x}{b:02x}{opacity:02x}"
            
            # Create arc
            self.create_arc(x0, y0, x1, y1, 
                          start=start_angle, extent=extent,
                          style="arc", width=thickness, 
                          outline=color, tags="spinner")
        
        # Update angle for next frame
        self.angle = (self.angle + 5) % 360
        
        # Schedule next frame
        self.after(40, self._animate)
        
    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        if len(h) == 8: h = h[:6]  # Strip alpha if present
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# --- ModernHeader Class ---
class ModernHeader(Frame):
    """Creates a modern header with animated icons and title"""
    def __init__(self, parent, title="EpiForecast", subtitle="Disease Tracker", icon="🦠", **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=parent.cget("bg") if "bg" not in kwargs else kwargs["bg"])
        
        # Header layout
        self.columnconfigure(0, weight=0)  # Icon
        self.columnconfigure(1, weight=1)  # Title
        
        # Create animated icon
        self.icon_canvas = Canvas(self, width=40, height=40, highlightthickness=0, bg=self.cget("bg"))
        self.icon_canvas.grid(row=0, column=0, rowspan=2, padx=(0, 10), pady=5)
        
        self.icon_text = icon
        self.icon_item = self.icon_canvas.create_text(20, 20, text=icon, font=("Segoe UI Symbol", 24), fill="#00CCB8")
        
        # Start icon animation
        self._animate_icon()
        
        # Title with gradient effect
        self.title_label = Label(self, text=title, font=("Segoe UI", 18, "bold"), bg=self.cget("bg"), fg="#E0E0FF")
        self.title_label.grid(row=0, column=1, sticky="sw")
        
        # Subtitle
        self.subtitle_label = Label(self, text=subtitle, font=("Segoe UI", 10), bg=self.cget("bg"), fg="#8A7CB4")
        self.subtitle_label.grid(row=1, column=1, sticky="nw")
        
    def _animate_icon(self):
        """Animate the icon with a subtle floating effect"""
        def float_animation():
            # Get current position
            x, y = self.icon_canvas.coords(self.icon_item)
            
            # Calculate new position with sine wave for smooth floating
            time_val = time.time() * 2  # Speed factor
            new_y = 20 + math.sin(time_val) * 3  # Amplitude of 3px
            
            # Update position
            self.icon_canvas.coords(self.icon_item, x, new_y)
            
            # Schedule next frame
            self.after(50, float_animation)
            
        # Start animation
        float_animation()

# --- ThemeToggle Class ---
class ThemeToggle(Frame):
    """Toggle button to switch between dark and light themes"""
    def __init__(self, parent, initial_theme="dark", command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=parent.cget("bg"))
        
        self.theme = initial_theme
        self.command = command
        
        # Create toggle button
        self.width = 50
        self.height = 24
        
        self.canvas = Canvas(self, width=self.width, height=self.height, 
                           highlightthickness=0, bg=self.cget("bg"))
        self.canvas.pack(padx=5, pady=5)
        
        # Draw the toggle background
        self.bg_dark = "#1A103C"
        self.bg_light = "#E0E0FF"
        self.accent_color = "#00CCB8"
        
        # Create the background and knob
        self._draw_toggle()
        
        # Bind click event
        self.canvas.bind("<Button-1>", self._toggle)
        
    def _draw_toggle(self):
        """Draw the toggle switch based on current theme"""
        self.canvas.delete("all")
        
        # Background color based on theme
        bg_color = self.bg_dark if self.theme == "dark" else self.bg_light
        fg_color = self.bg_light if self.theme == "dark" else self.bg_dark
        
        # Draw rounded rectangle for background
        self.canvas.create_rounded_rectangle(2, 2, self.width-2, self.height-2, 
                                          radius=self.height//2, fill=bg_color, width=0)
        
        # Draw knob position based on theme
        knob_x = self.width - self.height//2 - 2 if self.theme == "dark" else self.height//2 + 2
        
        # Draw sun/moon icon based on theme
        if self.theme == "dark":
            # Moon icon (crescent)
            self.canvas.create_oval(knob_x-8, 4, knob_x+8, self.height-4, fill=self.accent_color, outline="")
            self.canvas.create_oval(knob_x-3, 4, knob_x+13, self.height-4, fill=bg_color, outline="")
            # Stars
            for i in range(3):
                star_x = 10 + i * 10
                star_y = self.height // 2 + (i % 2) * 5 - 2
                self.canvas.create_text(star_x, star_y, text="✦", fill=fg_color, font=("Segoe UI Symbol", 7))
        else:
            # Sun icon
            self.canvas.create_oval(knob_x-8, 4, knob_x+8, self.height-4, fill="#FFC107", outline="")
            # Sun rays
            for i in range(8):
                angle = i * 45 * math.pi / 180
                ray_length = 5
                x1 = knob_x + math.cos(angle) * 8
                y1 = self.height // 2 + math.sin(angle) * 8
                x2 = knob_x + math.cos(angle) * (8 + ray_length)
                y2 = self.height // 2 + math.sin(angle) * (8 + ray_length)
                self.canvas.create_line(x1, y1, x2, y2, fill="#FFC107", width=2)
    
    def _toggle(self, event):
        """Toggle between dark and light themes"""
        self.theme = "light" if self.theme == "dark" else "dark"
        self._draw_toggle()
        
        # Trigger animation
        self._animate_toggle()
        
        # Call command if provided
        if self.command:
            self.command(self.theme)
            
    def _animate_toggle(self):
        """Smooth animation for the toggle switch"""
        pass  # Implement animation if needed
    
    def get_theme(self):
        """Return current theme"""
        return self.theme

# Add rounded rectangle capability to Canvas
if not hasattr(Canvas, 'create_rounded_rectangle'):
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)
        
    Canvas.create_rounded_rectangle = _create_rounded_rectangle