"""
Canon Exposure Bracketing Tool - Main Application

This is the main entry point for the Canon Exposure Bracketing Tool.
It sets up the Flask web server and handles routing and API endpoints.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO

# Import camera modules
from camera.camera_interface import CameraInterface
from camera.exposure_calculator import ExposureCalculator
from camera.capture_controller import CaptureController

# Import preset management
from presets.preset_manager import PresetManager

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename=f'logs/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'exposure-bracketing-tool'
socketio = SocketIO(app)

# Initialize components
try:
    camera_interface = CameraInterface()
    exposure_calculator = ExposureCalculator()
    capture_controller = CaptureController(camera_interface, socketio)
    preset_manager = PresetManager('presets')
    
    logger.info("Application components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    print(f"Error initializing components: {e}")

# Create required directories
for directory in ['presets', 'presets/default_presets', 'presets/user_presets', 'logs']:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

# Routes
@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/api/camera/connect', methods=['POST'])
def connect_camera():
    """Connect to the camera"""
    try:
        result = camera_interface.connect()
        return jsonify({"success": result, "message": "Camera connected successfully" if result else "Failed to connect camera"})
    except Exception as e:
        logger.error(f"Error connecting to camera: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/camera/disconnect', methods=['POST'])
def disconnect_camera():
    """Disconnect from the camera"""
    try:
        result = camera_interface.disconnect()
        return jsonify({"success": result, "message": "Camera disconnected successfully" if result else "Failed to disconnect camera"})
    except Exception as e:
        logger.error(f"Error disconnecting camera: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/camera/status', methods=['GET'])
def get_camera_status():
    """Get the current camera status and settings"""
    try:
        status = camera_interface.get_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get all available presets"""
    try:
        presets = preset_manager.get_all_presets()
        return jsonify({"success": True, "presets": presets})
    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id):
    """Get a specific preset by ID"""
    try:
        preset = preset_manager.get_preset(preset_id)
        if preset:
            return jsonify({"success": True, "preset": preset})
        else:
            return jsonify({"success": False, "message": "Preset not found"})
    except Exception as e:
        logger.error(f"Error getting preset {preset_id}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets', methods=['POST'])
def save_preset():
    """Save a new preset or update an existing one"""
    try:
        preset_data = request.json
        result = preset_manager.save_preset(preset_data)
        return jsonify({"success": True, "preset_id": result})
    except Exception as e:
        logger.error(f"Error saving preset: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets/<preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    """Delete a preset"""
    try:
        result = preset_manager.delete_preset(preset_id)
        return jsonify({"success": result, "message": "Preset deleted successfully" if result else "Failed to delete preset"})
    except Exception as e:
        logger.error(f"Error deleting preset {preset_id}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets/import', methods=['POST'])
def import_preset():
    """Import a preset from a file"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file provided"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"})
        
        preset_data = json.loads(file.read())
        result = preset_manager.import_preset(preset_data)
        return jsonify({"success": True, "preset_id": result})
    except Exception as e:
        logger.error(f"Error importing preset: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/presets/<preset_id>/export', methods=['GET'])
def export_preset(preset_id):
    """Export a preset to a file"""
    try:
        preset_path = preset_manager.export_preset(preset_id)
        if preset_path:
            return send_from_directory(os.path.dirname(preset_path), 
                                      os.path.basename(preset_path), 
                                      as_attachment=True)
        else:
            return jsonify({"success": False, "message": "Failed to export preset"})
    except Exception as e:
        logger.error(f"Error exporting preset {preset_id}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/capture/execute', methods=['POST'])
def execute_capture():
    """Execute a capture sequence"""
    try:
        capture_data = request.json
        capture_id = capture_controller.start_capture(capture_data)
        return jsonify({"success": True, "capture_id": capture_id})
    except Exception as e:
        logger.error(f"Error executing capture: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/capture/<capture_id>/status', methods=['GET'])
def get_capture_status(capture_id):
    """Get the status of a capture sequence"""
    try:
        status = capture_controller.get_capture_status(capture_id)
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"Error getting capture status for {capture_id}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/capture/<capture_id>/stop', methods=['POST'])
def stop_capture(capture_id):
    """Stop a capture sequence"""
    try:
        result = capture_controller.stop_capture(capture_id)
        return jsonify({"success": result, "message": "Capture stopped successfully" if result else "Failed to stop capture"})
    except Exception as e:
        logger.error(f"Error stopping capture {capture_id}: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/capture/test', methods=['POST'])
def test_capture_settings():
    """Test capture settings without actually taking photos"""
    try:
        print("\n" + "="*70)
        print("TEST CAPTURE SETTINGS")
        print("="*70)
        
        test_data = request.json
        print(f"Received test data: {json.dumps(test_data, indent=2)}")
        
        brackets = test_data.get('brackets', [])
        
        if not brackets:
            print("ERROR: No brackets provided for testing")
            return jsonify({"success": False, "message": "No brackets provided for testing"})
        
        print(f"Testing {len(brackets)} brackets")
        
        # Initialize results
        results = []
        all_valid = True
        
        # Test each bracket
        for i, bracket in enumerate(brackets):
            result = {
                "bracket_index": i,
                "bracket_name": bracket.get('name', f"Bracket {i+1}"),
                "valid": True
            }
            
            # Validate ISO
            try:
                iso = int(bracket.get('iso', 0))
                if iso < 100 or iso > 6400:
                    result["warning"] = f"ISO value {iso} may be out of supported range (100-6400)"
            except (ValueError, TypeError):
                result["valid"] = False
                result["error"] = f"Invalid ISO value: {bracket.get('iso')}"
                all_valid = False
            
            # Validate aperture
            try:
                aperture = float(bracket.get('aperture', 0))
                if aperture < 1.4 or aperture > 22:
                    result["warning"] = f"Aperture value f/{aperture} may be out of supported range (f/1.4-f/22)"
            except (ValueError, TypeError):
                result["valid"] = False
                result["error"] = f"Invalid aperture value: {bracket.get('aperture')}"
                all_valid = False
            
            # Validate shutter speed
            shutter = bracket.get('shutter_speed', '')
            if not shutter:
                result["valid"] = False
                result["error"] = "Missing shutter speed"
                all_valid = False
            elif isinstance(shutter, str):
                if '/' in shutter:
                    try:
                        parts = shutter.split('/')
                        num = float(parts[0])
                        denom = float(parts[1])
                        if denom == 0:
                            result["valid"] = False
                            result["error"] = f"Invalid shutter speed (division by zero): {shutter}"
                            all_valid = False
                        elif num/denom < 1/8000 or num/denom > 30:
                            result["warning"] = f"Shutter speed {shutter} may be out of supported range (30s-1/8000s)"
                    except (ValueError, IndexError):
                        result["valid"] = False
                        result["error"] = f"Invalid shutter speed format: {shutter}"
                        all_valid = False
                else:
                    try:
                        seconds = float(shutter)
                        if seconds < 1/8000 or seconds > 30:
                            result["warning"] = f"Shutter speed {shutter}s may be out of supported range (30s-1/8000s)"
                    except ValueError:
                        result["valid"] = False
                        result["error"] = f"Invalid shutter speed value: {shutter}"
                        all_valid = False
            
            # Validate frames
            try:
                frames = int(bracket.get('frames', 0))
                if frames <= 0:
                    result["valid"] = False
                    result["error"] = f"Invalid number of frames: {frames}"
                    all_valid = False
                elif frames > 100:
                    result["warning"] = f"Large number of frames ({frames}) may cause long capture times"
            except (ValueError, TypeError):
                result["valid"] = False
                result["error"] = f"Invalid frames value: {bracket.get('frames')}"
                all_valid = False
            
            # Add result to results list
            results.append(result)
        
        # If camera is connected, actually test the settings by taking a test shot with each bracket
        if camera_interface.connected:
            print("\nCamera is connected. Starting test capture session...")
            logger.info("Starting test capture session")
            
            # Start a fresh capture session
            if not camera_interface.start_capture_session():
                print("Failed to start capture session. Cannot test settings.")
                return jsonify({"success": False, "message": "Failed to start capture session"})
            
            # Create a temporary directory for test shots if it doesn't exist
            test_dir = os.path.join('captures', 'test_shots')
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)
            
            # Setup download handler
            camera_interface.setup_download_handler(test_dir)
            
            # Test each bracket by taking a test shot
            for i, bracket in enumerate(brackets):
                result_index = i
                result = results[result_index]
                
                # Skip invalid settings
                if not result.get('valid', True):
                    continue
                
                try:
                    # Extract settings and ensure proper types
                    # ISO must be an integer for the Canon SDK
                    try:
                        iso_value = int(bracket.get('iso', 100))
                    except (ValueError, TypeError):
                        iso_value = 100  # Default to ISO 100 if conversion fails
                        
                    settings = {
                        'iso': iso_value,  # Ensure ISO is an integer
                        'aperture': float(bracket.get('aperture', 8.0)),
                        'shutter_speed': str(bracket.get('shutter_speed', '1/125'))
                    }
                    
                    # Add additional settings if available
                    if 'additional_settings' in bracket:
                        if 'white_balance' in bracket['additional_settings']:
                            settings['white_balance'] = bracket['additional_settings']['white_balance']
                    
                    # Apply settings to camera
                    print(f"\nTesting bracket {i+1}/{len(brackets)}: {result['bracket_name']}")
                    print(f"Settings: ISO {settings['iso']}, f/{settings['aperture']}, {settings['shutter_speed']}")
                    logger.info(f"Testing bracket {i+1}: {result['bracket_name']} with settings: {settings}")
                    
                    # Get current camera settings for reference
                    camera_status = camera_interface.get_status()
                    print(f"Current camera settings: ISO {camera_status['settings']['iso']}, f/{camera_status['settings']['aperture']}, {camera_status['settings']['shutter_speed']}")
                    
                    # Apply settings
                    print("Applying settings to camera...")
                    success, message = camera_interface.apply_settings(settings)
                    print(f"Apply settings result: {'Success' if success else 'Failed'}")
                    if not success:
                        print(f"Error message: {message}")
                    
                    # If settings fail, try with fallback values
                    if not success:
                        logger.warning(f"Initial settings failed: {message}. Trying fallback values.")
                        
                        # Create fallback settings
                        fallback_settings = {
                            'iso': 100,  # Most cameras support ISO 100
                            'aperture': 8.0,  # f/8 is usually supported
                            'shutter_speed': '1/125'  # 1/125 is usually supported
                        }
                        
                        # Try with fallback settings
                        logger.info(f"Trying fallback settings: {fallback_settings}")
                        print(f"Trying fallback settings: ISO {fallback_settings['iso']}, f/{fallback_settings['aperture']}, {fallback_settings['shutter_speed']}")
                        success, fallback_message = camera_interface.apply_settings(fallback_settings)
                        
                        if success:
                            # Fallback worked, add a warning
                            if 'warning' not in result:
                                result['warning'] = f"Original settings failed, used fallback settings: {message}"
                            logger.info("Fallback settings applied successfully")
                            settings = fallback_settings  # Use the fallback settings for the test shot
                        else:
                            # Both original and fallback failed
                            result['valid'] = False
                            result['error'] = f"Failed to apply settings: {message}. Fallback also failed: {fallback_message}"
                            all_valid = False
                            continue
                    
                    # Take a test shot with the applied settings
                    print("\n" + "="*70)
                    print("IMPORTANT REMINDERS:")
                    print("  ✓ Camera on STABLE tripod")
                    print("  ✓ Image stabilization OFF")
                    print("  ✓ Camera in MANUAL (M) mode")
                    print("  ✓ Moon is in FOCUS")
                    print("  ✓ RAW format selected")
                    print("="*70)
                    
                    print("\nTaking test shot with applied settings...")
                    success, message = camera_interface.take_picture(save_to_camera=True)
                    print(f"Test shot result: {'Success' if success else 'Failed'}")
                    if not success:
                        print(f"Error message: {message}")
                    
                    if not success:
                        result['valid'] = False
                        result['error'] = f"Failed to take picture: {message}"
                        all_valid = False
                    else:
                        result['test_shot'] = True
                        result['message'] = "Test shot successful"
                        
                    # Add a significant delay between shots to ensure camera is ready
                    print("\nWaiting for camera to be ready for next shot...")
                    time.sleep(3.0)  # 3 second delay between shots
                    
                except Exception as e:
                    result['valid'] = False
                    result['error'] = f"Error during test: {str(e)}"
                    all_valid = False
                    logger.error(f"Error testing bracket {i+1}: {e}")
        
        return jsonify({
            "success": all_valid,
            "message": "All settings are valid" if all_valid else "Some settings are invalid",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error testing capture settings: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

# Socket.IO events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")

# Main entry point
if __name__ == '__main__':
    try:
        logger.info("Starting application")
        print("Starting Canon Exposure Bracketing Tool...")
        print("Open your browser and navigate to: http://localhost:5000")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Error running application: {e}")
        print(f"Error running application: {e}")