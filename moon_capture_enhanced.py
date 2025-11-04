"""
Enhanced Moon Photography Script
================================

Advanced moon photography script with multiple capture modes:

STANDARD MODE:
- Images download to computer after each shot
- More reliable, but slower (~3-4 seconds per shot)
- Better for smaller sessions

FAST MODE:
- Images save to camera SD card during shooting
- Much faster capture rate (~0.5-1 second per shot)
- Bulk download after capture completes
- Better for larger sessions

Features:
- Multiple capture presets for different moon phases
- Configurable exposure brackets
- Real-time settings verification
- Comprehensive error handling
- Detailed session statistics
- Progress tracking
"""

from canon_edsdk import CanonCamera, EdsSaveTo
import time
from datetime import datetime
import os
import json


# =============================================================================
# PRESETS - Adjust these for your specific needs
# =============================================================================

PRESETS = {
    'full_moon': {
        'description': 'Full Moon - High contrast, bright areas',
        'brackets': [
            {'name': 'Highlights', 'iso': 100, 'aperture': 11, 'shutter': '1/500', 'frames': 40},
            {'name': 'Normal', 'iso': 100, 'aperture': 8.0, 'shutter': '1/250', 'frames': 40},
            {'name': 'Shadows', 'iso': 100, 'aperture': 5.6, 'shutter': '1/125', 'frames': 20},
        ]
    },
    
    'quarter_moon': {
        'description': 'Quarter Moon - Best detail, dramatic shadows',
        'brackets': [
            {'name': 'Bright Side', 'iso': 100, 'aperture': 8.0, 'shutter': '1/250', 'frames': 50},
            {'name': 'Terminator', 'iso': 100, 'aperture': 5.6, 'shutter': '1/125', 'frames': 50},
            {'name': 'Dark Side', 'iso': 200, 'aperture': 4.0, 'shutter': '1/60', 'frames': 30},
        ]
    },
    
    'crescent_moon': {
        'description': 'Crescent Moon - Low light, earthshine possible',
        'brackets': [
            {'name': 'Lit Crescent', 'iso': 100, 'aperture': 5.6, 'shutter': '1/125', 'frames': 40},
            {'name': 'Earthshine', 'iso': 800, 'aperture': 2.8, 'shutter': '1/15', 'frames': 30},
        ]
    },
    
    'quick_stack': {
        'description': 'Quick Stack - Single exposure, 50 frames',
        'brackets': [
            {'name': 'Main Stack', 'iso': 100, 'aperture': 8.0, 'shutter': '1/250', 'frames': 50},
        ]
    },
    
    'hdr_intensive': {
        'description': 'Intensive HDR - 5 brackets, maximum detail',
        'brackets': [
            {'name': 'Very Under -3', 'iso': 100, 'aperture': 13, 'shutter': '1/1000', 'frames': 25},
            {'name': 'Under -1.5', 'iso': 100, 'aperture': 11, 'shutter': '1/500', 'frames': 30},
            {'name': 'Normal', 'iso': 100, 'aperture': 8.0, 'shutter': '1/250', 'frames': 40},
            {'name': 'Over +1.5', 'iso': 100, 'aperture': 5.6, 'shutter': '1/125', 'frames': 30},
            {'name': 'Very Over +3', 'iso': 100, 'aperture': 4.0, 'shutter': '1/60', 'frames': 25},
        ]
    },
    
    'test': {
        'description': 'Test - 3 quick brackets to verify settings',
        'brackets': [
            {'name': 'Test Normal', 'iso': 100, 'aperture': 8.0, 'shutter': '1/250', 'frames': 3},
            {'name': 'Test Under', 'iso': 100, 'aperture': 11, 'shutter': '1/500', 'frames': 3},
            {'name': 'Test Over', 'iso': 100, 'aperture': 5.6, 'shutter': '1/125', 'frames': 3},
        ]
    }
}


