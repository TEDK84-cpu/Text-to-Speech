# Text-to-Speech Application v3.1.5

A portable text-to-speech application with OCR capabilities that can run from a USB stick. This application allows you to select text from your screen and have it read aloud, making it useful for accessibility and productivity purposes.

## Features

- Text-to-speech conversion with multiple voice options
- Screen text selection with OCR capabilities
- PDF and Word document support
- Gaming Speech Mode for enhanced gaming experience
- Customizable text settings (font, size, color, etc.)
- High contrast mode and auto-hide options
- Multiple voice options (including Microsoft Edge TTS voices)
- Speech-to-text capabilities
- Hotkey support:
  - `Ctrl+Shift+S`: Start text selection
  - `Ctrl+Shift+X`: Stop speech
  - `Ctrl+Shift+R`: Start reading
  - `Ctrl+Shift+G`: Toggle Auto Hide

## Prerequisites

1. **Python Installation**
   - Download and install Python 3.8 or later from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Restart your computer after installation

2. **Tesseract-OCR**
   - Download the latest stable version of Tesseract-OCR for Windows from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Look for the `tesseract-ocr-w64-setup-vX.XX.XX.exe` (64-bit) or `tesseract-ocr-w32-setup-vX.XX.XX.exe` (32-bit) installer.
   - Run the installer. During installation, make sure to select "Install for all users" and note the installation directory.
   - After installation, copy the entire `Tesseract-OCR` folder from the installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to the same directory as this application's `run.bat` and `setup.bat` files.

