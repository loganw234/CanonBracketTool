"""
Minimal Camera Test Script

This script follows the exact approach from moon_capture_enhanced.py
to test if we can take a picture with the Canon SDK.
"""

from canon_edsdk import CanonCamera, EdsSaveTo
import time
import os

def test_camera():
    print("\n" + "="*70)
    print("MINIMAL CAMERA TEST")
    print("="*70)
    
    # Initialize camera exactly like moon_capture_enhanced.py
    print("Initializing Canon SDK...")
    camera = CanonCamera()
    camera.initialize_sdk()
    
    print("Searching for camera...")
    num_cameras = camera.get_camera_list()
    
    if num_cameras == 0:
        print("✗ No cameras found!")
        return
    
    print(f"Found {num_cameras} camera(s)")
    camera.get_camera(0)
    camera.open_session()
    
    # Get camera info
    camera_name = camera.get_product_name()
    firmware = camera.get_firmware_version()
    battery = camera.get_battery_level()
    available_shots = camera.get_available_shots()
    
    print(f"✓ Camera: {camera_name}")
    print(f"✓ Firmware: {firmware}")
    print(f"✓ Battery: {battery}%")
    print(f"✓ Available shots: {available_shots}")
    
    # Check camera mode
    try:
        from canon_edsdk import EdsPropertyID_
        ae_mode = camera.get_property(EdsPropertyID_.AEMode)
        print(f"Camera AE Mode: {ae_mode}")
        
        if ae_mode != 0:
            print("⚠ WARNING: Camera is not in Manual mode!")
            print("  Camera should be in Manual (M) mode for reliable operation")
            
            # Ask user if they want to continue
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Test cancelled.")
                camera.terminate_sdk()
                return
    except Exception as e:
        print(f"Could not check camera mode: {e}")
    
    # Configure save location - ALWAYS TO CAMERA like in moon_capture_enhanced.py
    print("\nConfiguring for capture...")
    print("✓ Images will save to camera SD card")
    camera.set_save_to(EdsSaveTo.Camera)
    
    # Add a delay after configuration (like in moon_capture_enhanced.py)
    time.sleep(1.0)
    
    # Get current settings
    try:
        iso = camera.get_iso_readable()
        aperture = camera.get_aperture_readable()
        shutter = camera.get_shutter_speed_readable()
        print(f"Current settings: ISO {iso}, f/{aperture}, {shutter}")
    except Exception as e:
        print(f"Could not read current settings: {e}")
    
    # Take picture
    print("\nTaking picture...")
    try:
        # Take picture exactly like moon_capture_enhanced.py
        camera.take_picture()
        print("✓ Picture taken successfully!")
    except Exception as e:
        print(f"✗ Error taking picture: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    print("\nDisconnecting camera...")
    camera.terminate_sdk()
    print("✓ Camera disconnected")

if __name__ == "__main__":
    try:
        test_camera()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()