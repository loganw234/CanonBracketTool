# Canon Exposure Bracketing Tool

A web-based application for controlling Canon cameras to create exposure bracketed sequences, particularly optimized for moon photography and other specialized photography techniques.

## Features

- Connect to Canon cameras via the Canon EDSDK
- Create and manage exposure bracketing presets
- Execute complex capture sequences with precise control over:
  - ISO
  - Aperture
  - Shutter speed
  - Number of frames
- Real-time status updates via WebSocket
- Preset management system with categories
- Support for specialized photography techniques:
  - Moon photography
  - HDR sequences
  - Focus stacking
  - Timelapse

## Screenshots

Here are some screenshots of the application interface:

![Main Interface](Screenshots/Screenshot%202025-11-03%20211531.png)


![Preset Management](Screenshots/Screenshot%202025-11-03%20211540.png)


![Capture Settings](Screenshots/Screenshot%202025-11-03%20211552.png)


![Results View](Screenshots/Screenshot%202025-11-03%20211623.png)


## Requirements

- Canon DSLR or mirrorless camera compatible with Canon EDSDK
- Windows operating system (EDSDK.dll is included for Windows)
- Python 3.7+
- Flask and Flask-SocketIO (see requirements.txt)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/loganw234/CanonBracketTool.git
   cd CanonBracketTool
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Connect your Canon camera via USB and turn it on

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Use the web interface to:
   - Connect to your camera
   - Create or select presets
   - Configure capture settings
   - Execute capture sequences

## Important Camera Settings

For best results:
- Set your camera to Manual (M) mode
- Turn off image stabilization when using a tripod
- Use a stable tripod for long exposure sequences
- Ensure your camera has sufficient battery and memory card space

## Project Structure

- `app.py` - Main Flask application
- `canon_edsdk.py` - Python wrapper for Canon EDSDK
- `EDSDK.dll` - Canon SDK library for Windows
- `camera/` - Camera control modules
  - `camera_interface.py` - Interface to Canon EDSDK
  - `capture_controller.py` - Controls capture sequences
  - `exposure_calculator.py` - Calculates exposure settings
- `presets/` - Preset management
  - `preset_manager.py` - Manages saving/loading presets
  - `default_presets/` - Built-in presets
  - `user_presets/` - User-created presets
- `static/` - Web assets (CSS, JavaScript)
- `templates/` - HTML templates
- `captures/` - Directory for captured images

## License

This project uses the Canon EDSDK which has its own licensing terms. The application code is provided for personal use only.

## Acknowledgments

- Canon for providing the EDSDK
- Contributors to the Python Canon EDSDK wrapper