class EnhancedMoonCapture:
    """Enhanced moon capture with multiple capture modes"""
    
    def __init__(self, save_directory=None, fast_mode=False):
        self.camera = None
        self.save_directory = save_directory or f"moon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fast_mode = fast_mode
        self.total_shots = 0
        self.successful_shots = 0
        self.session_start = None
        self.images_before_capture = 0
        self.session_stats = {
            'mode': 'fast' if fast_mode else 'standard',
            'brackets': [],
            'errors': []
        }
        
    def setup_camera(self):
        """Initialize and configure camera"""
        print("\n" + "="*70)
        print("CAMERA SETUP")
        print("="*70)
        
        self.camera = CanonCamera()
        self.camera.initialize_sdk()
        
        print("Searching for camera...")
        num_cameras = self.camera.get_camera_list()
        
        if num_cameras == 0:
            raise RuntimeError("No cameras found!")
        
        self.camera.get_camera(0)
        self.camera.open_session()
        
        # Get camera info
        camera_name = self.camera.get_product_name()
        firmware = self.camera.get_firmware_version()
        battery = self.camera.get_battery_level()
        
        print(f"✓ Camera: {camera_name}")
        print(f"✓ Firmware: {firmware}")
        print(f"✓ Battery: {battery}%")
        
        if battery < 50:
            print("⚠ WARNING: Battery below 50%! Consider charging.")
        
        # Configure based on mode
        if self.fast_mode:
            print("\nConfiguring for FAST capture mode...")
            print("✓ Images will save to camera SD card during shooting")
            print("✓ Bulk download will occur after capture completes")
            
            # Set to save to camera only
            self.camera.set_save_to(EdsSaveTo.Camera)
            
            # Count existing images on card
            print("\nChecking SD card...")
            self.images_before_capture = self.camera.get_image_count_on_camera()
            print(f"✓ Current images on card: {self.images_before_capture}")
            
            available_shots = self.camera.get_available_shots()
            print(f"✓ Available shots: {available_shots}")
            
            if available_shots < 100:
                print("⚠ WARNING: Low space on SD card!")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != "y":
                    raise RuntimeError("Cancelled due to low space")
        else:
            print("\nConfiguring for STANDARD capture mode...")
            print("✓ Images will download to computer after each shot")
            
            # Set to save to host
            self.camera.set_save_to(EdsSaveTo.Host)
            self.camera.set_capacity(0x7FFFFFFF, 0x1000)
            
            # Setup download handler
            self.camera.setup_download_handler(
                callback=self.on_image_downloaded,
                save_directory=self.save_directory
            )
        
        # Create directory
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
            print(f"✓ Created: {self.save_directory}")
        
        print("✓ Camera ready!")
        
    def on_image_downloaded(self, filename, save_path):
        """Callback for downloaded images"""
        self.successful_shots += 1
        
    def show_current_settings(self):
        """Display current camera settings"""
        try:
            iso = self.camera.get_iso_readable()
            aperture = self.camera.get_aperture_readable()
            shutter = self.camera.get_shutter_speed_readable()
            
            print(f"  Current: ISO {iso}, f/{aperture}, {shutter}")
        except:
            print("  (Could not read current settings)")
            
    def verify_settings(self, target_iso, target_aperture, target_shutter):
        """
        Verify that settings were applied correctly
        Returns True if all match, False otherwise
        """
        try:
            actual_iso = self.camera.get_iso_readable()
            actual_aperture = self.camera.get_aperture_readable()
            actual_shutter = self.camera.get_shutter_speed_readable()
            
            iso_match = actual_iso == target_iso
            aperture_match = abs(actual_aperture - target_aperture) < 0.1 if actual_aperture else False
            shutter_match = actual_shutter == target_shutter
            
            if not (iso_match and aperture_match and shutter_match):
                print(f"  ⚠ Settings mismatch!")
                if not iso_match:
                    print(f"    ISO: expected {target_iso}, got {actual_iso}")
                if not aperture_match:
                    print(f"    Aperture: expected {target_aperture}, got {actual_aperture}")
                if not shutter_match:
                    print(f"    Shutter: expected {target_shutter}, got {actual_shutter}")
                return False
            
            return True
        except:
            return False
            
    def capture_bracket(self, bracket_config):
        """
        Capture a single bracket
        
        Args:
            bracket_config: Dictionary with bracket settings
        """
        name = bracket_config['name']
        iso = bracket_config['iso']
        aperture = bracket_config['aperture']
        shutter = bracket_config['shutter']
        frames = bracket_config['frames']
        
        print(f"\n{'='*70}")
        print(f"BRACKET: {name}")
        print(f"{'='*70}")
        print(f"Target: ISO {iso}, f/{aperture}, {shutter}")
        print(f"Frames: {frames}")
        
        bracket_stats = {
            'name': name,
            'target_settings': {'iso': iso, 'aperture': aperture, 'shutter': shutter},
            'frames': frames,
            'successful': 0,
            'failed': 0,
            'start_time': time.time()
        }
        
        # Apply settings
        settings_ok = True
        
        try:
            print("\nApplying settings...")
            self.camera.set_iso_quick(iso)
            time.sleep(0.3)
            self.camera.set_aperture_quick(aperture)
            time.sleep(0.3)
            self.camera.set_shutter_speed_quick(shutter)
            time.sleep(0.5)
            
            # Verify
            if not self.verify_settings(iso, aperture, shutter):
                settings_ok = False
                print("  ⚠ Settings could not be verified!")
                print("  Camera must be in Manual (M) mode!")
                response = input("  Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return bracket_stats
                    
        except Exception as e:
            print(f"✗ Error applying settings: {e}")
            settings_ok = False
            
        if settings_ok:
            self.show_current_settings()
            print("  ✓ Settings verified")
        
        # Capture loop
        print("\nCapturing frames...")
        failed_captures = 0
        
        # Different timing based on mode
        if self.fast_mode:
            # Fast mode - minimal delay between shots
            process_time = 0.5  # Just enough for camera to be ready
            print("FAST MODE: Minimal delay between shots")
        else:
            # Standard mode - wait for download
            process_time = 2.5  # Wait for download to complete
            print("STANDARD MODE: Waiting for download after each shot")
        
        for i in range(1, frames + 1):
            self.total_shots += 1
            
            try:
                # Progress indicator
                progress = (i / frames) * 100
                bar_length = 40
                filled = int(bar_length * i / frames)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                print(f'\r  [{bar}] {progress:5.1f}% - Frame {i}/{frames}', end='', flush=True)
                
                # Capture
                self.camera.take_picture()
                
                if self.fast_mode:
                    # Fast mode - just increment counter
                    bracket_stats['successful'] += 1
                    # Minimal processing - just enough for camera to be ready
                    time.sleep(process_time)
                else:
                    # Standard mode - wait for download
                    self.camera.process_events(process_time)
                    bracket_stats['successful'] += 1
                    # Small additional delay
                    time.sleep(0.3)
                
            except Exception as e:
                failed_captures += 1
                bracket_stats['failed'] += 1
                self.session_stats['errors'].append(f"Frame {i}: {str(e)}")
                
                if failed_captures > 5:
                    print(f"\n\n✗ Too many failures ({failed_captures}). Stopping bracket.")
                    break
                    
        print()  # New line after progress bar
        
        # Stats
        bracket_stats['end_time'] = time.time()
        bracket_stats['duration'] = bracket_stats['end_time'] - bracket_stats['start_time']
        self.session_stats['brackets'].append(bracket_stats)
        
        success_rate = (bracket_stats['successful'] / frames * 100) if frames > 0 else 0
        print(f"\n✓ Bracket complete: {bracket_stats['successful']}/{frames} successful ({success_rate:.1f}%)")
        
        if failed_captures > 0:
            print(f"  ⚠ {failed_captures} failed captures")
        
        # Pause before next bracket
        if frames > 0:
            print("  Waiting 3 seconds...")
            time.sleep(3)
            
        return bracket_stats
        
    def bulk_download_images(self):
        """Download all newly captured images from camera (Fast mode only)"""
        if not self.fast_mode:
            print("Bulk download only available in FAST mode")
            return []
            
        print("\n" + "="*70)
        print("BULK DOWNLOAD FROM CAMERA")
        print("="*70)
        
        # Force cache refresh by closing/reopening session
        print("\nRefreshing camera connection to detect new images...")
        self.camera.close_session()
        time.sleep(0.5)
        self.camera.get_camera(0)
        self.camera.open_session()
        time.sleep(0.5)
        
        print("Counting images on camera...")
        current_count = self.camera.get_image_count_on_camera()
        new_images = current_count - self.images_before_capture
        
        print(f"Images before capture: {self.images_before_capture}")
        print(f"Images on camera now: {current_count}")
        print(f"New images to download: {new_images}")
        
        if new_images <= 0:
            print("⚠ No new images to download!")
            return []
        
        print(f"\nDownloading {new_images} images to: {self.save_directory}")
        print("This may take a few minutes...\n")
        
        download_start = time.time()
        downloaded_count = [0]
        
        def progress_callback(filename, path, index, total):
            downloaded_count[0] += 1
            percent = (index / new_images * 100) if new_images > 0 else 0
            print(f"  [{index}/{new_images}] ({percent:.0f}%) {filename}")
            self.successful_shots += 1
        
        downloaded_files = self.camera.download_images_from_camera(
            save_directory=self.save_directory,
            callback=progress_callback,
            max_images=new_images,
        )
        
        download_time = time.time() - download_start
        
        print(f"\n✓ Download complete!")
        print(f"  Downloaded: {len(downloaded_files)} files")
        print(f"  Time: {download_time:.1f} seconds")
        if download_time > 0:
            print(f"  Rate: {len(downloaded_files)/download_time:.1f} files/second")
        print(f"  Location: {os.path.abspath(self.save_directory)}")
        
        return downloaded_files
        
    def run_preset(self, preset_name):
        """Run a predefined preset session"""
        if preset_name not in PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")
            
        preset = PRESETS[preset_name]
        
        print("\n" + "="*70)
        print(f"PRESET: {preset_name.upper()}")
        print("="*70)
        print(f"{preset['description']}")
        print(f"\nBrackets: {len(preset['brackets'])}")
        
        total_frames = sum(b['frames'] for b in preset['brackets'])
        
        # Estimate time based on mode
        if self.fast_mode:
            # Fast mode: ~1 second per frame + bulk download time
            capture_time = total_frames * 1.0  # ~1 second per frame
            download_time = total_frames * 0.5  # ~0.5 seconds per frame for download
            estimated_time = capture_time + download_time
            print(f"Total frames: {total_frames}")
            print(f"Estimated time: {estimated_time/60:.1f} minutes (~{capture_time/60:.1f} min capture + ~{download_time/60:.1f} min download)")
            print(f"Mode: FAST (saving to SD card, bulk download after)")
        else:
            # Standard mode: ~3.5 seconds per frame
            estimated_time = total_frames * 3.5  # ~3.5 seconds per frame
            print(f"Total frames: {total_frames}")
            print(f"Estimated time: {estimated_time/60:.1f} minutes")
            print(f"Mode: STANDARD (downloading each image)")
        
        print()
        
        # Show all brackets
        print("Bracket details:")
        for i, bracket in enumerate(preset['brackets'], 1):
            print(f"  {i}. {bracket['name']}: "
                  f"ISO {bracket['iso']}, f/{bracket['aperture']}, "
                  f"{bracket['shutter']} × {bracket['frames']} frames")
        
        print("\n" + "="*70)
        print("IMPORTANT REMINDERS:")
        print("  ✓ Camera on STABLE tripod")
        print("  ✓ Image stabilization OFF")
        print("  ✓ Camera in MANUAL (M) mode")
        print("  ✓ Moon is in FOCUS")
        print("  ✓ RAW format selected")
        print("="*70)
        
        response = input("\nReady to start capture? (y/n): ")
        if response.lower() != 'y':
            print("Capture cancelled.")
            return
            
        # Start session
        self.session_start = time.time()
        print("\nStarting capture session...")
        time.sleep(2)
        
        # Capture each bracket
        for bracket in preset['brackets']:
            self.capture_bracket(bracket)
            
        # If in fast mode, do bulk download
        if self.fast_mode:
            print("\n" + "="*70)
            print("CAPTURE COMPLETE - STARTING BULK DOWNLOAD")
            print("="*70)
            self.bulk_download_images()
            
        # Session complete
        self.print_session_summary()
        
    def print_session_summary(self):
        """Print detailed session summary"""
        print("\n" + "="*70)
        print("SESSION COMPLETE!")
        print("="*70)
        
        if self.session_start:
            session_duration = time.time() - self.session_start
            print(f"\nSession duration: {session_duration/60:.1f} minutes")
        
        print(f"Capture mode: {'FAST' if self.fast_mode else 'STANDARD'}")
        print(f"Total shots: {self.successful_shots}/{self.total_shots}")
        success_rate = (self.successful_shots / self.total_shots * 100) if self.total_shots > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        print(f"\nSaved to: {os.path.abspath(self.save_directory)}")
        
        # Bracket breakdown
        print("\nBracket Summary:")
        for i, bracket in enumerate(self.session_stats['brackets'], 1):
            print(f"  {i}. {bracket['name']}: "
                  f"{bracket['successful']}/{bracket['frames']} frames "
                  f"({bracket['duration']:.1f}s)")
        
        # Errors
        if self.session_stats['errors']:
            print(f"\nErrors encountered: {len(self.session_stats['errors'])}")
            if len(self.session_stats['errors']) <= 5:
                for error in self.session_stats['errors']:
                    print(f"  • {error}")
        
        # Save session info
        session_info = {
            'date': datetime.now().isoformat(),
            'mode': 'fast' if self.fast_mode else 'standard',
            'total_shots': self.total_shots,
            'successful_shots': self.successful_shots,
            'brackets': self.session_stats['brackets'],
            'errors': self.session_stats['errors']
        }
        
        info_file = os.path.join(self.save_directory, 'session_info.json')
        with open(info_file, 'w') as f:
            json.dump(session_info, f, indent=2)
        
        print(f"\n📊 Session info saved to: session_info.json")
        
        # Next steps
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Review images and discard any blurry frames")
        print("2. Stack each bracket separately using stacking software")
        print("3. Merge the stacked images for HDR (if multiple brackets)")
        print("4. Apply final sharpening and adjustments")
        print("\nSee MOON_CAPTURE_GUIDE.md for detailed processing instructions")
        
    def cleanup(self):
        """Clean up camera connection"""
        if self.camera:
            try:
                self.camera.terminate_sdk()
                print("\n✓ Camera disconnected")
            except:
                pass


def show_presets():
    """Display all available presets"""
    print("\n" + "="*70)
    print("AVAILABLE PRESETS")
    print("="*70)
    
    for i, (name, preset) in enumerate(PRESETS.items(), 1):
        total_frames = sum(b['frames'] for b in preset['brackets'])
        print(f"\n{i}. {name.upper()}")
        print(f"   {preset['description']}")
        print(f"   Brackets: {len(preset['brackets'])}")
        print(f"   Total frames: {total_frames}")


def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║            ENHANCED MOON PHOTOGRAPHY CAPTURE SCRIPT                ║
║              Multi-Bracket Stacking & HDR System                   ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Choose capture mode
    print("\n" + "="*70)
    print("SELECT CAPTURE MODE:")
    print("="*70)
    print("1. STANDARD MODE - Download each image immediately (~3-4 sec/shot)")
    print("   • More reliable, better for smaller sessions")
    print("   • Images download to computer after each shot")
    print()
    print("2. FAST MODE - Bulk download after capture (~0.5-1 sec/shot)")
    print("   • Much faster capture rate, better for larger sessions")
    print("   • Images save to SD card during shooting")
    print("   • Bulk download occurs after all captures complete")
    print("   • Requires sufficient space on camera SD card")
    print()
    print("3. EXIT")
    
    try:
        mode_choice = input("\nSelect mode (1-3): ").strip()
        mode_num = int(mode_choice)
        
        if mode_num == 3:
            print("Goodbye!")
            return
            
        if mode_num not in [1, 2]:
            print("Invalid choice. Exiting.")
            return
            
        fast_mode = (mode_num == 2)
        
    except ValueError:
        print("Invalid input. Exiting.")
        return
    
    # Show presets
    show_presets()
    
    # Select preset
    print("\n" + "="*70)
    print("SELECT PRESET:")
    print("="*70)
    preset_names = list(PRESETS.keys())
    for i, name in enumerate(preset_names, 1):
        print(f"  {i}. {name}")
    print(f"  {len(preset_names) + 1}. EXIT")
    
    try:
        choice = input(f"\nEnter choice (1-{len(preset_names) + 1}): ").strip()
        choice_num = int(choice)
        
        if choice_num == len(preset_names) + 1:
            print("Goodbye!")
            return
            
        if 1 <= choice_num <= len(preset_names):
            preset_name = preset_names[choice_num - 1]
        else:
            print("Invalid choice. Exiting.")
            return
            
    except ValueError:
        print("Invalid input. Exiting.")
        return
    
    # Run session
    session = EnhancedMoonCapture(fast_mode=fast_mode)
    
    try:
        session.setup_camera()
        session.run_preset(preset_name)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Capture interrupted by user")
        if session.total_shots > 0:
            print(f"Captured {session.total_shots} images before interruption")
            
            # If in fast mode, offer to download captured images
            if fast_mode and session.total_shots > 0:
                response = input("\nDownload captured images? (y/n): ")
                if response.lower() == 'y':
                    session.bulk_download_images()
                    
            session.print_session_summary()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()