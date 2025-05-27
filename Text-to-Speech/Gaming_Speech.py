import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import pytesseract
from PIL import Image
import mss
import mss.tools
import pyttsx3
import threading
import edge_tts
import asyncio
import pyautogui
import numpy as np
from PIL import ImageFilter
import os
import tempfile
import winsound
from pydub import AudioSegment
import cv2
import easyocr

# Initialize EasyOCR reader
# This needs to be done once
reader = easyocr.Reader(['en'])

# Set Tesseract path (still needed for Tesseract checks, but OCR will use EasyOCR)
TESSERACT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Tesseract-OCR", "tesseract.exe")
if not os.path.exists(TESSERACT_PATH):
    print(f"Warning: Tesseract not found at {TESSERACT_PATH}")
    # Try to find Tesseract in the current directory
    alt_path = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
    if os.path.exists(alt_path):
        TESSERACT_PATH = alt_path
        print(f"Found Tesseract at alternative path: {TESSERACT_PATH}")
    else:
        print("Error: Tesseract not found. OCR functionality will not work.")
else:
    print(f"Tesseract found at: {TESSERACT_PATH}")

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Verify Tesseract language data exists
tessdata_path = os.path.join(os.path.dirname(TESSERACT_PATH), "tessdata")
eng_traineddata_path = os.path.join(tessdata_path, "eng.traineddata")

if not os.path.exists(tessdata_path):
    print(f"Error: Tesseract tessdata directory not found at {tessdata_path}")
    messagebox.showerror("Tesseract Data Error", f"Tesseract tessdata directory not found. Please ensure the Tesseract installation is complete.")
elif not os.path.exists(eng_traineddata_path):
    print(f"Error: Tesseract English language data (eng.traineddata) not found at {eng_traineddata_path}")
    messagebox.showerror("Tesseract Data Error", f"Tesseract English language data (eng.traineddata) not found. Please ensure the English language pack is installed for Tesseract.")
else:
    print("Tesseract tessdata and eng.traineddata found.")

