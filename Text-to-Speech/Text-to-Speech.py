# Launcher code - ensures running from virtual environment
import os
import sys
import subprocess
import traceback

# Required dependencies:
# pip install -r requirements.txt
# Also requires Tesseract OCR engine to be installed on the system OR
# placed in a relative "Tesseract-OCR" folder.
# Note: The 'keyboard' library might require administrator/root privileges
#       on Linux/macOS and can sometimes be flagged by antivirus software.

import tkinter as tk
from tkinter import messagebox, ttk, filedialog, font, colorchooser
import threading
import pyttsx3
import keyboard
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageFilter
import pytesseract
import mss
import mss.tools
import venv
import site
import json
import colorsys
import math
import numpy as np
import sounddevice as sd
import wave
import edge_tts
import asyncio
import pydub
from pydub import AudioSegment
import tempfile
import queue
import time
import winsound

# Add new imports for speech recognition
import speech_recognition as sr
from scipy.io import wavfile
import re

# Add new imports at the top of the file
import docx
import PyPDF2
import io

# Add new import for GamingSpeechWindow
from Gaming_Speech import GamingSpeechWindow

# Default settings
DEFAULT_SETTINGS = {
    'font_family': 'Arial',
    'font_size': 10,
    'font_style': 'normal',
    'font_weight': 'normal',
    'text_wrap': 'word',
    'text_color': '#000000',
    'bg_color': '#FFFFFF'
}

# Add version information at the top of the file, after imports
VERSION = "v3.2.7"

