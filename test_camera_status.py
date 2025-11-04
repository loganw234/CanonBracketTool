"""
Camera Status Test Script

This script tests basic camera interaction without taking pictures.
It focuses on getting camera status and properties to see if we can
interact with the camera in other ways.
"""

from canon_edsdk import CanonCamera, EdsSaveTo, EdsPropertyID_
import time
import os

def test_camera_status():
    print("\n" + "="*70)
    print("CAMERA STATUS TEST")
    print("="*70)
    
    # Initialize camera
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
    
    # Test getting various properties
    print("\n" + "="*70)
    print("TESTING CAMERA PROPERTIES")
    print("="*70)
    
    properties_to_test = [
        (EdsPropertyID_.AEMode, "AE Mode"),
        (EdsPropertyID_.Av, "Aperture Value"),
        (EdsPropertyID_.Tv, "Shutter Speed Value"),
        (EdsPropertyID_.ISOSpeed, "ISO Speed Value"),
        (EdsPropertyID_.MeteringMode, "Metering Mode"),
        (EdsPropertyID_.ExposureCompensation, "Exposure Compensation"),
        (EdsPropertyID_.ImageQuality, "Image Quality"),
        (EdsPropertyID_.WhiteBalance, "White Balance"),
        (EdsPropertyID_.ColorTemperature, "Color Temperature"),
        (EdsPropertyID_.PictureStyle, "Picture Style"),
        (EdsPropertyID_.DriveMode, "Drive Mode"),
        (EdsPropertyID_.Evf_Mode, "Live View Mode"),
        (EdsPropertyID_.Evf_OutputDevice, "Live View Output Device"),
        (EdsPropertyID_.Evf_DepthOfFieldPreview, "Depth of Field Preview"),
    ]
    
    for prop_id, prop_name in properties_to_test:
        try:
            value = camera.get_property(prop_id)
            print(f"✓ {prop_name}: {value}")
        except Exception as e:
            print(f"✗ Could not get {prop_name}: {e}")
    
    # Test getting current settings using the readable methods
    print("\n" + "="*70)
    print("TESTING READABLE SETTINGS")
    print("="*70)
    
    try:
        iso = camera.get_iso_readable()
        print(f"✓ ISO: {iso}")
    except Exception as e:
        print(f"✗ Could not get ISO: {e}")
    
    try:
        aperture = camera.get_aperture_readable()
        print(f"✓ Aperture: f/{aperture}")
    except Exception as e:
        print(f"✗ Could not get Aperture: {e}")
    
    try:
        shutter = camera.get_shutter_speed_readable()
        print(f"✓ Shutter Speed: {shutter}")
    except Exception as e:
        print(f"✗ Could not get Shutter Speed: {e}")
    
    # Test setting save location
    print("\n" + "="*70)
    print("TESTING SAVE LOCATION")
    print("="*70)
    
    try:
        print("Setting save location to camera...")
        camera.set_save_to(EdsSaveTo.Camera)
        print("✓ Save location set to camera")
    except Exception as e:
        print(f"✗ Could not set save location to camera: {e}")
    
    try:
        print("Setting save location to host...")
        camera.set_save_to(EdsSaveTo.Host)
        camera.set_capacity(0x7FFFFFFF, 0x1000)
        print("✓ Save location set to host")
    except Exception as e:
        print(f"✗ Could not set save location to host: {e}")
    
    # Test live view
    print("\n" + "="*70)
    print("TESTING LIVE VIEW")
    print("="*70)
    
    try:
        print("Starting live view...")
        camera.start_live_view()
        print("✓ Live view started")
        time.sleep(2)
        print("Stopping live view...")
        camera.end_live_view()
        print("✓ Live view stopped")
    except Exception as e:
        print(f"✗ Could not test live view: {e}")
    
    # Clean up
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    
    print("Disconnecting camera...")
    camera.terminate_sdk()
    print("✓ Camera disconnected")

if __name__ == "__main__":
    try:
        test_camera_status()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()