class GamingSpeechWindow:
    def __init__(self, parent):
        self.parent = parent
        # Store reference to main window
        self.main_window = parent
        
        # Create the gaming speech window
        self.window = tk.Toplevel(parent)
        self.window.title("Gaming Speech Mode")
        self.window.geometry("350x250")
        self.window.minsize(350, 250)
        
        # Initialize status variable
        self.status_var = tk.StringVar(value="Ready")
        
        # Initialize TTS settings
        self.settings = {
            'always_on_top': tk.BooleanVar(value=True),  # Set to True by default
            'transparency': tk.IntVar(value=100),
            'compact_mode': tk.BooleanVar(value=False),
            'high_contrast': tk.BooleanVar(value=False),
            'auto_hide': tk.BooleanVar(value=False),
            'text_size': tk.IntVar(value=12),
            'show_box': tk.BooleanVar(value=True),
            'hotkey': tk.StringVar(value="F1"),
            'voice': tk.StringVar(value="en-US-GuyNeural")
        }
        
        # Add stop flag and thread tracking
        self.stop_flag = False
        self.tts_thread = None
        self.is_reading = False
        
        # Selection box variables
        self.selection_mode = False
        self.selection_window = None
        self.selection_canvas = None
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.selection_rect = None
        self.selection_box = None
        self.screenshot = None
        self.rect = None
        self.canvas = None
        self.top_level = None
        
        # Selection box visibility and opacity
        self.selection_box_visible = True
        self.box_opacity = tk.DoubleVar(value=0.5)
        self.selection_box_geometry = None
        
        # Create UI
        self.create_ui()
        
        # Apply initial settings
        self.apply_settings()
        
        # Register hotkeys
        self.register_hotkeys()
        
        # Make window modal and set up close handler
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set window to be always on top initially
        self.window.attributes('-topmost', True)
        
        # Ensure the window is visible and focused
        self.window.deiconify()
        self.window.focus_force()
        
        # Minimize main window after a short delay
        self.window.after(100, self.minimize_main_window)

    def minimize_main_window(self):
        """Minimize the main window"""
        try:
            # Iconify (minimize) the main window
            self.main_window.iconify()
            print("Main window minimized")
            
            # Ensure gaming speech window stays visible and focused
            self.window.deiconify()
            self.window.focus_force()
            self.window.lift()
        except Exception as e:
            print(f"Error minimizing main window: {e}")

    def create_ui(self):
        # Create menu bar
        self.menu_bar = tk.Menu(self.window)
        self.window.config(menu=self.menu_bar)

        # Create File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Add items to File menu
        file_menu.add_command(label="Instructions", command=self.show_instructions)
        file_menu.add_separator()
        file_menu.add_command(label="Copy to Main Window", command=self.copy_to_main)
        file_menu.add_command(label="Clear Text", command=self.clear_text)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        # Main frame
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar at the top
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_label = tk.Label(status_frame, textvariable=self.status_var, fg="gray")
        status_label.pack(side=tk.LEFT)

        # Settings section
        settings_frame = tk.LabelFrame(main_frame, text="Settings")
        settings_frame.pack(fill=tk.X, pady=5)

        # Left settings
        left_frame = tk.Frame(settings_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right settings
        right_frame = tk.Frame(settings_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left checkboxes
        tk.Checkbutton(left_frame, text="Always on Top", variable=self.settings['always_on_top'], command=self.apply_settings).pack(anchor=tk.W)
        tk.Checkbutton(left_frame, text="Compact Mode", variable=self.settings['compact_mode'], command=self.apply_settings).pack(anchor=tk.W)
        tk.Checkbutton(left_frame, text="High Contrast", variable=self.settings['high_contrast'], command=self.apply_settings).pack(anchor=tk.W)
        tk.Checkbutton(left_frame, text="Show Box", variable=self.settings['show_box'], command=self.toggle_box_visibility).pack(anchor=tk.W)

        # Right checkboxes and controls
        tk.Checkbutton(right_frame, text="Hide Box", variable=self.settings['auto_hide'], command=self.toggle_box_visibility).pack(anchor=tk.W)

        # Voice selection
        voice_frame = tk.Frame(right_frame)
        voice_frame.pack(fill=tk.X, pady=2)
        tk.Label(voice_frame, text="Voice:").pack(side=tk.LEFT)
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.settings['voice'], state="readonly", width=15)
        self.voice_combo['values'] = [
            "en-US-GuyNeural",
            "en-US-AriaNeural",
            "en-GB-RyanNeural",
            "en-GB-SoniaNeural"
        ]
        self.voice_combo.pack(side=tk.LEFT, padx=5)

        # Box opacity slider
        trans_frame = tk.Frame(right_frame)
        trans_frame.pack(fill=tk.X, pady=2)
        tk.Label(trans_frame, text="Box Opacity:").pack(side=tk.LEFT)
        trans_slider = tk.Scale(trans_frame, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=self.box_opacity, command=self.update_box_opacity, length=100)
        trans_slider.pack(side=tk.LEFT, padx=5)

        # Panel opacity slider
        panel_opacity_frame = tk.Frame(right_frame)
        panel_opacity_frame.pack(fill=tk.X, pady=2)
        tk.Label(panel_opacity_frame, text="Panel Opacity:").pack(side=tk.LEFT)
        self.panel_opacity = tk.DoubleVar(value=1.0)
        panel_slider = tk.Scale(panel_opacity_frame, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=self.panel_opacity, command=self.update_panel_opacity, length=100)
        panel_slider.pack(side=tk.LEFT, padx=5)

        # Control buttons section
        control_frame = tk.LabelFrame(main_frame, text="Controls")
        control_frame.pack(fill=tk.X, pady=5)

        # Use grid for button layout
        button_style = {'font': ("Arial", 8), 'padx': 1, 'pady': 1}
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)
        button_frame.grid_columnconfigure(4, weight=1)

        tk.Button(
            button_frame,
            text="Capture",
            command=self.start_selection,
            **button_style
        ).grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        tk.Button(
            button_frame,
            text="Read",
            command=self.read_box_text,
            **button_style
        ).grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        tk.Button(
            button_frame,
            text="Stop",
            command=self.stop_reading,
            **button_style
        ).grid(row=0, column=2, padx=1, pady=1, sticky="ew")
        tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_text,
            **button_style
        ).grid(row=0, column=3, padx=1, pady=1, sticky="ew")
        tk.Button(
            button_frame,
            text="Copy",
            command=self.copy_to_main,
            **button_style
        ).grid(row=0, column=4, padx=1, pady=1, sticky="ew")

        # Text area section
        text_frame = tk.LabelFrame(main_frame, text="Text")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create text area
        self.text_area = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", self.settings['text_size'].get()),
            height=8,  # Reduced height
            yscrollcommand=scrollbar.set
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.text_area.yview)

    def update_panel_opacity(self, value):
        """Update panel opacity"""
        self.window.attributes('-alpha', self.panel_opacity.get())

    def start_selection(self):
        """Start screen selection mode"""
        if self.selection_mode:
            return

        self.selection_mode = True
        self.status_var.set("Click and drag to select text on screen. Press ESC to cancel.")
        print("Starting selection mode...")

        # Hide gaming speech window during selection
        self.window.withdraw()

        # Use window.after for GUI thread safety
        self.window.after(150, self._initiate_capture_overlay)

    def _initiate_capture_overlay(self):
        """Takes screenshot of ALL monitors and creates overlay window covering them"""
        try:
            # Use MSS to get virtual screen geometry and capture it
            with mss.mss() as sct:
                # Monitor 0 provides the bounding box for the entire virtual screen
                self.virtual_screen_geo = sct.monitors[0]
                print(f"Virtual screen geometry: {self.virtual_screen_geo}")

                # Grab the entire virtual screen
                sct_img = sct.grab(self.virtual_screen_geo)

                # Convert the MSS BGRA image to a PIL Image (RGB)
                self.screenshot = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            print(f"Virtual screenshot taken: {self.screenshot.size}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screen using MSS: {str(e)}")
            print(f"Screen capture error (MSS): {e}")
            self.selection_mode = False
            if self.window: self.window.deiconify()
            self.status_var.set("Screen capture failed. Ready.")
            return

        # Create a Toplevel window that covers the ENTIRE virtual screen
        self.top_level = tk.Toplevel(self.window)

        # Set geometry explicitly to cover the virtual screen
        geo_str = f"{self.virtual_screen_geo['width']}x{self.virtual_screen_geo['height']}+{self.virtual_screen_geo['left']}+{self.virtual_screen_geo['top']}"
        self.top_level.geometry(geo_str)
        print(f"Setting overlay geometry: {geo_str}")

        # Make it borderless, always on top, and semi-transparent
        self.top_level.overrideredirect(True)
        self.top_level.attributes('-topmost', True)
        self.top_level.attributes('-alpha', 0.4)  # Semi-transparent

        # Create canvas for drawing selection rectangle
        self.canvas = tk.Canvas(self.top_level, cursor="cross", bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Store the screen offset for coordinate conversion
        self.screen_offset_x = self.virtual_screen_geo['left']
        self.screen_offset_y = self.virtual_screen_geo['top']

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Escape key to cancel
        self.top_level.bind("<Escape>", self.cancel_selection)
        self.top_level.focus_force()  # Ensure it captures key presses

        # Failsafe: auto-close overlay after 10 seconds if nothing happens
        self.top_level.after(10000, self._failsafe_overlay_close)

    def _failsafe_overlay_close(self):
        if self.top_level:
            print("[Failsafe] Overlay auto-closed after timeout.")
            self.cancel_selection()

    def on_mouse_down(self, event):
        """Handle mouse button press"""
        print("Mouse down event triggered")
        self.start_x = event.x
        self.start_y = event.y
        self.current_x = event.x
        self.current_y = event.y
        
        # Delete any existing rectangle
        if hasattr(self, 'rect') and self.rect:
            self.canvas.delete(self.rect)
            self.rect = None
            
        # Create new rectangle
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.current_x, self.current_y,
            outline='red', width=2
        )
        print(f"Created rectangle at ({self.start_x}, {self.start_y})")

    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if not hasattr(self, 'rect') or not self.rect:
            return
            
        self.current_x = event.x
        self.current_y = event.y
        
        # Update rectangle coordinates
        self.canvas.coords(
            self.rect,
            self.start_x, self.start_y,
            self.current_x, self.current_y
        )

    def on_mouse_up(self, event):
        """Handle mouse button release"""
        print("Mouse up event triggered")
        if not hasattr(self, 'rect') or not self.rect:
            print("No rectangle found on mouse up")
            return
            
        # Get final coordinates
        self.current_x = event.x
        self.current_y = event.y
        
        # Calculate box dimensions
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        print(f"Selection dimensions: ({x1}, {y1}) to ({x2}, {y2})")
        
        # Only create box if there's a valid selection
        if x2 - x1 > 5 and y2 - y1 > 5:
            print("Valid selection detected, creating box")
            # Convert coordinates to screen coordinates
            # The coordinates from the overlay are relative to the overlay window,
            # which covers the virtual screen. We need to convert them to absolute
            # screen coordinates using the virtual screen geometry.
            screen_x = x1 + self.virtual_screen_geo['left']
            screen_y = y1 + self.virtual_screen_geo['top']
            width = x2 - x1
            height = y2 - y1
            
            # Store the geometry in screen coordinates
            self.selection_box_geometry = (int(screen_x), int(screen_y), int(width), int(height))
            print(f"Screen coordinates: ({screen_x}, {screen_y}) size {width}x{height}")
            
            # Clean up selection overlay
            if self.top_level:
                self.top_level.destroy()
                self.top_level = None
            self.canvas = None
            self.rect = None
            self.selection_mode = False
            
            # Show gaming speech window and create selection box
            self.window.deiconify()
            self.create_selection_box()
        else:
            print("Selection too small, cancelling")
            self.cancel_selection()

    def cancel_selection(self, event=None):
        print("[DEBUG] Selection cancelled.")
        if self.top_level:
            self.top_level.destroy()
            self.top_level = None
        self.canvas = None
        self.rect = None
        self.selection_mode = False
        self.window.deiconify()
        self.status_var.set("Selection cancelled. Ready.")

    def create_selection_box(self):
        """Create a visible selection box window"""
        print("Creating selection box")
        # Destroy any existing box first
        if self.selection_box:
            self.selection_box.destroy()
            self.selection_box = None
            
        if not self.selection_box_geometry:
            print("No selection box geometry available")
            return
            
        x, y, w, h = self.selection_box_geometry
        print(f"Creating box at ({x}, {y}) with size {w}x{h}")
        
        # Create the selection box window
        self.selection_box = tk.Toplevel(self.window)
        self.selection_box.overrideredirect(True)
        self.selection_box.attributes('-topmost', True)
        
        # Set the geometry using screen coordinates
        self.selection_box.geometry(f"{w}x{h}+{x}+{y}")
        self.selection_box.config(bg='red')
        self.selection_box.attributes('-alpha', self.box_opacity.get())
        
        # Allow dragging from anywhere inside the box
        self.selection_box.bind('<ButtonPress-1>', self._start_drag_box)
        self.selection_box.bind('<B1-Motion>', self._on_drag_box)
        
        # Allow resizing from any edge/corner
        self.selection_box.bind('<Motion>', self._on_motion_box)
        self.selection_box.bind('<ButtonPress-3>', self._start_resize_box)
        self.selection_box.bind('<B3-Motion>', self._on_resize_box)
        
        self.selection_box_visible = True
        self.settings['show_box'].set(True)
        print("Selection box created successfully")

    def _start_drag_box(self, event):
        if self._resize_mode:
            return  # Don't drag if resizing
        self._drag_offset = (event.x, event.y)
        self._drag_geom = (self.selection_box.winfo_x(), self.selection_box.winfo_y())

    def _on_drag_box(self, event):
        if self._resize_mode:
            return
        dx, dy = self._drag_offset
        x0, y0 = self._drag_geom
        x = x0 + event.x - dx
        y = y0 + event.y - dy
        w = self.selection_box.winfo_width()
        h = self.selection_box.winfo_height()
        self.selection_box.geometry(f"{w}x{h}+{x}+{y}")
        self.selection_box_geometry = (x, y, w, h)

    def _on_motion_box(self, event):
        # Change cursor and set resize mode based on position
        x, y = event.x, event.y
        w, h = self.selection_box.winfo_width(), self.selection_box.winfo_height()
        border = 8
        if x < border and y < border:
            self.selection_box.config(cursor='top_left_corner')
            self._resize_mode = 'nw'
        elif x > w - border and y < border:
            self.selection_box.config(cursor='top_right_corner')
            self._resize_mode = 'ne'
        elif x < border and y > h - border:
            self.selection_box.config(cursor='bottom_left_corner')
            self._resize_mode = 'sw'
        elif x > w - border and y > h - border:
            self.selection_box.config(cursor='bottom_right_corner')
            self._resize_mode = 'se'
        elif x < border:
            self.selection_box.config(cursor='left_side')
            self._resize_mode = 'w'
        elif x > w - border:
            self.selection_box.config(cursor='right_side')
            self._resize_mode = 'e'
        elif y < border:
            self.selection_box.config(cursor='top_side')
            self._resize_mode = 'n'
        elif y > h - border:
            self.selection_box.config(cursor='bottom_side')
            self._resize_mode = 's'
        else:
            self.selection_box.config(cursor='fleur')
            self._resize_mode = None

    def _start_resize_box(self, event):
        self._resize_start = (event.x, event.y, self.selection_box.winfo_x(), self.selection_box.winfo_y(), self.selection_box.winfo_width(), self.selection_box.winfo_height(), self._resize_mode)

    def _on_resize_box(self, event):
        x0, y0, win_x, win_y, w0, h0, mode = self._resize_start
        min_w, min_h = 40, 30
        dx = event.x - x0
        dy = event.y - y0
        x, y, w, h = win_x, win_y, w0, h0
        if mode == 'nw':
            x = win_x + dx
            y = win_y + dy
            w = w0 - dx
            h = h0 - dy
        elif mode == 'ne':
            y = win_y + dy
            w = w0 + dx
            h = h0 - dy
        elif mode == 'sw':
            x = win_x + dx
            w = w0 - dx
            h = h0 + dy
        elif mode == 'se':
            w = w0 + dx
            h = h0 + dy
        elif mode == 'w':
            x = win_x + dx
            w = w0 - dx
        elif mode == 'e':
            w = w0 + dx
        elif mode == 'n':
            y = win_y + dy
            h = h0 - dy
        elif mode == 's':
            h = h0 + dy
        w = max(min_w, w)
        h = max(min_h, h)
        self.selection_box.geometry(f"{int(w)}x{int(h)}+{int(x)}+{int(y)}")
        self.selection_box_geometry = (int(x), int(y), int(w), int(h))

    def toggle_box_visibility(self, *args):
        """Toggle selection box visibility"""
        if self.settings['auto_hide'].get():
            # Hide the selection box but keep it active
            if self.selection_box:
                self.selection_box.withdraw()
            self.selection_box_visible = False
            # Update status to show box is hidden but active
            self.status_var.set("Box hidden but active")
        else:
            # Show the selection box if show_box is also enabled
            if self.selection_box and self.settings['show_box'].get():
                self.selection_box.deiconify()
                self.selection_box_visible = True
                self.status_var.set("Ready")

    def update_box_opacity(self, *args):
        """Update selection box opacity"""
        if self.selection_box:
            self.selection_box.attributes('-alpha', self.box_opacity.get())

    def clear_text(self):
        """Clear text and selection box"""
        self.text_area.delete(1.0, tk.END)
        if self.selection_box:
            self.selection_box.destroy()
            self.selection_box = None
            self.selection_box_visible = False
            self.selection_box_geometry = None

    def update_hotkey(self, event=None):
        """Update the hotkey for reading text"""
        try:
            # Remove old hotkey
            keyboard.remove_hotkey(self.settings['hotkey'].get())
            
            # Add new hotkey
            keyboard.add_hotkey(
                self.settings['hotkey'].get(),
                self.read_selection
            )
        except Exception as e:
            print(f"Error updating hotkey: {e}")

    def read_selection(self):
        """Read the text in the current selection"""
        if self.text_area.get(1.0, tk.END).strip():
            self.start_reading()

    def apply_settings(self, *args):
        # Apply always on top
        self.window.attributes('-topmost', self.settings['always_on_top'].get())
        
        # Apply transparency
        alpha = self.settings['transparency'].get() / 100
        self.window.attributes('-alpha', alpha)
        
        # Apply compact mode
        if self.settings['compact_mode'].get():
            self.window.geometry("300x200")
        else:
            self.window.geometry("350x250")
        
        # Apply high contrast
        if self.settings['high_contrast'].get():
            self.text_area.configure(
                fg='#FFFFFF',
                bg='#000000'
            )
        else:
            self.text_area.configure(
                fg='#000000',
                bg='#FFFFFF'
            )
        
        # Apply text size
        self.text_area.configure(
            font=("Arial", self.settings['text_size'].get())
        )
        
        # Update selection box if it exists
        if self.selection_box:
            self.selection_box.attributes('-topmost', self.settings['always_on_top'].get())
            self.selection_box.attributes('-alpha', alpha)
            self.toggle_box_visibility()
            
        # Ensure window stays visible and focused
        self.window.deiconify()
        self.window.focus_force()
        self.window.lift()

    def register_hotkeys(self):
        """Register hotkeys for the application"""
        try:
            # Register hotkey for capturing text
            keyboard.add_hotkey(
                'ctrl+shift+c',
                self.start_selection
            )
            
            # Register hotkey for reading text
            keyboard.add_hotkey(
                'ctrl+shift+r',
                self.read_box_text
            )
            
            # Register hotkey for stopping reading
            keyboard.add_hotkey(
                'ctrl+shift+s',
                self.stop_reading
            )
            
            # Register hotkey for toggling box visibility
            keyboard.add_hotkey(
                'ctrl+shift+h',
                self.toggle_box_visibility
            )
            
            # Register hotkey for copying to main window
            keyboard.add_hotkey(
                'ctrl+shift+g',
                self.copy_to_main
            )
            
        except Exception as e:
            print(f"Error registering hotkeys: {e}")

    async def read_text_with_edge_tts(self, text):
        """Read text using Edge TTS"""
        try:
            if self.stop_flag:
                return
                
            # Create new Communicate instance with text
            communicate = edge_tts.Communicate(text, self.settings['voice'].get())
            
            # Create temporary directory for audio files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_mp3 = os.path.join(temp_dir, "temp_audio.mp3")
                
                # Save audio
                await communicate.save(temp_mp3)
                
                # Play the audio file using subprocess
                import subprocess
                process = subprocess.Popen(['ffplay', '-autoexit', '-nodisp', temp_mp3])
                
                # Wait for the process to finish or stop flag
                while process.poll() is None and not self.stop_flag:
                    await asyncio.sleep(0.1)
                
                # Kill the process if stop flag is set
                if self.stop_flag:
                    process.terminate()
                    process.wait()
                
        except Exception as e:
            print(f"Error in Edge TTS: {e}")
            if not self.stop_flag:  # Only show error if not stopped
                messagebox.showerror("Error", f"Failed to read text: {str(e)}")

    def start_reading(self):
        """Start reading the text"""
        if self.is_reading:  # Don't start if already reading
            return
            
        # Reset stop flag
        self.stop_flag = False
        self.is_reading = True
        
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.is_reading = False
            return
            
        # Use Edge TTS
        def run_edge_tts():
            try:
                asyncio.run(self.read_text_with_edge_tts(text))
            except Exception as e:
                print(f"Error in Edge TTS thread: {e}")
            finally:
                self.is_reading = False
                self.stop_flag = False
                # Force update UI
                self.window.after(0, self.window.update_idletasks)
        
        # Store the thread for cleanup
        self.tts_thread = threading.Thread(target=run_edge_tts, daemon=True)
        self.tts_thread.start()

    def stop_reading(self):
        """Stop reading"""
        print("Stopping speech...")
        self.stop_flag = True
        
        try:
            # Kill any running ffplay processes
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'ffplay.exe'], capture_output=True)
            
            # Reset states immediately
            self.is_reading = False
            self.stop_flag = False
            
            # Update status
            self.status_var.set("Speech stopped")
            print("Speech stopped successfully")
            
            # Force update UI
            self.window.update_idletasks()
            
        except Exception as e:
            print(f"Error stopping speech: {e}")
        finally:
            # Ensure these are always reset
            self.stop_flag = False
            self.is_reading = False
            # Force update UI
            self.window.update_idletasks()

    def copy_to_main(self):
        """Copy text to main window"""
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            self.parent.text_area.delete(1.0, tk.END)
            self.parent.text_area.insert(1.0, text)

    def on_close(self):
        """Handle window close"""
        print("Closing window...")
        try:
            # Set stop flag
            self.stop_flag = True
            
            # Kill any running ffplay processes
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'ffplay.exe'], capture_output=True)
            
            # Clean up selection box
            if self.selection_box:
                self.selection_box.destroy()
                self.selection_box = None
            
            # Restore main window before destroying this window
            try:
                self.main_window.deiconify()
                self.main_window.lift()
                print("Main window restored")
            except Exception as e:
                print(f"Error restoring main window: {e}")
            
            # Destroy the window
            self.window.destroy()
            print("Window closed successfully")
        except Exception as e:
            print(f"Error closing window: {e}")
            # Force quit if normal cleanup fails
            import sys
            sys.exit(1)

    def read_box_text(self):
        """Read text from the current selection box"""
        if not self.selection_box_geometry:
            messagebox.showinfo("No Box", "Please create a selection box first.")
            return
            
        x, y, w, h = self.selection_box_geometry
        print(f"Attempting to capture from box at ({x}, {y}) with size {w}x{h}")
        
        try:
            # Take screenshot
            print("Taking screenshot...")
            try:
                img = pyautogui.screenshot(region=(x, y, w, h))
                print(f"Screenshot taken, size: {img.size}")
            except Exception as e:
                print(f"Error taking screenshot: {e}")
                raise Exception("Failed to capture screen region")
            
            # Convert the PIL image to a format compatible with OpenCV
            cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # Save the original image for debugging
            original_image_path = os.path.join(os.getcwd(), "debug_original.png")
            cv2.imwrite(original_image_path, cv_image)
            print(f"Original image saved to {original_image_path}")

            # Scale up the image for better small text detection
            scale_factor = 2.0
            scaled_image = cv2.resize(cv_image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

            # Convert to grayscale
            gray_image = cv2.cvtColor(scaled_image, cv2.COLOR_BGR2GRAY)

            # Apply adaptive thresholding for better text/background separation
            try:
                thresh_image = cv2.adaptiveThreshold(
                    gray_image,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,  # Block size
                    2    # C constant
                )
            except Exception as e:
                print(f"Adaptive thresholding failed: {e}")
                thresh_image = gray_image

            # Apply slight blur to reduce noise while preserving text
            try:
                blurred_image = cv2.GaussianBlur(thresh_image, (3, 3), 0)
            except Exception as e:
                print(f"Blurring failed: {e}")
                blurred_image = thresh_image

            # Save the processed image for debugging
            processed_image_path = os.path.join(os.getcwd(), "debug_processed.png")
            cv2.imwrite(processed_image_path, blurred_image)
            print(f"Processed image saved to {processed_image_path}")

            # Try Tesseract with optimized configuration for small text
            print("Starting OCR with Tesseract...")
            try:
                # Configure Tesseract for small text
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()[]{}<>-_=+;:\'\" "'
                text = pytesseract.image_to_string(blurred_image, config=custom_config)
                print(f"OCR completed with Tesseract. Text: {text}")

            except Exception as e:
                print(f"Error during Tesseract OCR: {str(e)}")
                text = ""

            # If Tesseract fails or returns no text, try EasyOCR
            if not text.strip():
                print("Tesseract returned no text, trying EasyOCR...")
                try:
                    # Try with the scaled image for better small text detection
                    results = reader.readtext(scaled_image)
                    text = " ".join([result[1] for result in results])
                    print(f"OCR completed with EasyOCR. Text: {text}")
                except Exception as e:
                    print(f"Error during EasyOCR: {str(e)}")
                    text = ""

            if text.strip():
                # Update text area
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, text)
                # Start reading immediately
                self.start_reading()
            else:
                print("No text found in OCR result")
                messagebox.showinfo("No Text", "No text found in the selected area. Try adjusting the selection box or check the debug images.")
        except Exception as e:
            print(f"Error during capture/OCR: {str(e)}")
            messagebox.showerror("Error", f"Failed to capture or OCR: {str(e)}\nCheck the console for more details.")
            
            # Try to get more detailed error information
            import traceback
            print("Full error traceback:")
            print(traceback.format_exc())

    def show_instructions(self):
        """Show instructions in a new window"""
        instructions_window = tk.Toplevel(self.window)
        instructions_window.title("Instructions")
        instructions_window.geometry("400x300")
        instructions_window.transient(self.window)
        instructions_window.grab_set()

        # Make the window stay on top
        instructions_window.attributes('-topmost', True)

        # Create a frame with padding
        frame = tk.Frame(instructions_window, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create a text widget with scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(
            frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            padx=5,
            pady=5
        )
        text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        # Insert instructions
        instructions = """
Keyboard Shortcuts:
------------------
Ctrl+Shift+C: Create selection box
Ctrl+Shift+R: Read selected text
Ctrl+Shift+S: Stop reading
Ctrl+Shift+H: Toggle box visibility
Ctrl+Shift+G: Copy text to main window

Selection Box Controls:
---------------------
• Click and drag to create selection box
• Right-click and drag to resize box
• Left-click and drag to move box
• Use 'Hide Box' to temporarily hide the box

Tips:
-----
• The selection box can be hidden while still reading text
• Adjust box opacity to make it less intrusive
• Use panel opacity to make the entire window more transparent
• The box will remember its position and size
• You can have multiple boxes and switch between them

Settings:
--------
• Always on Top: Keep window above other windows
• Compact Mode: Reduce window size
• High Contrast: Change text colors for better visibility
• Show Box: Toggle selection box visibility
• Hide Box: Temporarily hide the box
• Box Opacity: Adjust selection box transparency
• Panel Opacity: Adjust window transparency
"""
        text.insert(tk.END, instructions)
        text.config(state=tk.DISABLED)  # Make text read-only

        # Add close button
        close_button = tk.Button(
            instructions_window,
            text="Close",
            command=instructions_window.destroy
        )
        close_button.pack(pady=5)
