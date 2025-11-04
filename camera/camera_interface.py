"""
Camera Interface Module

This module provides a wrapper around the canon_edsdk.py library,
handling camera connection, status management, and settings control.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add parent directory to path to import canon_edsdk
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from canon_edsdk import (
        CanonCamera, EdsSaveTo, EdsErrorCodes,
        EdsPropertyID_, EdsDataType
    )
except ImportError:
    print("Error: canon_edsdk.py not found. Please copy it to the project directory.")
    logging.error("canon_edsdk.py not found")

logger = logging.getLogger(__name__)

class CameraInterface:
    """Interface for controlling Canon cameras via EDSDK"""
    
    def __init__(self):
        """Initialize the camera interface"""
        self.camera = None
        self.connected = False
        self.last_error = None
        self.camera_info = {}
        logger.info("Camera interface initialized")
    
    def connect(self):
        """Connect to the camera"""
        try:
            logger.info("Connecting to camera...")
            print("\n" + "="*70)
            print("CAMERA SETUP")
            print("="*70)
            print("Initializing Canon SDK...")
            
            # Initialize the SDK
            self.camera = CanonCamera()
            self.camera.initialize_sdk()
            
            # Get camera list
            print("Searching for camera...")
            num_cameras = self.camera.get_camera_list()
            
            if num_cameras == 0:
                self.last_error = "No cameras found"
                logger.error(self.last_error)
                print("✗ No cameras found!")
                return False
            
            # Connect to the first camera
            print(f"Found {num_cameras} camera(s)")
            self.camera.get_camera(0)
            self.camera.open_session()
            
            # Add a delay after opening session (like in moon_capture_enhanced.py)
            time.sleep(1.0)
            
            # Store the camera index for session refresh
            self.camera_index = 0
            
            # Get camera info
            self.camera_info = {
                'name': self.camera.get_product_name(),
                'firmware': self.camera.get_firmware_version(),
                'battery': self.camera.get_battery_level(),
                'available_shots': self.camera.get_available_shots()
            }
            
            self.connected = True
            logger.info(f"Connected to camera: {self.camera_info['name']}")
            print(f"✓ Camera: {self.camera_info['name']}")
            print(f"✓ Firmware: {self.camera_info['firmware']}")
            print(f"✓ Battery: {self.camera_info['battery']}%")
            print(f"✓ Available shots: {self.camera_info['available_shots']}")
            
            # Set save location to camera by default (like in moon_capture_enhanced.py)
            print("\nConfiguring for capture...")
            print("✓ Images will save to camera SD card")
            self.camera.set_save_to(EdsSaveTo.Camera)
            
            # Add a delay after configuration (like in moon_capture_enhanced.py)
            time.sleep(1.0)
            
            print("\n✓ Camera ready!")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error connecting to camera: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the camera"""
        try:
            if self.camera:
                logger.info("Disconnecting from camera...")
                self.camera.terminate_sdk()
                self.camera = None
                self.connected = False
                return True
            return False
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error disconnecting camera: {e}")
            return False
    
    def get_status(self):
        """Get the current camera status and settings"""
        if not self.connected or not self.camera:
            return {'connected': False, 'error': "Camera not connected"}
        
        try:
            # Update camera info
            self.camera_info = {
                'name': self.camera.get_product_name(),
                'firmware': self.camera.get_firmware_version(),
                'battery': self.camera.get_battery_level(),
                'available_shots': self.camera.get_available_shots()
            }
            
            # Get current settings
            settings = {
                'iso': self.camera.get_iso_readable(),
                'aperture': self.camera.get_aperture_readable(),
                'shutter_speed': self.camera.get_shutter_speed_readable(),
            }
            
            # Try to get additional settings if available
            try:
                settings['white_balance'] = self.camera.get_property(EdsPropertyID_.Evf_WhiteBalance)
            except:
                pass
                
            return {
                'connected': self.connected,
                'info': self.camera_info,
                'settings': settings
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error getting camera status: {e}")
            return {'connected': self.connected, 'error': str(e)}
    
    def check_camera_mode(self):
        """
        Check if the camera is in Manual mode
        Returns True if in Manual mode, False otherwise
        """
        try:
            # Try to get current camera mode
            ae_mode = self.camera.get_property(EdsPropertyID_.AEMode)
            print(f"Current camera AE Mode: {ae_mode}")
            
            # Check if camera is in Manual mode (0 is Manual mode in most Canon cameras)
            if ae_mode == 0:
                print("✓ Camera is in Manual mode")
                return True
            else:
                print("⚠ Camera is NOT in Manual mode!")
                print("  Camera must be in Manual (M) mode for reliable operation")
                print("  Please switch the camera to Manual mode and try again")
                return False
                
        except Exception as e:
            logger.error(f"Error checking camera mode: {e}")
            print(f"Error checking camera mode: {e}")
            return False
    
    def verify_settings(self, target_iso, target_aperture, target_shutter):
        """
        Verify that settings were applied correctly
        Returns True if all match, False otherwise
        """
        try:
            actual_iso = self.camera.get_iso_readable()
            actual_aperture = self.camera.get_aperture_readable()
            actual_shutter = self.camera.get_shutter_speed_readable()
            
            # Convert target_iso to string for comparison
            if isinstance(target_iso, int):
                target_iso = str(target_iso)
                
            # Convert target_aperture to float for comparison
            if isinstance(target_aperture, str):
                target_aperture = float(target_aperture)
                
            iso_match = str(actual_iso) == str(target_iso)
            aperture_match = abs(float(actual_aperture) - float(target_aperture)) < 0.1 if actual_aperture else False
            shutter_match = str(actual_shutter) == str(target_shutter)
            
            if not (iso_match and aperture_match and shutter_match):
                logger.warning("Settings mismatch!")
                if not iso_match:
                    logger.warning(f"ISO: expected {target_iso}, got {actual_iso}")
                if not aperture_match:
                    logger.warning(f"Aperture: expected {target_aperture}, got {actual_aperture}")
                if not shutter_match:
                    logger.warning(f"Shutter: expected {target_shutter}, got {actual_shutter}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error verifying settings: {e}")
            return False
    
    def apply_settings(self, settings):
        """Apply settings to the camera"""
        if not self.connected or not self.camera:
            return False, "Camera not connected"
        
        try:
            # Check if camera is in Manual mode first
            print("\nChecking camera mode before applying settings...")
            is_manual = self.check_camera_mode()
            if not is_manual:
                print("WARNING: Camera is not in Manual mode!")
                print("Settings may not apply correctly. Please switch to Manual mode.")
                print("Continuing anyway, but operation may fail.")
            
            # Apply ISO setting
            if 'iso' in settings:
                try:
                    iso_value = int(settings['iso'])
                    logger.info(f"Setting ISO to {iso_value}")
                    print(f"Setting ISO to {iso_value}...")
                    
                    # Use set_iso_quick as in moon_capture_enhanced.py
                    self.camera.set_iso_quick(iso_value)
                    time.sleep(0.3)  # Add delay as in moon_capture_enhanced.py
                except Exception as e:
                    logger.error(f"Error setting ISO: {e}")
                    return False, f"Error setting ISO: {e}"
            
            # Apply aperture setting
            if 'aperture' in settings:
                try:
                    aperture_value = float(settings['aperture'])
                    logger.info(f"Setting aperture to f/{aperture_value}")
                    print(f"Setting aperture to f/{aperture_value}...")
                    
                    # Use set_aperture_quick as in moon_capture_enhanced.py
                    self.camera.set_aperture_quick(aperture_value)
                    time.sleep(0.3)  # Add delay as in moon_capture_enhanced.py
                except Exception as e:
                    logger.error(f"Error setting aperture: {e}")
                    return False, f"Error setting aperture: {e}"
            
            # Apply shutter speed setting
            if 'shutter_speed' in settings:
                try:
                    shutter_value = settings['shutter_speed']
                    logger.info(f"Setting shutter speed to {shutter_value}")
                    print(f"Setting shutter speed to {shutter_value}...")
                    
                    # Use set_shutter_speed_quick as in moon_capture_enhanced.py
                    self.camera.set_shutter_speed_quick(shutter_value)
                    time.sleep(0.5)  # Add delay as in moon_capture_enhanced.py
                except Exception as e:
                    logger.error(f"Error setting shutter speed: {e}")
                    return False, f"Error setting shutter speed: {e}"
            
            # Apply white balance setting if available
            if 'white_balance' in settings:
                try:
                    wb_value = settings['white_balance']
                    logger.info(f"Setting white balance to {wb_value}")
                    self.camera.set_property(EdsPropertyID_.Evf_WhiteBalance, wb_value)
                    time.sleep(0.3)  # Add delay
                except Exception as e:
                    logger.warning(f"Error setting white balance (non-critical): {e}")
                    # Don't fail the entire operation for white balance
            
            # Add a small delay after all settings are applied
            time.sleep(1.0)
            
            # Verify settings were applied correctly
            if 'iso' in settings and 'aperture' in settings and 'shutter_speed' in settings:
                print("\nVerifying settings were applied correctly...")
                if not self.verify_settings(settings['iso'], settings['aperture'], settings['shutter_speed']):
                    logger.warning("Settings verification failed. Camera must be in Manual (M) mode!")
                    print("WARNING: Settings verification failed. Camera must be in Manual (M) mode!")
                    # Continue anyway, but warn the user
                else:
                    print("✓ Settings verified successfully")
            
            return True, "Settings applied successfully"
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error applying settings: {e}")
            return False, str(e)
    
    def take_picture(self, save_to_camera=False):
        """
        Take a picture with the current settings
        
        Args:
            save_to_camera: Whether to save the picture to the camera (True) or computer (False)
        
        Returns:
            tuple: (success, message)
        """
        if not self.connected or not self.camera:
            return False, "Camera not connected"
        
        try:
            # Configure save location
            if save_to_camera:
                # Fast mode - save to camera
                self.camera.set_save_to(EdsSaveTo.Camera)
            else:
                # Standard mode - save to host
                self.camera.set_save_to(EdsSaveTo.Host)
                self.camera.set_capacity(0x7FFFFFFF, 0x1000)
            
            # Take picture
            logger.info("Taking picture...")
            print("Taking picture...")
            self.camera.take_picture()
            
            if save_to_camera:
                # Fast mode - minimal delay between shots (like in moon_capture_enhanced.py)
                print("Fast mode: Minimal delay after shot...")
                time.sleep(0.5)  # Just enough for camera to be ready
            else:
                # Standard mode - wait for download (like in moon_capture_enhanced.py)
                print("Standard mode: Waiting for download...")
                self.camera.process_events(2.5)  # Wait for download to complete
                time.sleep(0.3)  # Small additional delay
            
            logger.info("Picture taken successfully")
            print("✓ Picture taken successfully")
            return True, "Picture taken successfully"
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error taking picture: {e}")
            return False, str(e)
    
    def setup_download_handler(self, save_directory):
        """Setup download handler for captured images"""
        if not self.connected or not self.camera:
            return False, "Camera not connected"
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            
            # Setup download handler
            def callback(filename, save_path):
                logger.info(f"Downloaded: {filename} to {save_path}")
            
            self.camera.setup_download_handler(
                callback=callback,
                save_directory=save_directory
            )
            
            return True, "Download handler setup successfully"
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error setting up download handler: {e}")
            return False, str(e)
    
    def bulk_download(self, save_directory, max_images=None):
        """
        Download images from camera
        
        Args:
            save_directory: Directory to save images to
            max_images: Maximum number of images to download (newest first)
                        If None, download all images
        
        Returns:
            tuple: (success, message, downloaded_files)
        """
        if not self.connected or not self.camera:
            return False, "Camera not connected", []
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            
            # Download images
            downloaded_files = self.camera.download_images_from_camera(
                save_directory=save_directory,
                max_images=max_images
            )
            
            return True, f"Downloaded {len(downloaded_files)} images", downloaded_files
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error downloading images: {e}")
            return False, str(e), []
    
    def start_capture_session(self):
        """
        Start a fresh capture session
        This should be called at the beginning of a capture sequence
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting fresh capture session...")
            print("\n" + "="*70)
            print("STARTING FRESH CAPTURE SESSION")
            print("="*70)
            
            # First, disconnect completely if already connected
            if self.camera:
                print("Disconnecting existing camera...")
                try:
                    self.camera.terminate_sdk()
                except Exception as e:
                    print(f"Warning during disconnect: {e}")
                self.camera = None
                self.connected = False
                time.sleep(1.0)
            
            # Initialize the SDK fresh
            print("Initializing Canon SDK...")
            self.camera = CanonCamera()
            self.camera.initialize_sdk()
            
            # Get camera list
            print("Searching for camera...")
            num_cameras = self.camera.get_camera_list()
            
            if num_cameras == 0:
                self.last_error = "No cameras found"
                logger.error(self.last_error)
                print("✗ No cameras found!")
                return False
            
            # Connect to the first camera
            print(f"Found {num_cameras} camera(s)")
            self.camera.get_camera(0)
            self.camera.open_session()
            
            # Add a delay after opening session
            time.sleep(1.0)
            
            # Store the camera index
            self.camera_index = 0
            
            # Get camera info
            self.camera_info = {
                'name': self.camera.get_product_name(),
                'firmware': self.camera.get_firmware_version(),
                'battery': self.camera.get_battery_level(),
                'available_shots': self.camera.get_available_shots()
            }
            
            self.connected = True
            logger.info(f"Connected to camera: {self.camera_info['name']}")
            print(f"✓ Camera: {self.camera_info['name']}")
            print(f"✓ Firmware: {self.camera_info['firmware']}")
            print(f"✓ Battery: {self.camera_info['battery']}%")
            print(f"✓ Available shots: {self.camera_info['available_shots']}")
            
            # Set save location to camera by default
            print("\nConfiguring for capture...")
            print("✓ Images will save to camera SD card")
            self.camera.set_save_to(EdsSaveTo.Camera)
            
            # Add a delay after configuration
            time.sleep(1.0)
            
            print("\n✓ Capture session ready!")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error starting capture session: {e}")
            print(f"✗ Error starting capture session: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_last_error(self):
        """Get the last error message"""
        return self.last_error
        
    def adjust_focus(self, step_value):
        """
        Adjust the focus position by a relative amount
        
        Args:
            step_value: Integer value for focus adjustment
                        Positive values move focus farther
                        Negative values move focus closer
                        The absolute value determines the speed (1=slow, 2=medium, 3=fast)
                        
        Returns:
            tuple: (success, message)
        """
        if not self.connected or not self.camera:
            return False, "Camera not connected"
        
        try:
            # Adjust focus using the Canon SDK
            logger.info(f"Adjusting focus by {step_value} steps")
            print(f"Adjusting focus by {step_value} steps...")
            
            # Determine direction and speed from step_value
            direction = 1 if step_value > 0 else -1
            speed = min(3, abs(step_value))
            
            if direction > 0:
                # Move focus farther
                logger.info(f"Moving focus farther with speed {speed}")
                print(f"Moving focus farther with speed {speed}")
                self.camera.focus_far(speed=speed)
            elif direction < 0:
                # Move focus closer
                logger.info(f"Moving focus closer with speed {speed}")
                print(f"Moving focus closer with speed {speed}")
                self.camera.focus_near(speed=speed)
            else:
                # No adjustment needed
                return True, "No focus adjustment needed"
            
            # Add a delay to allow focus to settle
            # Use a longer delay for higher speeds
            settle_time = 0.3 + (speed * 0.1)  # 0.4s for speed 1, 0.5s for speed 2, 0.6s for speed 3
            time.sleep(settle_time)
            
            return True, f"Focus adjusted with direction {direction} and speed {speed}"
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error adjusting focus: {e}")
            print(f"Error adjusting focus: {e}")
            return False, str(e)
        
    def take_picture_direct(self):
        """
        Take a picture with current settings without changing anything
        This is a simplified method that just calls take_picture directly
        without changing any settings or save location
        
        Returns:
            tuple: (success, message)
        """
        if not self.connected or not self.camera:
            return False, "Camera not connected"
        
        try:
            # Check if camera is in Manual mode
            print("\nChecking camera mode...")
            is_manual = self.check_camera_mode()
            if not is_manual:
                print("WARNING: Camera is not in Manual mode!")
                print("Continuing anyway, but operation may fail")
            
            # Get current settings for reference
            try:
                iso = self.camera.get_iso_readable()
                aperture = self.camera.get_aperture_readable()
                shutter = self.camera.get_shutter_speed_readable()
                print(f"Current settings: ISO {iso}, f/{aperture}, {shutter}")
            except:
                print("(Could not read current settings)")
            
            # Add a small delay before taking picture (like in moon_capture_enhanced.py)
            time.sleep(0.5)
            
            # Just take the picture without changing any settings
            logger.info("Taking picture with current settings...")
            print("\nTaking picture...")
            self.camera.take_picture()
            
            # Add a small delay after taking picture (like in moon_capture_enhanced.py)
            time.sleep(0.5)
            
            logger.info("Picture taken successfully")
            print("✓ Picture taken successfully")
            return True, "Picture taken successfully"
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error taking picture: {e}")
            print(f"✗ Error taking picture: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)


# Simple test function
def test():
    """Test the camera interface"""
    camera = CameraInterface()
    
    print("Connecting to camera...")
    result = camera.connect()
    print(f"Connected: {result}")
    
    if result:
        print("\nCamera Status:")
        status = camera.get_status()
        print(f"Camera: {status['info']['name']}")
        print(f"Battery: {status['info']['battery']}%")
        print(f"Settings: ISO {status['settings']['iso']}, "
              f"f/{status['settings']['aperture']}, "
              f"{status['settings']['shutter_speed']}")
        
        print("\nDisconnecting...")
        camera.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    test()