def ensure_virtual_environment():
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Script directory: {script_dir}")
        
        # Change to the script's directory
        os.chdir(script_dir)
        print(f"Changed working directory to: {os.getcwd()}")
        
        # Check if we're already running from the virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("Already running in virtual environment")
            return True
        
        # Path to the virtual environment's Python executable
        venv_dir = os.path.join(script_dir, '.venv')
        if sys.platform == 'win32':
            python_exe = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_exe = os.path.join(venv_dir, 'bin', 'python')
        
        # If virtual environment doesn't exist, create it
        if not os.path.exists(python_exe):
            print("Creating virtual environment...")
            try:
                subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
                print("Virtual environment created successfully")
            except subprocess.CalledProcessError as e:
                print(f"Error creating virtual environment: {e}")
                return False
        
        # Verify the virtual environment is valid
        if not os.path.exists(python_exe):
            print(f"Error: Python executable not found at {python_exe}")
            return False
            
        # Restart the script using the virtual environment's Python
        print("Restarting with virtual environment...")
        script_path = os.path.abspath(__file__)
        print(f"Executing: {python_exe} {script_path}")
        
        # Use subprocess instead of os.execv
        try:
            subprocess.run([python_exe, script_path] + sys.argv[1:], check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Error running script in virtual environment: {e}")
            return False
        
    except Exception as e:
        print(f"Error in ensure_virtual_environment: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

def setup_portable_environment():
    """Set up portable environment with proper path handling"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Setting up portable environment in: {script_dir}")
        
        # Set up paths relative to the script directory
        global TESSERACT_PATH, SETTINGS_FILE, FFMPEG_PATH
        TESSERACT_PATH = os.path.join(script_dir, 'Tesseract-OCR', 'tesseract.exe')
        SETTINGS_FILE = os.path.join(script_dir, 'text_settings.json')
        FFMPEG_PATH = os.path.join(script_dir, 'ffmpeg')
        
        print(f"Tesseract path: {TESSERACT_PATH}")
        print(f"Settings file: {SETTINGS_FILE}")
        print(f"FFmpeg path: {FFMPEG_PATH}")
        
        # Add FFmpeg to PATH
        if FFMPEG_PATH not in os.environ['PATH']:
            os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ['PATH']
        
        # Set FFmpeg binary paths for pydub
        os.environ['FFMPEG_BINARY'] = os.path.join(FFMPEG_PATH, 'ffmpeg.exe')
        os.environ['FFPROBE_BINARY'] = os.path.join(FFMPEG_PATH, 'ffprobe.exe')
        
        # Ensure the settings file exists
        if not os.path.exists(SETTINGS_FILE):
            print("Creating default settings file...")
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(DEFAULT_SETTINGS, f, indent=4)
            print("Settings file created successfully")
            
        # Check for Tesseract-OCR
        if not os.path.exists(os.path.dirname(TESSERACT_PATH)):
            print("Warning: Tesseract-OCR folder not found")
            print("The application will try to use system-installed Tesseract if available")
            
        # Check for FFmpeg
        if not os.path.exists(FFMPEG_PATH):
            print("Warning: FFmpeg folder not found")
            print("Please run setup.bat to install FFmpeg")
            
        # Set up logging directory
        logs_dir = os.path.join(script_dir, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # Set up temp directory within the application folder
        temp_dir = os.path.join(script_dir, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        os.environ['TEMP'] = temp_dir
        os.environ['TMP'] = temp_dir
            
    except Exception as e:
        print(f"Error in setup_portable_environment: {e}")
        traceback.print_exc()
        raise

def find_tesseract():
    # First check the portable Tesseract-OCR folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    portable_tesseract = os.path.join(script_dir, 'Tesseract-OCR', 'tesseract.exe')
    
    if os.path.exists(portable_tesseract):
        return portable_tesseract
    
    # If not found in portable folder, try system PATH
    try:
        tesseract_cmd = 'tesseract'
        subprocess.run([tesseract_cmd, '--version'], capture_output=True, check=True)
        return tesseract_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

class ScreenTextSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Screen Text Selector {VERSION}")
        self.root.geometry("800x700")  # Initial size
        self.root.minsize(600, 500)    # Minimum size to prevent too small window

        # Load settings first, before creating UI
        self.settings = self.load_settings()
        print(f"Loaded settings: {self.settings}")  # Debug print

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save Text...", command=self.save_text)
        self.file_menu.add_command(label="Save as MP3...", command=self.save_as_mp3)
        self.file_menu.add_command(label="Load from MP3...", command=self.load_from_mp3)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Load from Text...", command=self.load_from_text)
        self.file_menu.add_command(label="Load from PDF...", command=self.load_from_pdf)
        self.file_menu.add_command(label="Load from Word...", command=self.load_from_word)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close)

        # Voice Settings menu
        self.voice_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Voice Settings", menu=self.voice_menu)
        self.voice_menu.add_command(label="Test Voice", command=self.test_voice_settings)
        self.voice_menu.add_separator()
        self.voice_menu.add_command(label="Voice Selection", command=self.show_voice_settings)
        self.voice_menu.add_command(label="Speed Settings", command=self.show_speed_settings)

        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Font Settings", command=self.show_font_settings)
        self.tools_menu.add_command(label="Speech to Text", command=self.start_speech_to_text)
        self.tools_menu.add_command(label="Audio File to Text", command=self.audio_file_to_text)
        self.tools_menu.add_command(label="Enhanced OCR", command=self.enhanced_ocr)
        self.tools_menu.add_command(label="Gaming Speech", command=self.show_gaming_speech)

        # About menu
        self.about_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="About", menu=self.about_menu)
        self.about_menu.add_command(label="About Application", command=self.show_about)
        self.about_menu.add_command(label="Dyslexic Features", command=self.show_dyslexic_features)

        # --- Tesseract Path Handling ---
        # Get application directory (works with USB drives)
        if getattr(sys, 'frozen', False):  # Running as compiled exe
            self.app_dir = os.path.dirname(sys.executable)
        else:  # Running as script
            self.app_dir = os.path.dirname(os.path.abspath(__file__))

        # Check if Tesseract path was already set
        tesseract_path_set = False
        try:
            if pytesseract.pytesseract.tesseract_cmd and os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                tesseract_path_set = True
        except AttributeError:
            pass

        # Try to find Tesseract in portable location first
        if not tesseract_path_set:
            # Check for portable Tesseract in the app directory
            portable_tesseract = os.path.join(self.app_dir, "Tesseract-OCR", "tesseract.exe")
            if os.path.exists(portable_tesseract):
                pytesseract.pytesseract.tesseract_cmd = portable_tesseract
                tesseract_path_set = True
                print(f"Using portable Tesseract: {portable_tesseract}")
            else:
                # Try common installation paths
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Tesseract-OCR\tesseract.exe'
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        tesseract_path_set = True
                        print(f"Using system Tesseract: {path}")
                        break

        if not tesseract_path_set:
            messagebox.showwarning("Tesseract Not Found",
                                 "Tesseract OCR not found. Please ensure Tesseract is either:\n"
                                 "1. Installed on this computer, or\n"
                                 "2. Placed in the 'Tesseract-OCR' folder next to this application")

        # Initialize text-to-speech engine *after* setting up default attributes
        self.current_rate = 150  # Default speed
        self.current_voice_id = None  # Default voice ID
        self.engine = None
        self.voices = []
        self.voice_descriptions = {}  # Store friendly descriptions of voices
        self.init_tts_engine()  # Initialize the engine with enhanced option

        # App state
        self.selection_mode = False
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.screenshot = None # This will be a PIL Image
        self.virtual_screen_geo = None # Store combined geometry {left, top, width, height}
        self.top_level = None
        self.canvas = None
        self.rect = None # Initialize rect attribute

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize Edge TTS (don't initialize here, create when needed)
        self.edge_tts_communicate = None
        
        # Audio recording variables
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None

        # Add audio playback control
        self.audio_thread = None
        self.is_playing = False
        self.audio_process = None

        # Create UI
        self.create_ui()

        # Apply saved settings to UI
        self.apply_saved_settings()

        # Register hotkeys
        try:
            keyboard.add_hotkey('ctrl+shift+s', self.start_selection)
            keyboard.add_hotkey('ctrl+shift+x', self.stop_speech)
            keyboard.add_hotkey('ctrl+shift+r', self.start_reading)
            print("Hotkeys registered (Ctrl+Shift+S, Ctrl+Shift+X, Ctrl+Shift+R)")
        except Exception as e:
             messagebox.showerror("Hotkey Error", f"Could not register hotkeys. Administrator rights might be needed.\nError: {e}")
             print(f"Error registering hotkeys: {e}")

    def apply_saved_settings(self):
        """Apply saved settings to the UI"""
        try:
            # Apply font settings to text area
            font_config = (
                self.settings['font_family'],
                self.settings['font_size'],
                self.settings['font_style'],
                self.settings['font_weight']
            )
            self.text_area.configure(
                font=font_config,
                wrap=self.settings['text_wrap'],
                fg=self.settings['text_color'],
                bg=self.settings['bg_color']
            )
            print("Applied saved settings to UI")
        except Exception as e:
            print(f"Error applying saved settings: {e}")
            messagebox.showerror("Settings Error", f"Could not apply saved settings: {str(e)}")

    def save_settings(self):
        """Save settings to config file"""
        try:
            # Ensure the settings directory exists
            settings_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(settings_dir, 'text_settings.json')
            
            # Create a copy of current settings
            current_settings = self.settings.copy()
            
            # Ensure all required settings are present
            for key, value in DEFAULT_SETTINGS.items():
                if key not in current_settings:
                    current_settings[key] = value
            
            # Save settings with proper formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=4)
            
            print(f"Settings saved successfully to: {config_path}")
            print(f"Saved settings: {current_settings}")  # Debug print
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            messagebox.showerror("Settings Error", f"Could not save settings: {str(e)}")
            return False

    def load_settings(self):
        """Load settings from config file"""
        try:
            settings_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(settings_dir, 'text_settings.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Ensure all default settings exist
                    for key, value in DEFAULT_SETTINGS.items():
                        if key not in settings:
                            settings[key] = value
                    print(f"Settings loaded successfully from: {config_path}")
                    print(f"Loaded settings: {settings}")  # Debug print
                    return settings
            else:
                print("No settings file found, using defaults")
                return DEFAULT_SETTINGS.copy()
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            messagebox.showerror("Settings Error", f"Could not load settings: {str(e)}")
            return DEFAULT_SETTINGS.copy()

    def init_tts_engine(self):
        """Initialize text-to-speech engine with enhanced voice options"""
        # Clean up existing engine if any
        if hasattr(self, 'engine') and self.engine is not None:
            try:
                self.engine.stop()
            except Exception as e:
                print(f"Minor error stopping previous TTS engine: {e}")
            self.engine = None

        try:
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            self.voice_descriptions = {}  # Reset descriptions
            
            # Create friendly descriptions for each voice
            for i, voice in enumerate(self.voices):
                gender = "Male" if "male" in voice.name.lower() or "david" in voice.name.lower() else "Female"
                lang = "English"  # Default, can be enhanced
                if "en-" in voice.id.lower():
                    lang = "English"
                elif "es-" in voice.id.lower():
                    lang = "Spanish"
                # Add more language detection as needed
                
                self.voice_descriptions[voice.id] = f"{gender} {lang} Voice - {voice.name}"

            # Apply rate (using pre-set default or previously stored value)
            self.engine.setProperty('rate', self.current_rate)

            # Determine and apply voice if not set
            if not self.current_voice_id and self.voices:
                # Try to find a female English voice first
                preferred_voice = None
                for voice in self.voices:
                    if "female" in voice.name.lower() and "en-" in voice.id.lower():
                        preferred_voice = voice
                        break
                
                # Fallback to first available voice
                self.current_voice_id = preferred_voice.id if preferred_voice else self.voices[0].id
                self.engine.setProperty('voice', self.current_voice_id)

            print(f"TTS Engine initialized with {len(self.voices)} voices available")

        except Exception as e:
            messagebox.showerror("TTS Error", f"Error initializing text-to-speech: {str(e)}")
            print(f"TTS Initialization Error: {e}")
            self.engine = None
            self.voices = []
            self.voice_descriptions = {}

    def create_ui(self):
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size based on screen size
        # Use smaller percentages for smaller screens
        if screen_width >= 1920:  # Full HD or larger
            window_width = int(screen_width * 0.7)
            window_height = int(screen_height * 0.7)
        else:  # Smaller screens
            window_width = int(screen_width * 0.8)
            window_height = int(screen_height * 0.8)
            
        # Set minimum window size
        min_width = 600  # Reduced minimum width
        min_height = 400  # Reduced minimum height
        
        # Ensure window size is not smaller than minimum
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        # Calculate window position to center it
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(min_width, min_height)
        
        # Main frame with smaller padding
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title with smaller font
        title_label = tk.Label(main_frame, text="Screen Text Selector", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 5))

        # Instructions in a more compact format
        instructions_frame = tk.LabelFrame(main_frame, text="Instructions", padx=5, pady=5)
        instructions_frame.pack(fill=tk.X, pady=5)

        instructions = tk.Label(
            instructions_frame,
            text="1. Ctrl+Shift+S: Start Selection\n"
                 "2. Click and drag to select text\n"
                 "3. Release to capture text\n"
                 "4. Ctrl+Shift+R: Start Reading\n"
                 "5. Ctrl+Shift+X: Stop Reading",
            justify=tk.LEFT,
            font=("Arial", 9),
            wraplength=window_width - 40
        )
        instructions.pack(anchor=tk.W)
        
        # Status label with smaller font
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(main_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(pady=(0, 5))
        
        # Text area with scrollbar - reduced height
        text_frame = tk.LabelFrame(main_frame, text="Captured Text", padx=5, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text area with scrollbar
        self.text_area = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Arial", 9),
            height=8  # Reduced height
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)
        
        # Control buttons in a more compact layout
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Configure grid weights for equal button sizes
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        
        # Calculate button width based on window size
        button_width = min(12, int(window_width / 60))  # Reduced button width
        
        # Create buttons with smaller font and padding
        button_style = {
            'font': ("Arial", 9),
            'padx': 2,
            'pady': 2
        }
        
        self.start_selection_button = tk.Button(
            control_frame,
            text="Start Selection",
            command=self.start_selection,
            bg="#2196F3",
            fg="white",
            width=button_width,
            **button_style
        )
        self.start_selection_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.start_reading_button = tk.Button(
            control_frame,
            text="Start Reading",
            command=self.start_reading,
            bg="#4CAF50",
            fg="white",
            width=button_width,
            **button_style
        )
        self.start_reading_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        self.stop_speech_button = tk.Button(
            control_frame,
            text="Stop Speech",
            command=self.stop_speech,
            bg="#F44336",
            fg="white",
            width=button_width,
            **button_style
        )
        self.stop_speech_button.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self.root:
            # Update text wrapping for instructions
            if hasattr(self, 'instructions'):
                self.instructions.configure(wraplength=event.width - 40)
            
            # Update button widths
            button_width = min(12, int(event.width / 60))
            for button in [self.start_selection_button, self.start_reading_button, self.stop_speech_button]:
                button.configure(width=button_width)

    def check_tesseract_status(self):
        """Check if Tesseract is working and show status"""
        tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
        if tesseract_cmd and test_tesseract(tesseract_cmd):
            # Shorten path for display if too long
            display_path = tesseract_cmd
            if len(display_path) > 50:
                 display_path = "..." + display_path[-47:]
            self.tesseract_status.set(f"Tesseract OK: {display_path}")
        else:
            self.tesseract_status.set("Tesseract not found or not working! OCR will fail.")
            print("Warning: Tesseract OCR engine not found or failing.")

    def update_voice_dropdown(self):
        """Update voice descriptions and current voice"""
        if not self.engine or not self.voices:
            self.status_var.set("TTS Engine Error. Cannot update voices.")
            print("TTS engine not available for voice update")
            return

        try:
            # Create friendly descriptions for each voice
            self.voice_descriptions = {}
            for voice in self.voices:
                gender = "Male" if "male" in voice.name.lower() or "david" in voice.name.lower() else "Female"
                lang = "English"  # Default, can be enhanced
                if "en-" in voice.id.lower():
                    lang = "English"
                elif "es-" in voice.id.lower():
                    lang = "Spanish"
                # Add more language detection as needed
                
                self.voice_descriptions[voice.id] = f"{gender} {lang} Voice - {voice.name}"

            # Determine and apply voice if not set
            if not self.current_voice_id and self.voices:
                # Try to find a female English voice first
                preferred_voice = None
                for voice in self.voices:
                    if "female" in voice.name.lower() and "en-" in voice.id.lower():
                        preferred_voice = voice
                        break
                
                # Fallback to first available voice
                self.current_voice_id = preferred_voice.id if preferred_voice else self.voices[0].id
                self.engine.setProperty('voice', self.current_voice_id)

            print(f"Voice descriptions updated with {len(self.voices)} voices available")

        except Exception as e:
            self.status_var.set(f"Error updating voices: {str(e)}")
            print(f"Error updating voice descriptions: {e}")
            self.voice_descriptions = {}

    def on_voice_selected(self, event=None):
        """Handle voice selection from combobox with enhanced mapping"""
        if not self.engine or not self.voices:
            return

        selected_display = self.voice_var.get()
        if not selected_display or "Error" in selected_display:
            return

        try:
            # Find the voice ID that matches the selected display name
            new_voice_id = None
            for voice in self.voices:
                desc = self.voice_descriptions.get(voice.id, f"Voice - {voice.name}")
                if desc == selected_display:
                    new_voice_id = voice.id
                    break

            if new_voice_id and new_voice_id != self.current_voice_id:
                self.current_voice_id = new_voice_id
                self.engine.setProperty('voice', self.current_voice_id)
                self.status_var.set(f"Voice set to {selected_display}")
                print(f"Voice changed to: {selected_display} (ID: {self.current_voice_id})")

        except Exception as e:
            self.status_var.set(f"Error setting voice: {str(e)}")
            print(f"Error setting voice: {e}")

    def update_speed(self, value):
        """Update speech rate when slider changes"""
        if not self.engine:
            return

        try:
            # The value from scale is already an int via self.speed_var
            speed = self.speed_var.get() # Use get() on the IntVar
            if speed != self.current_rate:
                self.current_rate = speed
                # Apply speed setting
                self.engine.setProperty('rate', speed)
                self.status_var.set(f"Speech speed set to {speed}")
                print(f"Speed changed to: {speed}")
        except Exception as e:
            self.status_var.set(f"Error setting speed: {str(e)}")
            print(f"Error setting speed: {e}")

    def test_voice_settings(self):
        """Test the current voice settings"""
        try:
            # Get the current text
            text = self.text_area.get(1.0, tk.END).strip()
            if not text:
                text = "This is a test of the current voice settings."
            
            # Create new Communicate instance with text
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            
            # Create temporary directory for audio files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_mp3 = os.path.join(temp_dir, "temp_audio.mp3")
                temp_wav = os.path.join(temp_dir, "temp_audio.wav")
                
                # Save and convert audio
                asyncio.run(communicate.save(temp_mp3))
                audio = AudioSegment.from_mp3(temp_mp3)
                audio.export(temp_wav, format="wav")
                
                # Play the audio file using winsound
                try:
                    winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    self.status_var.set("Playing test audio...")
                    
                    # Wait for the audio to finish playing
                    while winsound.PlaySound(None, winsound.SND_PURGE) == 0:
                        time.sleep(0.1)
                        self.root.update()  # Keep the UI responsive
                    
                    self.status_var.set("Test complete")
                except Exception as e:
                    self.status_var.set(f"Error playing audio: {str(e)}")
                    raise
                
        except Exception as e:
            self.status_var.set(f"Error testing voice: {str(e)}")
            print(f"Error in test_voice_settings: {e}")
            messagebox.showerror("Error", f"Could not test voice: {str(e)}")


    def start_selection(self):
        """Start screen selection mode"""
        if self.selection_mode:
            return

        self.selection_mode = True
        self.status_var.set("Click and drag to select text on screen. Press ESC to cancel.")
        print("Starting selection mode...")

        # Minimize main window
        self.root.iconify()
        self.root.update() # Ensure window is minimized before grabbing screen

        # Use root.after for GUI thread safety
        self.root.after(150, self._initiate_capture_overlay)


    def _initiate_capture_overlay(self):
        """ Takes screenshot of ALL monitors and creates overlay window covering them"""
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
                # Alternative if the above fails (less efficient):
                # mss.tools.to_png(sct_img.rgb, sct_img.size, output='screenshot.png')
                # self.screenshot = Image.open('screenshot.png')
                # os.remove('screenshot.png') # Clean up temp file

            print(f"Virtual screenshot taken: {self.screenshot.size}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screen using MSS: {str(e)}")
            print(f"Screen capture error (MSS): {e}")
            self.selection_mode = False
            if self.root: self.root.deiconify()
            self.status_var.set("Screen capture failed. Ready.")
            return

        # Create a Toplevel window that covers the ENTIRE virtual screen
        self.top_level = tk.Toplevel(self.root)

        # --- Crucial Part for Multi-Monitor ---
        # Set geometry explicitly to cover the virtual screen
        geo_str = f"{self.virtual_screen_geo['width']}x{self.virtual_screen_geo['height']}+{self.virtual_screen_geo['left']}+{self.virtual_screen_geo['top']}"
        self.top_level.geometry(geo_str)
        print(f"Setting overlay geometry: {geo_str}")
        # --------------------------------------

        # Make it borderless, always on top, and semi-transparent
        self.top_level.overrideredirect(True)
        self.top_level.attributes('-topmost', True)
        self.top_level.attributes('-alpha', 0.4) # Semi-transparent

        # Create canvas for drawing selection rectangle
        self.canvas = tk.Canvas(self.top_level, cursor="cross", bg='white', highlightthickness=0) # White bg helps alpha, remove border
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Escape key to cancel
        self.top_level.bind("<Escape>", self.cancel_selection)
        self.top_level.focus_force() # Ensure it captures key presses


    def on_mouse_down(self, event):
        """Handle mouse button press"""
        # Coordinates are relative to the canvas, which covers the virtual screen
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        print(f"Mouse down at virtual coords: ({self.start_x}, {self.start_y})")

        # Delete previous rect if it exists
        if self.rect:
            self.canvas.delete(self.rect)

        # Create a rectangle to represent selection
        # Coordinates are directly usable for the canvas covering the virtual screen
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2, dash=(4, 2)
        )

    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if not self.selection_mode or self.start_x is None or self.rect is None:
             return

        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)

        # Update selection rectangle using virtual screen coordinates
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.current_x, self.current_y)

    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if not self.selection_mode or self.start_x is None:
            print("Mouse up received but selection not active or not started.")
            return

        # Final coordinates relative to the virtual screen
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)

        # Calculate selection coordinates, ensuring positive width/height
        # These coordinates are relative to the top-left of the *virtual screen*
        # because the canvas covers the whole virtual screen.
        left = min(self.start_x, self.current_x)
        top = min(self.start_y, self.current_y)
        right = max(self.start_x, self.current_x)
        bottom = max(self.start_y, self.current_y)
        print(f"Mouse up. Virtual Box: L={left}, T={top}, R={right}, B={bottom}")

        # Capture dimensions
        width = right - left
        height = bottom - top

        # Clean up selection UI *before* processing
        self._end_selection_mode()

        # Process the selected region if it's large enough
        if width > 5 and height > 5:
             # Add a small delay before processing, allows UI cleanup
             self.root.after(50, lambda l=left, t=top, r=right, b=bottom: self.process_selection(l, t, r, b))
        else:
            messagebox.showinfo("Selection Too Small", "The selected area is too small. Please try again.")
            print("Selection too small, cancelled.")
            self.status_var.set("Selection too small. Ready.")


    def cancel_selection(self, event=None):
        """Cancel the selection process"""
        print("Selection cancelled by user (ESC).")
        self._end_selection_mode()
        self.status_var.set("Selection cancelled. Ready.")

    def _end_selection_mode(self):
        """Cleans up the selection overlay and resets state"""
        try:
            self.selection_mode = False
            self.start_x = None
            self.start_y = None
            self.current_x = None
            self.current_y = None
            self.rect = None

            if self.top_level:
                try:
                    self.top_level.destroy()
                except tk.TclError:
                    pass
                self.top_level = None
                self.canvas = None

            # Restore main window
            if self.root:
                try:
                    self.root.deiconify()
                    self.root.focus_force()
                    self.root.update()  # Force update the UI
                except tk.TclError:
                    pass
        except Exception as e:
            print(f"Error in _end_selection_mode: {e}")

    def process_selection(self, left, top, right, bottom):
        """Process the selected region of the screen using virtual coords"""
        if not self.screenshot:
            messagebox.showerror("Error", "No screenshot available to process.")
            print("Error: process_selection called without a screenshot.")
            self.status_var.set("Error: No screenshot data. Ready.")
            return

        self.status_var.set("Processing selection with OCR...")
        print("Processing selection...")
        self.root.update_idletasks()  # Update UI

        try:
            # Verify Tesseract is available before proceeding
            if not pytesseract.pytesseract.tesseract_cmd or not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                raise pytesseract.TesseractNotFoundError("Tesseract executable not found")

            # Crop the full virtual screenshot using the calculated coordinates
            img_width, img_height = self.screenshot.size
            safe_left = max(0, int(left))
            safe_top = max(0, int(top))
            safe_right = min(img_width, int(right))
            safe_bottom = min(img_height, int(bottom))

            if safe_right <= safe_left or safe_bottom <= safe_top:
                raise ValueError("Calculated crop box has zero or negative size.")

            selection = self.screenshot.crop((safe_left, safe_top, safe_right, safe_bottom))
            print(f"Cropped image size: {selection.size}")

            # Preprocess image to improve OCR
            preprocessed_selection = self.preprocess_image(selection)

            # Perform OCR with custom configuration for better text recognition
            custom_config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(preprocessed_selection, config=custom_config)
            text = text.strip()

            # Enhanced text processing
            if text:
                # Split into lines and process each line
                lines = text.split('\n')
                processed_lines = []
                for line in lines:
                    # Remove common OCR artifacts and normalize spacing
                    cleaned_line = line.strip()
                    if cleaned_line:
                        # Remove any non-printable characters
                        cleaned_line = ''.join(char for char in cleaned_line if char.isprintable())
                        # Normalize multiple spaces
                        cleaned_line = ' '.join(cleaned_line.split())
                        # Skip lines that look like debug output or system messages
                        if not any(x in cleaned_line.lower() for x in ['debug:', 'error:', 'warning:', 'exception:']):
                            processed_lines.append(cleaned_line)

                # Join processed lines with proper spacing
                processed_text = '\n'.join(processed_lines)
                
                # Update text area with processed text
                if processed_text:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, processed_text)
                    self.status_var.set("Text captured successfully. Ready to read.")
                else:
                    self.status_var.set("No valid text found after processing.")
                    messagebox.showinfo("Processing Result", "No valid text was found after cleaning the OCR result.")
            else:
                self.status_var.set("No text found in selection.")
                messagebox.showinfo("No Text Found", "Could not recognize any text in the selected area.")

        except pytesseract.TesseractNotFoundError:
            self.status_var.set("Error: Tesseract not found or path incorrect.")
            messagebox.showerror("Tesseract Error", "Tesseract executable not found or path is incorrect.\nPlease ensure Tesseract is installed or placed in the 'Tesseract-OCR' folder.")
            print("TesseractNotFoundError during OCR.")
        except ValueError as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
            print(f"ValueError during process_selection: {e}")
        except Exception as e:
            self.status_var.set(f"OCR Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during OCR: {str(e)}")
            print(f"Error during process_selection: {e}")
        finally:
            # Clear the screenshot and geometry from memory
            self.screenshot = None
            self.virtual_screen_geo = None
            
            # Ensure the main window is restored and focused
            if self.root:
                try:
                    self.root.deiconify()
                    self.root.focus_force()
                    self.root.update()
                except Exception as e:
                    print(f"Error restoring window: {e}")

    def preprocess_image(self, image):
        """Preprocess image to improve OCR results"""
        try:
            # Ensure image is in RGB mode first
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Reduced from 2.0 to prevent over-enhancement
            
            # Apply threshold to make text more distinct
            image = image.point(lambda x: 0 if x < 128 else 255, '1')
            
            # Apply slight blur to reduce noise
            image = image.convert('L')  # Convert back to grayscale after threshold
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            return image
        except Exception as e:
            print(f"Error during image preprocessing: {e}")
            # Return original image if preprocessing fails
            return image.convert('L') if image.mode != 'L' else image

    def start_speech_to_text(self):
        """Start speech to text in a new window"""
        SpeechToTextWindow(self.root)

    def audio_file_to_text(self):
        """Convert audio file to text"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac")]
        )
        if not file_path:
            return
            
        try:
            # Convert to WAV if needed
            if not file_path.lower().endswith('.wav'):
                audio = AudioSegment.from_file(file_path)
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_path = temp_file.name
                temp_file.close()  # Close the file handle
                
                audio.export(temp_path, format="wav")
                file_path = temp_path
                
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, text)
                self.status_var.set("Audio file converted to text successfully")
                
        except Exception as e:
            self.status_var.set(f"Error converting audio to text: {str(e)}")
            print(f"Error in audio_file_to_text: {e}")
        finally:
            # Clean up temporary file if it was created
            if 'temp_file' in locals() and os.path.exists(temp_path):
                try:
                    time.sleep(0.1)  # Give a small delay for any processes to release the file
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Warning: Could not delete temporary file: {e}")

    def enhanced_ocr(self):
        """Enhanced OCR with better preprocessing"""
        if not self.screenshot:
            messagebox.showerror("Error", "No screenshot available to process.")
            return
            
        try:
            # Enhanced preprocessing
            img = self.screenshot.convert('L')  # Convert to grayscale
            img = ImageEnhance.Contrast(img).enhance(2.0)  # Increase contrast
            img = img.filter(ImageFilter.SHARPEN)  # Sharpen image
            img = img.filter(ImageFilter.MedianFilter(size=3))  # Reduce noise
            
            # Perform OCR with custom configuration
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%&*()[]{}:;"\''
            text = pytesseract.image_to_string(img, config=custom_config)
            text = text.strip()

            if text:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, text)
                self.status_var.set("Enhanced OCR completed successfully")
            else:
                self.status_var.set("No text found in selection")
                
        except Exception as e:
            self.status_var.set(f"Error during enhanced OCR: {str(e)}")
            
    async def read_text_with_edge_tts(self, text):
        """Read text using Edge TTS"""
        try:
            # Create new Communicate instance with text
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            
            # Create temporary directory for audio files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_mp3 = os.path.join(temp_dir, "temp_audio.mp3")
                temp_wav = os.path.join(temp_dir, "temp_audio.wav")
                
                # Save and convert audio
                await communicate.save(temp_mp3)
                audio = AudioSegment.from_mp3(temp_mp3)
                audio.export(temp_wav, format="wav")
                
                # Play the audio file using winsound
                winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                
                # Wait for the audio to finish playing
                while winsound.PlaySound(None, winsound.SND_PURGE) == 0:
                    await asyncio.sleep(0.1)
                
                # Small delay to ensure cleanup
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.status_var.set(f"Error with Edge TTS: {str(e)}")
            print(f"Edge TTS Error: {e}")
            
    def start_reading(self):
        """Start reading the current text using Edge TTS"""
        # Stop any existing playback
        self.stop_speech()
        
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.status_var.set("No text to read")
            return
            
        self.status_var.set("Preparing to read text...")
        
        # Start audio playback in a separate thread
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(text,))
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
    def _play_audio_thread(self, text):
        """Handle audio playback in a separate thread"""
        try:
            self.is_playing = True
            
            # Create temporary directory for audio files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_mp3 = os.path.join(temp_dir, "temp_audio.mp3")
                temp_wav = os.path.join(temp_dir, "temp_audio.wav")
                
                # Create new Communicate instance with text
                communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Generating speech..."))
                
                # Save audio synchronously
                asyncio.run(communicate.save(temp_mp3))
                
                # Convert to WAV format
                audio = AudioSegment.from_mp3(temp_mp3)
                audio.export(temp_wav, format="wav")
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Playing audio..."))
                
                if self.is_playing:  # Check if we should still play
                    # Play the audio file using subprocess for better control
                    self.audio_process = subprocess.Popen(
                        ['powershell', '-c', f'(New-Object Media.SoundPlayer "{temp_wav}").PlaySync()'],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Wait for playback to complete or stop signal
                    while self.is_playing and self.audio_process.poll() is None:
                        time.sleep(0.1)
                    
                    # If we're still playing, it means playback completed naturally
                    if self.is_playing:
                        self.root.after(0, lambda: self.status_var.set("Reading complete"))
                
        except Exception as e:
            error_msg = f"Error reading text: {str(e)}"
            print(f"Error in _play_audio_thread: {e}")
            # Update status in main thread
            self.root.after(0, lambda: [
                self.status_var.set(error_msg),
                messagebox.showerror("Text-to-Speech Error", error_msg)
            ])
        finally:
            self.is_playing = False
            if self.audio_process and self.audio_process.poll() is None:
                self.audio_process.terminate()
                self.audio_process = None
            
    def stop_speech(self):
        """Stop current speech"""
        try:
            self.is_playing = False
            
            # Terminate the audio process if it's running
            if self.audio_process and self.audio_process.poll() is None:
                self.audio_process.terminate()
                self.audio_process = None
            
            # Wait for the audio thread to finish
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1.0)
            
            # Update status
            self.status_var.set("Speech stopped")
            print("TTS stop requested")
            
        except Exception as e:
            error_msg = f"Error stopping speech: {str(e)}"
            self.status_var.set(error_msg)
            print(f"Error stopping TTS: {e}")
            messagebox.showerror("Stop Error", error_msg)


    def on_close(self):
        """Handle application close"""
        print("Closing application...")
        try:
            self.stop_speech() # Stop any active speech

            print("Unhooking keyboard hotkeys...")
            try:
                keyboard.unhook_all()
            except Exception as e:
                print(f"Error unhooking keyboard: {e}")

            if hasattr(self, 'engine') and self.engine:
                print("Shutting down TTS engine...")
                try:
                    self.engine.stop()
                except Exception as e:
                    print(f"Error during TTS engine cleanup: {e}")
                self.engine = None

            if self.root:
                print("Destroying main window.")
                self.root.destroy()
                self.root = None
        except Exception as e:
            print(f"Error during application close: {e}")
        finally:
            print("Application exited.")

    def run(self):
        """Run the application's main loop"""
        print("Starting ScreenTextSelector application...")
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            self.root.mainloop()
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, closing.")
            self.on_close()
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            self.on_close()
        finally:
            print("Application exited.")

    def save_text(self):
        """Save the current text to a file"""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("No Text", "There is no text to save.")
            return

        try:
            # Get the file path from the user
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Text As"
            )
            
            if file_path:  # If user didn't cancel
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(text)
                messagebox.showinfo("Success", f"Text saved successfully to:\n{file_path}")
                self.status_var.set(f"Text saved to: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            self.status_var.set("Error saving file")

    def show_voice_settings(self):
        """Show voice selection dialog"""
        if not self.engine or not self.voices:
            messagebox.showerror("Error", "Text-to-speech engine is not available.")
            return

        # Create a new window for voice settings
        voice_window = tk.Toplevel(self.root)
        voice_window.title("Voice Selection")
        voice_window.geometry("400x200")
        voice_window.transient(self.root)  # Make it float above main window

        # Voice selection frame
        voice_frame = tk.LabelFrame(voice_window, text="Select Voice", padx=10, pady=10)
        voice_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(voice_frame, text="Voice:").pack(side=tk.LEFT)
        voice_combo = ttk.Combobox(voice_frame, state='readonly')
        voice_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Populate voice dropdown
        voice_options = []
        voice_id_map = {}
        for voice in self.voices:
            desc = self.voice_descriptions.get(voice.id, f"Voice - {voice.name}")
            display_name = f"{desc}"
            voice_options.append(display_name)
            voice_id_map[display_name] = voice.id

        voice_combo['values'] = voice_options

        # Set current selection
        current_display = None
        for display, vid in voice_id_map.items():
            if vid == self.current_voice_id:
                current_display = display
                break
        if current_display in voice_options:
            voice_combo.set(current_display)

        def apply_voice():
            selected_display = voice_combo.get()
            if selected_display and selected_display in voice_id_map:
                new_voice_id = voice_id_map[selected_display]
                if new_voice_id != self.current_voice_id:
                    self.current_voice_id = new_voice_id
                    self.engine.setProperty('voice', self.current_voice_id)
                    self.status_var.set(f"Voice set to {selected_display}")
            voice_window.destroy()

        # Buttons
        button_frame = tk.Frame(voice_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(button_frame, text="Apply", command=apply_voice).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=voice_window.destroy).pack(side=tk.RIGHT)

    def show_speed_settings(self):
        """Show speed settings dialog"""
        if not self.engine:
            messagebox.showerror("Error", "Text-to-speech engine is not available.")
            return

        # Create a new window for speed settings
        speed_window = tk.Toplevel(self.root)
        speed_window.title("Speed Settings")
        speed_window.geometry("400x150")
        speed_window.transient(self.root)  # Make it float above main window

        # Speed settings frame
        speed_frame = tk.LabelFrame(speed_window, text="Speech Speed", padx=10, pady=10)
        speed_frame.pack(fill=tk.X, padx=10, pady=5)

        speed_var = tk.IntVar(value=self.current_rate)
        speed_scale = tk.Scale(
            speed_frame,
            from_=50,
            to=300,
            orient=tk.HORIZONTAL,
            variable=speed_var,
            label="Words per minute"
        )
        speed_scale.pack(fill=tk.X, padx=5, pady=5)

        def apply_speed():
            new_speed = speed_var.get()
            if new_speed != self.current_rate:
                self.current_rate = new_speed
                self.engine.setProperty('rate', self.current_rate)
                self.status_var.set(f"Speech speed set to {self.current_rate}")
            speed_window.destroy()

        # Buttons
        button_frame = tk.Frame(speed_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(button_frame, text="Apply", command=apply_speed).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Cancel", command=speed_window.destroy).pack(side=tk.RIGHT)

    def show_font_settings(self):
        """Show font settings dialog"""
        font_window = tk.Toplevel(self.root)
        font_window.title("Font Settings")
        font_window.geometry("600x600")
        font_window.transient(self.root)

        # Create main frames
        settings_frame = tk.Frame(font_window)
        settings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        preview_frame = tk.LabelFrame(font_window, text="Preview", padx=10, pady=10)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Font family
        font_family_frame = tk.LabelFrame(settings_frame, text="Font Family", padx=10, pady=10)
        font_family_frame.pack(fill=tk.X, pady=5)

        font_families = sorted(font.families())
        font_family_var = tk.StringVar(value=self.settings['font_family'])
        font_family_combo = ttk.Combobox(font_family_frame, textvariable=font_family_var, values=font_families, state='readonly')
        font_family_combo.pack(fill=tk.X, padx=5, pady=5)

        # Font size
        font_size_frame = tk.LabelFrame(settings_frame, text="Font Size", padx=10, pady=10)
        font_size_frame.pack(fill=tk.X, pady=5)

        font_size_var = tk.IntVar(value=self.settings['font_size'])
        font_size_scale = tk.Scale(font_size_frame, from_=8, to=24, orient=tk.HORIZONTAL, variable=font_size_var)
        font_size_scale.pack(fill=tk.X, padx=5, pady=5)

        # Font style
        font_style_frame = tk.LabelFrame(settings_frame, text="Font Style", padx=10, pady=10)
        font_style_frame.pack(fill=tk.X, pady=5)

        font_style_var = tk.StringVar(value=self.settings['font_style'])
        font_weight_var = tk.StringVar(value=self.settings['font_weight'])

        style_frame = tk.Frame(font_style_frame)
        style_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Radiobutton(style_frame, text="Normal", variable=font_style_var, value="normal").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(style_frame, text="Italic", variable=font_style_var, value="italic").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(style_frame, text="Bold", variable=font_weight_var, value="bold").pack(side=tk.LEFT, padx=5)

        # Text wrap
        wrap_frame = tk.LabelFrame(settings_frame, text="Text Wrap", padx=10, pady=10)
        wrap_frame.pack(fill=tk.X, pady=5)

        wrap_var = tk.StringVar(value=self.settings['text_wrap'])
        tk.Radiobutton(wrap_frame, text="Word", variable=wrap_var, value="word").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(wrap_frame, text="Character", variable=wrap_var, value="char").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(wrap_frame, text="None", variable=wrap_var, value="none").pack(side=tk.LEFT, padx=5)

        # Colors
        colors_frame = tk.LabelFrame(settings_frame, text="Colors", padx=10, pady=10)
        colors_frame.pack(fill=tk.X, pady=5)

        # Text color
        text_color_frame = tk.Frame(colors_frame)
        text_color_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(text_color_frame, text="Text Color:").pack(side=tk.LEFT)
        text_color_var = tk.StringVar(value=self.settings['text_color'])
        text_color_entry = tk.Entry(text_color_frame, textvariable=text_color_var, width=10)
        text_color_entry.pack(side=tk.LEFT, padx=5)
        
        def choose_text_color():
            color = colorchooser.askcolor(title="Choose Text Color", initialcolor=text_color_var.get())
            if color[1]:  # color[1] is the hex color string
                text_color_var.set(color[1])
                update_preview()
        
        text_color_button = tk.Button(text_color_frame, text="Choose", command=choose_text_color)
        text_color_button.pack(side=tk.LEFT, padx=5)

        # Background color
        bg_color_frame = tk.Frame(colors_frame)
        bg_color_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(bg_color_frame, text="Background Color:").pack(side=tk.LEFT)
        bg_color_var = tk.StringVar(value=self.settings['bg_color'])
        bg_color_entry = tk.Entry(bg_color_frame, textvariable=bg_color_var, width=10)
        bg_color_entry.pack(side=tk.LEFT, padx=5)
        
        def choose_bg_color():
            color = colorchooser.askcolor(title="Choose Background Color", initialcolor=bg_color_var.get())
            if color[1]:  # color[1] is the hex color string
                bg_color_var.set(color[1])
                update_preview()
        
        bg_color_button = tk.Button(bg_color_frame, text="Choose", command=choose_bg_color)
        bg_color_button.pack(side=tk.LEFT, padx=5)

        # Preview area
        preview_text = tk.Text(
            preview_frame,
            wrap=wrap_var.get(),
            height=10,
            font=(font_family_var.get(), font_size_var.get(), font_style_var.get(), font_weight_var.get()),
            fg=text_color_var.get(),
            bg=bg_color_var.get()
        )
        preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_text.insert(tk.END, "This is a preview of how your text will look.\n\n")
        preview_text.insert(tk.END, "You can see how different fonts, sizes, and colors will appear in your text area.")
        preview_text.config(state='disabled')  # Make it read-only

        def update_preview():
            # Update preview text configuration
            font_config = (
                font_family_var.get(),
                font_size_var.get(),
                font_style_var.get(),
                font_weight_var.get()
            )
            preview_text.config(
                font=font_config,
                wrap=wrap_var.get(),
                fg=text_color_var.get(),
                bg=bg_color_var.get()
            )

        # Bind update events
        font_family_var.trace_add('write', lambda *args: update_preview())
        font_size_var.trace_add('write', lambda *args: update_preview())
        font_style_var.trace_add('write', lambda *args: update_preview())
        font_weight_var.trace_add('write', lambda *args: update_preview())
        wrap_var.trace_add('write', lambda *args: update_preview())
        text_color_var.trace_add('write', lambda *args: update_preview())
        bg_color_var.trace_add('write', lambda *args: update_preview())

        def apply_settings():
            # Update settings
            self.settings.update({
                'font_family': font_family_var.get(),
                'font_size': font_size_var.get(),
                'font_style': font_style_var.get(),
                'font_weight': font_weight_var.get(),
                'text_wrap': wrap_var.get(),
                'text_color': text_color_var.get(),
                'bg_color': bg_color_var.get()
            })

            # Apply to text area
            font_config = (
                self.settings['font_family'],
                self.settings['font_size'],
                self.settings['font_style'],
                self.settings['font_weight']
            )
            self.text_area.configure(
                font=font_config,
                wrap=self.settings['text_wrap'],
                fg=self.settings['text_color'],
                bg=self.settings['bg_color']
            )

            # Save settings
            if self.save_settings():
                self.status_var.set("Font settings applied and saved")
            else:
                self.status_var.set("Font settings applied but could not be saved")

        def apply_and_close():
            apply_settings()
            font_window.destroy()

        # Buttons
        button_frame = tk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Apply & Close", command=apply_and_close).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=font_window.destroy).pack(side=tk.RIGHT, padx=5)

    def save_as_mp3(self):
        """Save the current text as an MP3 file using Edge TTS"""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("No Text", "There is no text to convert to speech.")
            return

        try:
            # Get the file path from the user
            file_path = filedialog.asksaveasfilename(
                defaultextension=".mp3",
                filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
                title="Save as MP3"
            )
            
            if not file_path:  # User cancelled
                return

            # Show progress
            self.status_var.set("Converting text to speech...")
            self.root.update()

            # Create a progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Converting to MP3")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            # Add progress label
            progress_label = tk.Label(progress_window, text="Converting text to speech...\nThis may take a moment.")
            progress_label.pack(pady=10)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()

            def convert_to_mp3():
                try:
                    # Create new Communicate instance with text
                    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                    
                    # Save directly to MP3
                    asyncio.run(communicate.save(file_path))
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set(f"Text saved as MP3: {os.path.basename(file_path)}"),
                        messagebox.showinfo("Success", f"Text successfully converted to MP3:\n{file_path}")
                    ])
                    
                except Exception as e:
                    # Show error in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set("Error converting to MP3"),
                        messagebox.showerror("Error", f"Could not convert text to MP3: {str(e)}")
                    ])

            # Start conversion in a separate thread
            threading.Thread(target=convert_to_mp3, daemon=True).start()
            
        except Exception as e:
            self.status_var.set("Error saving MP3")
            messagebox.showerror("Error", f"Could not save MP3: {str(e)}")
            print(f"Error in save_as_mp3: {e}")

    def show_about(self):
        """Show about window with application information"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Screen Text Selector")
        about_window.geometry("600x400")
        about_window.transient(self.root)
        about_window.grab_set()

        # Center the window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (about_window.winfo_width() // 2)
        y = (about_window.winfo_screenheight() // 2) - (about_window.winfo_height() // 2)
        about_window.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = tk.Frame(about_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and version
        title_label = tk.Label(
            main_frame,
            text=f"Screen Text Selector\n{VERSION}",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Description
        description = tk.Text(
            main_frame,
            wrap=tk.WORD,
            height=10,
            font=("Arial", 10)
        )
        description.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        description.insert(tk.END, 
            f"Screen Text Selector {VERSION} is a comprehensive text-to-speech and OCR application designed to enhance accessibility "
            "and productivity. It can run from a USB stick, making it fully portable.\n\n"
            "Core Features:\n"
            "• Advanced OCR with multiple engines (Tesseract & EasyOCR)\n"
            "• Microsoft Edge TTS with natural-sounding voices\n"
            "• Gaming Speech Mode with customizable overlay\n"
            "• Document support (PDF, Word, Text files)\n"
            "• Speech-to-text conversion\n"
            "• Audio file transcription\n"
            "• MP3 import/export functionality\n\n"
            "Accessibility Features:\n"
            "• Customizable fonts and colors\n"
            "• High contrast mode\n"
            "• Adjustable text size and wrapping\n"
            "• Screen position memory\n"
            "• Auto-hide options\n\n"
            "Gaming Mode Features:\n"
            "• Always-on-top window\n"
            "• Compact mode\n"
            "• Adjustable overlay opacity\n"
            "• Movable and resizable selection box\n"
            "• Quick text copying between windows\n\n"
            "Hotkeys:\n"
            "• Ctrl+Shift+S: Start selection\n"
            "• Ctrl+Shift+R: Start reading\n"
            "• Ctrl+Shift+X: Stop reading\n"
            "• Ctrl+Shift+G: Toggle auto-hide\n\n"
            "Voice Options:\n"
            "• Multiple Microsoft Edge TTS voices\n"
            "• Adjustable speaking rate\n"
            "• Language variations (US/UK English)\n"
            "• Voice testing feature\n\n"
            "This application is ideal for:\n"
            "• Accessibility assistance\n"
            "• Gaming and streaming\n"
            "• Document reading\n"
            "• Language learning\n"
            "• Content creation\n"
            "• Audio transcription\n"
        )
        description.config(state='disabled')

        # Close button
        close_button = tk.Button(
            main_frame,
            text="Close",
            command=about_window.destroy,
            font=("Arial", 11)
        )
        close_button.pack()

    def show_dyslexic_features(self):
        """Show information about dyslexic-friendly features"""
        features_window = tk.Toplevel(self.root)
        features_window.title("Dyslexic-Friendly Features")
        features_window.geometry("600x500")
        features_window.transient(self.root)
        features_window.grab_set()

        # Center the window
        features_window.update_idletasks()
        x = (features_window.winfo_screenwidth() // 2) - (features_window.winfo_width() // 2)
        y = (features_window.winfo_screenheight() // 2) - (features_window.winfo_height() // 2)
        features_window.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = tk.Frame(features_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="Dyslexic-Friendly Features",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Features text
        features_text = tk.Text(
            main_frame,
            wrap=tk.WORD,
            height=15,
            font=("Arial", 10)
        )
        features_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        features_text.insert(tk.END,
            "Screen Text Selector includes several features specifically designed to help users with dyslexia:\n\n"
            "1. Text-to-Speech Features:\n"
            "   • High-quality voice synthesis for clear pronunciation\n"
            "   • Adjustable reading speed to match your comfort level\n"
            "   • Multiple voice options for better comprehension\n"
            "   • MP3 export for listening on other devices\n\n"
            "2. Visual Assistance:\n"
            "   • Customizable font settings for better readability\n"
            "   • Adjustable text and background colors\n"
            "   • Word wrap options to prevent line breaks\n"
            "   • Clear, high-contrast interface\n\n"
            "3. Text Capture Features:\n"
            "   • OCR technology to capture text from any screen area\n"
            "   • Speech-to-text for hands-free operation\n"
            "   • Audio file transcription for recorded content\n"
            "   • Enhanced text processing for better accuracy\n\n"
            "4. Accessibility Features:\n"
            "   • Keyboard shortcuts for easy navigation\n"
            "   • Simple, intuitive interface\n"
            "   • Clear status messages and feedback\n"
            "   • Error prevention and recovery\n\n"
            "5. Learning Support:\n"
            "   • Text can be read back for verification\n"
            "   • Multiple recognition attempts for accuracy\n"
            "   • Clear visual feedback during operations\n"
            "   • Easy text editing and correction\n"
        )
        features_text.config(state='disabled')

        # Close button
        close_button = tk.Button(
            main_frame,
            text="Close",
            command=features_window.destroy,
            font=("Arial", 11)
        )
        close_button.pack()

    def load_from_mp3(self):
        """Load text from an MP3 file using speech recognition"""
        try:
            # Get the file path from the user
            file_path = filedialog.askopenfilename(
                filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
                title="Load from MP3"
            )
            
            if not file_path:  # User cancelled
                return

            # Show progress
            self.status_var.set("Converting MP3 to text...")
            self.root.update()

            # Create a progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Converting MP3")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            # Add progress label
            progress_label = tk.Label(progress_window, text="Converting MP3 to text...\nThis may take a moment.")
            progress_label.pack(pady=10)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()

            def convert_mp3_to_text():
                try:
                    # Convert MP3 to WAV for speech recognition
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_path = temp_file.name
                        
                        # Convert MP3 to WAV using pydub with enhanced settings
                        audio = AudioSegment.from_mp3(file_path)
                        
                        # Enhance audio quality
                        audio = audio.normalize()  # Normalize volume
                        audio = audio.high_pass_filter(80)  # Remove low frequency noise
                        audio = audio.low_pass_filter(3000)  # Remove high frequency noise
                        
                        # Export with high quality settings
                        audio.export(temp_path, format="wav", parameters=[
                            "-ac", "1",  # Mono channel
                            "-ar", "44100",  # High sample rate
                            "-acodec", "pcm_s16le"  # High quality codec
                        ])
                        
                        # Use speech recognition to convert WAV to text
                        with sr.AudioFile(temp_path) as source:
                            # Configure recognizer for better accuracy
                            self.recognizer.energy_threshold = 20  # Even lower threshold for better sensitivity
                            self.recognizer.dynamic_energy_threshold = True
                            self.recognizer.dynamic_energy_adjustment_damping = 0.03
                            self.recognizer.dynamic_energy_ratio = 4.0
                            self.recognizer.pause_threshold = 1.5  # Longer pause threshold
                            self.recognizer.phrase_threshold = 0.03  # More sensitive to phrases
                            self.recognizer.non_speaking_duration = 1.0  # Longer non-speaking duration
                            
                            # Adjust for ambient noise with longer duration
                            self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                            
                            # Record the audio
                            audio = self.recognizer.record(source)
                            
                            # Try multiple recognition attempts with different settings
                            text = None
                            attempts = [
                                # First attempt: With specific formatting context
                                lambda: self.recognizer.recognize_google(
                                    audio,
                                    language='en-US',
                                    show_all=True,
                                    with_confidence=True,
                                    speech_contexts=[["formatting", "punctuation", "numbers", "technical", "documentation", "examples"]]
                                ),
                                
                                # Second attempt: With alternative settings
                                lambda: self.recognizer.recognize_google(
                                    audio,
                                    language='en-US',
                                    show_all=True,
                                    with_confidence=True,
                                    speech_contexts=[["text", "formatting", "structure", "examples"]]
                                ),
                                
                                # Third attempt: With different language model
                                lambda: self.recognizer.recognize_google(
                                    audio,
                                    language='en-US',
                                    show_all=True,
                                    with_confidence=True
                                ),
                                
                                # Fourth attempt: Basic recognition
                                lambda: self.recognizer.recognize_google(audio, language='en-US')
                            ]
                            
                            for attempt in attempts:
                                try:
                                    result = attempt()
                                    if isinstance(result, dict) and 'alternative' in result:
                                        # Get the most confident result
                                        text = result['alternative'][0]['transcript']
                                        break
                                    elif isinstance(result, str):
                                        text = result
                                        break
                                except sr.UnknownValueError:
                                    continue
                                except Exception as e:
                                    print(f"Recognition attempt failed: {e}")
                                    continue
                            
                            if text:
                                # Enhanced text cleanup
                                text = text.strip()
                                
                                # Fix common speech recognition mistakes
                                replacements = {
                                    'FORMATTING': 'formatting',
                                    'FORMAT': 'formatting',
                                    'PATTERNS': 'patterns',
                                    'PATTERN': 'pattern',
                                    'FIX': 'fix',
                                    'FIXED': 'fixed',
                                    'DECIMAL': 'decimal',
                                    'DECIMALS': 'decimals',
                                    'NUMBERS': 'numbers',
                                    'NUMBER': 'number',
                                    'TIME': 'time',
                                    'FORMAT': 'format',
                                    'RANGES': 'ranges',
                                    'RANGE': 'range',
                                    'INSTEAD': 'instead',
                                    'OF': 'of',
                                    'DEGREES': '',
                                    'DEGREE': '',
                                    'DEG': '',
                                    'TO': 'to',
                                    'E.G.': 'e.g.',
                                    'EG': 'e.g.',
                                    'EXAMPLE': 'example',
                                    'EXAMPLES': 'examples'
                                }
                                
                                for wrong, right in replacements.items():
                                    text = text.replace(wrong, right)
                                    text = text.replace(wrong.lower(), right)
                                
                                # Fix spacing around punctuation
                                text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Remove spaces before punctuation
                                text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)  # Add space after punctuation
                                
                                # Fix specific formatting patterns
                                text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)  # Fix decimal numbers
                                text = re.sub(r'(\d+)\s*:\s*(\d+)', r'\1:\2', text)  # Fix time format
                                text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', text)  # Fix number ranges
                                
                                # Fix example formatting
                                text = re.sub(r'e\s*\.\s*g\s*\.', 'e.g.', text, flags=re.IGNORECASE)
                                text = re.sub(r'for\s+example', 'e.g.', text, flags=re.IGNORECASE)
                                
                                # Remove any remaining degree symbols
                                text = text.replace('°', '')
                                text = text.replace('degrees', '')
                                
                                # Fix common formatting issues
                                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                                text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)  # Add newlines after sentences
                                
                                # Update UI in main thread
                                self.root.after(0, lambda: [
                                    progress_window.destroy(),
                                    self.text_area.delete(1.0, tk.END),
                                    self.text_area.insert(tk.END, text),
                                    self.status_var.set(f"MP3 converted to text successfully"),
                                    messagebox.showinfo("Success", "MP3 successfully converted to text")
                                ])
                            else:
                                # Show error in main thread
                                self.root.after(0, lambda: [
                                    progress_window.destroy(),
                                    self.status_var.set("Could not recognize speech in MP3"),
                                    messagebox.showerror("Error", "Could not recognize speech in the MP3 file. Please try again with a clearer audio file.")
                                ])
                        
                        # Clean up temporary file
                        try:
                            os.unlink(temp_path)
                        except Exception as e:
                            print(f"Warning: Could not delete temporary file: {e}")
                    
                except Exception as e:
                    # Show error in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set("Error converting MP3"),
                        messagebox.showerror("Error", f"Could not convert MP3 to text: {str(e)}")
                    ])

            # Start conversion in a separate thread
            threading.Thread(target=convert_mp3_to_text, daemon=True).start()
            
        except Exception as e:
            self.status_var.set("Error loading MP3")
            messagebox.showerror("Error", f"Could not load MP3: {str(e)}")
            print(f"Error in load_from_mp3: {e}")

    def load_from_text(self):
        """Load text from a text file"""
        try:
            # Get the file path from the user
            file_path = filedialog.askopenfilename(
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Load from Text File"
            )
            
            if not file_path:  # User cancelled
                return

            # Show progress
            self.status_var.set("Loading text file...")
            self.root.update()

            # Create a progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Loading Text")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            # Add progress label
            progress_label = tk.Label(progress_window, text="Loading text file...")
            progress_label.pack(pady=10)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()

            def load_text():
                try:
                    # Try different encodings
                    encodings = ['utf-8', 'utf-16', 'ascii', 'latin-1']
                    text = None
                    
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as file:
                                text = file.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if text is None:
                        raise Exception("Could not read file with any supported encoding")
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.text_area.delete(1.0, tk.END),
                        self.text_area.insert(tk.END, text),
                        self.status_var.set(f"Text loaded from: {os.path.basename(file_path)}")
                    ])
                    
                except Exception as e:
                    # Show error in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set("Error loading text file"),
                        messagebox.showerror("Error", f"Could not load text file: {str(e)}")
                    ])

            # Start loading in a separate thread
            threading.Thread(target=load_text, daemon=True).start()
            
        except Exception as e:
            self.status_var.set("Error loading text file")
            messagebox.showerror("Error", f"Could not load text file: {str(e)}")
            print(f"Error in load_from_text: {e}")

    def load_from_pdf(self):
        """Load text from a PDF file"""
        try:
            # Get the file path from the user
            file_path = filedialog.askopenfilename(
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Load from PDF"
            )
            
            if not file_path:  # User cancelled
                return

            # Show progress
            self.status_var.set("Loading PDF file...")
            self.root.update()

            # Create a progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Loading PDF")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            # Add progress label
            progress_label = tk.Label(progress_window, text="Loading PDF file...")
            progress_label.pack(pady=10)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()

            def load_pdf():
                try:
                    text = ""
                    with open(file_path, 'rb') as file:
                        # Create PDF reader object
                        pdf_reader = PyPDF2.PdfReader(file)
                        
                        # Get number of pages
                        num_pages = len(pdf_reader.pages)
                        
                        # Extract text from each page
                        for page_num in range(num_pages):
                            page = pdf_reader.pages[page_num]
                            text += page.extract_text() + "\n\n"
                    
                    if not text.strip():
                        raise Exception("No text could be extracted from the PDF")
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.text_area.delete(1.0, tk.END),
                        self.text_area.insert(tk.END, text),
                        self.status_var.set(f"PDF loaded from: {os.path.basename(file_path)}")
                    ])
                    
                except Exception as e:
                    # Show error in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set("Error loading PDF"),
                        messagebox.showerror("Error", f"Could not load PDF: {str(e)}")
                    ])

            # Start loading in a separate thread
            threading.Thread(target=load_pdf, daemon=True).start()
            
        except Exception as e:
            self.status_var.set("Error loading PDF")
            messagebox.showerror("Error", f"Could not load PDF: {str(e)}")
            print(f"Error in load_from_pdf: {e}")

    def load_from_word(self):
        """Load text from a Word document"""
        try:
            # Get the file path from the user
            file_path = filedialog.askopenfilename(
                filetypes=[("Word files", "*.docx"), ("All files", "*.*")],
                title="Load from Word"
            )
            
            if not file_path:  # User cancelled
                return

            # Show progress
            self.status_var.set("Loading Word document...")
            self.root.update()

            # Create a progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Loading Word")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            
            # Center the progress window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
            y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            # Add progress label
            progress_label = tk.Label(progress_window, text="Loading Word document...")
            progress_label.pack(pady=10)
            
            # Add progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()

            def load_word():
                try:
                    # Open the Word document
                    doc = docx.Document(file_path)
                    
                    # Extract text from paragraphs
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    
                    if not text.strip():
                        raise Exception("No text could be extracted from the Word document")
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.text_area.delete(1.0, tk.END),
                        self.text_area.insert(tk.END, text),
                        self.status_var.set(f"Word document loaded from: {os.path.basename(file_path)}")
                    ])
                    
                except Exception as e:
                    # Show error in main thread
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        self.status_var.set("Error loading Word document"),
                        messagebox.showerror("Error", f"Could not load Word document: {str(e)}")
                    ])

            # Start loading in a separate thread
            threading.Thread(target=load_word, daemon=True).start()
            
        except Exception as e:
            self.status_var.set("Error loading Word document")
            messagebox.showerror("Error", f"Could not load Word document: {str(e)}")
            print(f"Error in load_from_word: {e}")

    def show_gaming_speech(self):
        """Show the gaming speech window"""
        GamingSpeechWindow(self.root)

class SpeechToTextWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Speech to Text")
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate window size based on screen size
        if screen_width >= 1920:  # Full HD or larger
            window_width = int(screen_width * 0.7)
            window_height = int(screen_height * 0.7)
        else:  # Smaller screens
            window_width = int(screen_width * 0.8)
            window_height = int(screen_height * 0.8)
            
        # Set minimum window size
        min_width = 600
        min_height = 400
        
        # Ensure window size is not smaller than minimum
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        # Calculate window position to center it
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window size and position
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.minsize(min_width, min_height)
        self.window.transient(parent)
        
        # Make window modal
        self.window.grab_set()
        
        # Initialize variables
        self.is_recording = False
        self.is_talking = False
        self.is_reading = False
        self.audio_queue = queue.Queue(maxsize=2000)
        self.recording_thread = None
        self.recognizer = sr.Recognizer()
        self.selected_device = None
        self.audio_process = None
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Configure recognizer settings
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.1
        self.recognizer.dynamic_energy_ratio = 1.1
        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.1
        self.recognizer.non_speaking_duration = 0.5
        
        # Create UI
        self.create_ui()
        
        # Test audio devices
        self.test_audio_devices()

    def create_ui(self):
        """Create the user interface"""
        # Main frame with smaller padding
        main_frame = tk.Frame(self.window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with smaller font
        title_label = tk.Label(main_frame, text="Speech to Text", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 5))
        
        # Instructions frame with compact layout
        instructions_frame = tk.LabelFrame(main_frame, text="How to Use", padx=5, pady=5)
        instructions_frame.pack(fill=tk.X, pady=5)
        
        instructions = tk.Label(
            instructions_frame,
            text="1. Select microphone\n"
                 "2. Click 'Start Recording'\n"
                 "3. Click 'Start Talking' to speak\n"
                 "4. Click 'Stop Talking' when done\n"
                 "5. Click 'Stop Recording' to process\n"
                 "6. Use 'Read Text' to listen\n"
                 "7. Use 'Copy to Main' to transfer",
            justify=tk.LEFT,
            font=("Arial", 9)
        )
        instructions.pack(anchor=tk.W)
        
        # Microphone selection frame
        mic_frame = tk.LabelFrame(main_frame, text="Microphone Selection", padx=5, pady=5)
        mic_frame.pack(fill=tk.X, pady=5)
        
        # Get available input devices
        devices = sd.query_devices()
        self.input_devices = []
        seen_names = set()
        
        # Filter and deduplicate devices
        for device in devices:
            if device['max_input_channels'] > 0:
                base_name = device['name'].split(',')[0].strip()
                if base_name not in seen_names:
                    seen_names.add(base_name)
                    self.input_devices.append(device)
        
        device_names = [d['name'].split(',')[0].strip() for d in self.input_devices]
        
        # Create dropdown with smaller font
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(
            mic_frame,
            textvariable=self.device_var,
            values=device_names,
            state='readonly',
            font=("Arial", 9)
        )
        self.device_dropdown.pack(fill=tk.X, pady=2)
        
        # Set default selection to SteelSeries if available
        for i, device in enumerate(device_names):
            if "SteelSeries Sonar" in device and "Microphone" in device:
                self.device_dropdown.current(i)
                break
        
        # Status label with smaller font
        self.status_var = tk.StringVar(value="Ready to record")
        status_label = tk.Label(main_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(pady=5)
        
        # Text area with scrollbar
        text_frame = tk.LabelFrame(main_frame, text="Recognized Text", padx=5, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text area with scrollbar
        self.text_area = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Arial", 9),
            height=8
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)
        
        # Controls container frame
        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        # Button style
        button_style = {
            'font': ("Arial", 9),
            'padx': 2,
            'pady': 2
        }
        
        # Recording controls frame
        recording_frame = tk.LabelFrame(controls_frame, text="Recording Controls", padx=5, pady=5)
        recording_frame.pack(fill=tk.X, pady=5)
        
        # Configure grid weights
        recording_frame.grid_columnconfigure(0, weight=1)
        recording_frame.grid_columnconfigure(1, weight=1)
        
        # Start/Stop Recording buttons
        self.start_record_button = tk.Button(
            recording_frame,
            text="Start Recording",
            command=self.start_recording,
            bg="#4CAF50",
            fg="white",
            width=12,
            **button_style
        )
        self.start_record_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.stop_record_button = tk.Button(
            recording_frame,
            text="Stop Recording",
            command=self.stop_recording,
            bg="#F44336",
            fg="white",
            width=12,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_record_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Talk control buttons
        self.start_talk_button = tk.Button(
            recording_frame,
            text="Start Talking",
            command=self.start_talking,
            bg="#2196F3",
            fg="white",
            width=12,
            state=tk.DISABLED,
            **button_style
        )
        self.start_talk_button.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        self.stop_talk_button = tk.Button(
            recording_frame,
            text="Stop Talking",
            command=self.stop_talking,
            bg="#FF9800",
            fg="white",
            width=12,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_talk_button.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        # Read controls frame
        read_frame = tk.LabelFrame(controls_frame, text="Text Reading Controls", padx=5, pady=5)
        read_frame.pack(fill=tk.X, pady=5)
        
        # Configure grid weights
        read_frame.grid_columnconfigure(0, weight=1)
        read_frame.grid_columnconfigure(1, weight=1)
        
        # Read/Stop Read buttons
        self.read_button = tk.Button(
            read_frame,
            text="Read Text",
            command=self.start_reading,
            bg="#2196F3",
            fg="white",
            width=12,
            **button_style
        )
        self.read_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.stop_read_button = tk.Button(
            read_frame,
            text="Stop Reading",
            command=self.stop_reading,
            bg="#F44336",
            fg="white",
            width=12,
            state=tk.DISABLED,
            **button_style
        )
        self.stop_read_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Action buttons frame
        action_frame = tk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        # Configure grid weights
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        action_frame.grid_columnconfigure(2, weight=1)
        
        # Copy button
        copy_button = tk.Button(
            action_frame,
            text="Copy to Main",
            command=self.copy_to_main,
            bg="#2196F3",
            fg="white",
            width=12,
            **button_style
        )
        copy_button.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        # Clear button
        clear_button = tk.Button(
            action_frame,
            text="Clear Text",
            command=self.clear_text,
            bg="#9E9E9E",
            fg="white",
            width=12,
            **button_style
        )
        clear_button.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Close button
        close_button = tk.Button(
            action_frame,
            text="Close",
            command=self.window.destroy,
            width=12,
            **button_style
        )
        close_button.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
            
        try:
            # Get selected device
            selected_name = self.device_var.get()
            if not selected_name:
                raise Exception("Please select a microphone")
                
            # Find the selected device
            selected_device = None
            for device in self.input_devices:
                if device['name'].split(',')[0].strip() == selected_name:
                    selected_device = device
                    break
                    
            if not selected_device:
                raise Exception(f"Selected device '{selected_name}' not found")
            
            self.is_recording = True
            self.audio_queue = queue.Queue(maxsize=2000)  # Increased queue size
            self.status_var.set("Recording ready - Click 'Start Talking' to begin")
            
            # Update button states
            self.start_record_button.config(state=tk.DISABLED)
            self.stop_record_button.config(state=tk.NORMAL)
            self.start_talk_button.config(state=tk.NORMAL)
            self.stop_talk_button.config(state=tk.DISABLED)
            self.device_dropdown.config(state=tk.DISABLED)
            
            def record_audio():
                try:
                    # Configure stream with optimal settings
                    with sd.InputStream(device=selected_device['name'],
                                      samplerate=44100,
                                      channels=1,
                                      dtype=np.int16,
                                      blocksize=4096,  # Increased block size
                                      latency='high') as stream:
                        while self.is_recording:
                            try:
                                data, overflowed = stream.read(4096)  # Increased read size
                                if overflowed:
                                    print("Audio buffer overflow - adjusting...")
                                    time.sleep(0.05)  # Shorter delay on overflow
                                    continue
                                if self.is_talking:
                                    # Check if queue is full before adding
                                    if not self.audio_queue.full():
                                        self.audio_queue.put(data)
                                    else:
                                        # If queue is full, remove oldest item
                                        try:
                                            self.audio_queue.get_nowait()
                                            self.audio_queue.put(data)
                                        except queue.Empty:
                                            pass
                                time.sleep(0.02)  # Reduced sleep time for better responsiveness
                            except Exception as e:
                                print(f"Error in audio read loop: {e}")
                                time.sleep(0.05)
                except Exception as e:
                    print(f"Recording error: {e}")
                    self.window.after(0, lambda: self.status_var.set(f"Recording error: {str(e)}"))
                    self.is_recording = False
            
            self.recording_thread = threading.Thread(target=record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
        except Exception as e:
            self.status_var.set(f"Error starting recording: {str(e)}")
            self.is_recording = False

    def stop_recording(self):
        """Stop recording and process the audio"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.is_talking = False
        self.status_var.set("Processing speech...")
        
        # Update button states
        self.start_record_button.config(state=tk.NORMAL)
        self.stop_record_button.config(state=tk.DISABLED)
        self.start_talk_button.config(state=tk.DISABLED)
        self.stop_talk_button.config(state=tk.DISABLED)
        self.device_dropdown.config(state='readonly')
        
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        # Process the recorded audio
        try:
            # Save recorded audio to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                with wave.open(temp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(44100)
                    
                    while not self.audio_queue.empty():
                        data = self.audio_queue.get()
                        wf.writeframes(data.tobytes())
                
                # Convert audio to text with enhanced settings
                with sr.AudioFile(temp_path) as source:
                    # Adjust for ambient noise with longer duration
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    
                    # Record with enhanced settings
                    audio = self.recognizer.record(source)
                    
                    # Try multiple recognition attempts with different settings
                    text = None
                    try:
                        # First attempt with default settings
                        text = self.recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        try:
                            # Second attempt with language hint and show_all
                            results = self.recognizer.recognize_google(audio, language='en-US', show_all=True)
                            if results and 'alternative' in results:
                                # Get the most confident result
                                text = results['alternative'][0]['transcript']
                        except sr.UnknownValueError:
                            try:
                                # Third attempt with different settings
                                self.recognizer.energy_threshold = 150
                                self.recognizer.pause_threshold = 0.8
                                audio = self.recognizer.record(source)
                                text = self.recognizer.recognize_google(audio, language='en-US')
                            except:
                                pass
                    
                    if text:
                        self.text_area.delete(1.0, tk.END)
                        self.text_area.insert(tk.END, text)
                        self.status_var.set("Speech converted to text successfully")
                    else:
                        self.status_var.set("Could not recognize speech clearly")
                
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            self.status_var.set(f"Error processing speech: {str(e)}")
            print(f"Speech processing error: {e}")

    def start_talking(self):
        """Start talking mode"""
        if not self.is_recording:
            return
            
        self.is_talking = True
        self.status_var.set("Recording... Speak now")
        
        # Update button states
        self.start_talk_button.config(state=tk.DISABLED)
        self.stop_talk_button.config(state=tk.NORMAL)

    def stop_talking(self):
        """Stop talking mode"""
        if not self.is_talking:
            return
            
        self.is_talking = False
        self.status_var.set("Recording paused - Click 'Start Talking' to continue")
        
        # Update button states
        self.start_talk_button.config(state=tk.NORMAL)
        self.stop_talk_button.config(state=tk.DISABLED)

    def start_reading(self):
        """Start reading the recognized text"""
        if self.is_reading:
            return
            
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            self.status_var.set("No text to read")
            return
            
        try:
            self.is_reading = True
            self.status_var.set("Reading text...")
            
            # Update button states
            self.read_button.config(state=tk.DISABLED)
            self.stop_read_button.config(state=tk.NORMAL)
            
            # Start reading in a separate thread
            threading.Thread(target=self._read_text_thread, args=(text,), daemon=True).start()
            
        except Exception as e:
            self.status_var.set(f"Error reading text: {str(e)}")
            self.is_reading = False
            self.read_button.config(state=tk.NORMAL)
            self.stop_read_button.config(state=tk.DISABLED)

    def stop_reading(self):
        """Stop reading the text"""
        if not self.is_reading:
            return
            
        try:
            self.engine.stop()
            self.is_reading = False
            self.status_var.set("Reading stopped")
            
            # Update button states
            self.read_button.config(state=tk.NORMAL)
            self.stop_read_button.config(state=tk.DISABLED)
            
        except Exception as e:
            self.status_var.set(f"Error stopping reading: {str(e)}")

    def clear_text(self):
        """Clear the text area"""
        self.text_area.delete(1.0, tk.END)
        self.status_var.set("Text cleared")

    def copy_to_main(self):
        """Copy the recognized text to the main window's text area"""
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            # Get the main window's text area and update it
            main_text_area = self.window.master.text_area
            main_text_area.delete(1.0, tk.END)
            main_text_area.insert(tk.END, text)
            self.status_var.set("Text copied to main window")
        else:
            self.status_var.set("No text to copy")

    def test_audio_devices(self):
        """Test available audio devices and show status"""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                self.status_var.set("No audio input devices found!")
                messagebox.showerror("Audio Error", "No audio input devices found. Please check your microphone connection.")
                return
                
            # Get default input device
            default_input = sd.query_devices(kind='input')
            self.status_var.set(f"Using microphone: {default_input['name']}")
            
        except Exception as e:
            error_msg = f"Error testing audio devices: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Audio Error", error_msg)

    def _read_text_thread(self, text):
        """Handle text reading in a separate thread"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            self.window.after(0, lambda: self.status_var.set(f"Error reading text: {str(e)}"))
        finally:
            self.is_reading = False
            self.window.after(0, lambda: [
                self.status_var.set("Ready to record"),
                self.read_button.config(state=tk.NORMAL),
                self.stop_read_button.config(state=tk.DISABLED)
            ])

    def on_close(self):
        """Handle window close"""
        try:
            self.stop_reading()
            if hasattr(self, 'engine') and self.engine:
                self.engine.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.window.destroy()

def test_tesseract(tesseract_cmd_path):
    """Test if the specified Tesseract command works"""
    if not tesseract_cmd_path or not os.path.exists(tesseract_cmd_path):
        print(f"Test Tesseract: Path '{tesseract_cmd_path}' does not exist.")
        return False
    try:
        original_cmd = pytesseract.pytesseract.tesseract_cmd
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
        version = pytesseract.get_tesseract_version()
        pytesseract.pytesseract.tesseract_cmd = original_cmd # Restore original
        print(f"Test Tesseract: Found version {version} at {tesseract_cmd_path}")
        return True
    except pytesseract.TesseractNotFoundError:
        print(f"Test Tesseract: TesseractNotFoundError for path '{tesseract_cmd_path}'.")
        pytesseract.pytesseract.tesseract_cmd = original_cmd # Restore original
        return False
    except Exception as e:
        print(f"Test Tesseract: Error checking version at '{tesseract_cmd_path}': {e}")
        pytesseract.pytesseract.tesseract_cmd = original_cmd # Restore original
        return False

def find_tesseract():
    # First check the portable Tesseract-OCR folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    portable_tesseract = os.path.join(script_dir, 'Tesseract-OCR', 'tesseract.exe')
    
    if os.path.exists(portable_tesseract):
        return portable_tesseract
    
    # If not found in portable folder, try system PATH
    try:
        tesseract_cmd = 'tesseract'
        subprocess.run([tesseract_cmd, '--version'], capture_output=True, check=True)
        return tesseract_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def main():
    """Main entry point with error handling"""
    try:
        print("Starting main function...")
        
        # Set up portable environment first
        print("Setting up portable environment...")
        setup_portable_environment()
        
        # Initialize the application
        print("Initializing ScreenTextSelector...")
        app = ScreenTextSelector()
        
        print("Starting application main loop...")
        app.run()
        
    except Exception as e:
        print(f"Error in main function: {e}")
        print("Stack trace:")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    try:
        print("Starting application...")
        if ensure_virtual_environment():
            # If we're already in the virtual environment, run the main application
            main()
    except Exception as e:
        print(f"Error in virtual environment setup: {e}")
        print("Stack trace:")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)