3. **FFmpeg**
   - The setup script will automatically download and install FFmpeg into the `ffmpeg` folder.
   - If automatic installation fails, you can manually download the latest release from [ffmpeg.org](https://ffmpeg.org/download.html). Download the release for Windows.
   - Extract the downloaded FFmpeg zip file and copy the `ffmpeg.exe`, `ffprobe.exe`, and `ffplay.exe` files from the `bin` folder into the `ffmpeg` folder of the application.

## Installation

1. Clone this repository:
   ```bash   git clone https://github.com/TEDK84-cpu/Text-to-Speech.git
   cd Text-to-Speech
   ```

2. Run the setup script:
   ```bash
   setup.bat
   ```

## Folder Structure

After installation, your folder structure should look like this:

```
Text-to-Speech/
├── ffmpeg/                     # FFmpeg executables
│   ├── ffmpeg.exe
│   ├── ffplay.exe
│   └── ffprobe.exe
├── logs/                      # Log directory
├── temp/                      # Temporary files directory
├── Tesseract-OCR/             # Tesseract OCR files
│   ├── tesseract.exe
│   └── ... (other Tesseract files)
├── __init__.py               # Python package initialization
├── __pycache__/              # Python cache directory
├── app_config.json           # Application configuration file
├── Gaming_Speech.py          # Gaming speech mode module
├── LICENSE                   # MIT License file
├── README.md                 # This documentation file
├── requirements.txt          # Python dependencies
├── run.bat                   # Run script
├── setup.bat                 # Setup script
├── setup_log.txt            # Log file for the setup script
├── text_settings.json       # User interface settings
└── Text-to-Speech.py        # Main application file
```

## Usage

1. Run the application:
   ```bash
   run.bat
   ```

2. Main Features:
   - Text Selection: Use the selection tool to capture text from anywhere on your screen
   - OCR Recognition: The application will automatically detect and convert text from images
   - Multiple Voice Options: Choose from various Microsoft Edge TTS voices
   - Gaming Mode: Access specialized features for gaming with text-to-speech
   - Document Support: Open and read PDF and Word documents
   - Speech Recognition: Convert spoken words to text

3. Default Hotkeys:
   - `Ctrl+Shift+S`: Start text selection
   - `Ctrl+Shift+R`: Start reading selected text
   - `Ctrl+Shift+X`: Stop reading
   - `Ctrl+Shift+G`: Toggle Auto Hide

4. Customization:
   - Font Settings: Customize font family, size, style, and weight
   - Colors: Adjust text and background colors
   - Text Wrapping: Configure how text wraps in the display
   - Voice Settings: Select different voices and adjust speech rate

## Troubleshooting

If you encounter any issues:

1. **Python Issues**
   - Make sure Python is installed and added to PATH.
   - The application is tested with Python 3.8 or later.
   - Try running `python --version` in Command Prompt to verify installation.
   - If Python is not found, reinstall Python and check "Add Python to PATH".

2. **Audio Issues**
   - Make sure FFmpeg is properly installed (check the `ffmpeg` folder for all required executables).
   - Verify that your computer's audio is working.
   - Try running the application with administrator privileges.
   - If text-to-speech isn't working, check that Microsoft Edge TTS services are accessible.

3. **OCR Issues**
   - Ensure the `Tesseract-OCR` folder is present and contains all necessary files.
   - Check that the OCR language data files are present in the tessdata folder.
   - For better OCR results, ensure your screen resolution and text clarity are good.

4. **Gaming Mode Issues**
   - Make sure the application has necessary permissions to run in gaming mode.
   - If auto-hide isn't working, try toggling it with Ctrl+Shift+G.
   - Check that the voice selection is appropriate for gaming use.

5. **General Issues**
   - Review the logs in the `logs` directory for error messages.
   - Ensure all dependencies are installed by checking `requirements.txt`.
   - Try running with administrator privileges if you experience permission issues.
   - Clear the `temp` directory if you experience performance issues.

## Advanced Features

1. **Gaming Speech Mode**
   - Specialized interface for gaming scenarios
   - Always-on-top option
   - Compact mode for minimal interference
   - High contrast mode for better visibility
   - Auto-hide functionality
   - Multiple voice options optimized for gaming

2. **Document Support**
   - PDF file reading
   - Word document support
   - Text file processing
   - Image text extraction (OCR)

3. **Voice Options**
   - Microsoft Edge TTS voices
   - Multiple language support
   - Adjustable speech rate
   - Voice testing feature

4. **Accessibility Features**
   - High contrast mode
   - Customizable font settings
   - Adjustable text colors
   - Screen position memory
   - Auto-hide options

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Before contributing:
1. Check existing issues or create a new one
2. Fork the repository
3. Create a feature branch
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

### Core Technologies
- [Python](https://www.python.org/) - Core programming language
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [FFmpeg](https://ffmpeg.org/) - Multimedia framework

### Python Libraries
- [PyTorch](https://pytorch.org/) - Deep learning framework (CPU version)
- [edge-tts](https://pypi.org/project/edge-tts/) - Microsoft Edge TTS integration
- [pyttsx3](https://pyttsx3.readthedocs.io/) - Text-to-speech engine
- [PyPDF2](https://pypi.org/project/PyPDF2/) - PDF file processing
- [python-docx](https://python-docx.readthedocs.io/) - Word document processing
- [pyautogui](https://pyautogui.readthedocs.io/) - Screen interaction
- [keyboard](https://github.com/boppreh/keyboard) - Keyboard control
- [Pillow](https://python-pillow.org/) - Image processing
- [pytesseract](https://github.com/madmaze/pytesseract) - Python wrapper for Tesseract OCR
- [numpy](https://numpy.org/) - Numerical operations
- [scipy](https://scipy.org/) - Scientific computing
- [mss](https://python-mss.readthedocs.io/) - Fast screen capture
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio processing
- [soundfile](https://python-soundfile.readthedocs.io/) - Audio file I/O
- [PyAudio](https://pypi.org/project/PyAudio/) - Audio I/O
- [pydub](https://github.com/jiaaro/pydub) - Audio file manipulation
- [speech_recognition](https://pypi.org/project/SpeechRecognition/) - Speech recognition
- [psutil](https://psutil.readthedocs.io/) - System and process utilities
- [opencv-python](https://pypi.org/project/opencv-python/) - Computer vision
- [easyocr](https://github.com/JaidedAI/EasyOCR) - Easy OCR in various languages