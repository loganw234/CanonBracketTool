"""
Capture Controller Module

This module handles the execution of capture sequences, including
exposure bracketing and focus stacking. It manages the capture process,
error handling, and provides status updates.
"""

import os
import time
import json
import uuid
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class CaptureController:
    """Controller for executing capture sequences"""
    
    def __init__(self, camera_interface, socketio=None):
        """
        Initialize the capture controller
        
        Args:
            camera_interface: Instance of CameraInterface
            socketio: Optional Flask-SocketIO instance for real-time updates
        """
        self.camera = camera_interface
        self.socketio = socketio
        self.active_captures = {}
        self.capture_threads = {}
        logger.info("Capture controller initialized")
        
    def _calculate_total_frames(self, capture_data):
        """
        Calculate the total number of frames to be captured, accounting for focus stacking
        
        Args:
            capture_data: Dictionary with capture parameters
            
        Returns:
            int: Total number of frames to be captured
        """
        # Get focus stacking parameters
        focus_stack_enabled = capture_data.get('focus_stack', {}).get('enabled', False)
        focus_stack_steps = capture_data.get('focus_stack', {}).get('steps', 10)
        
        # Calculate total frames
        total_frames = 0
        brackets = capture_data.get('brackets', [])
        
        for bracket in brackets:
            frames_in_bracket = bracket.get('frames', 0)
            
            if focus_stack_enabled:
                # For each frame in the bracket, we take focus_stack_steps shots
                # Plus one additional shot at the reset position
                total_frames += frames_in_bracket * (focus_stack_steps + 1)
            else:
                # Without focus stacking, just count the frames directly
                total_frames += frames_in_bracket
                
        return total_frames
    
    def start_capture(self, capture_data):
        """
        Start a new capture sequence
        
        Args:
            capture_data: Dictionary with capture parameters
        
        Returns:
            str: Capture ID
        """
        try:
            print("\n" + "="*70)
            print("STARTING CAPTURE SEQUENCE")
            print("="*70)
            print(f"Capture data: {json.dumps(capture_data, indent=2)}")
            
            # Generate a unique ID for this capture
            capture_id = str(uuid.uuid4())
            print(f"Generated capture ID: {capture_id}")
            
            # Create capture info
            capture_info = {
                'id': capture_id,
                'start_time': datetime.now().isoformat(),
                'status': 'initializing',
                'data': capture_data,
                'progress': {
                    'current_bracket': 0,
                    'total_brackets': len(capture_data.get('brackets', [])),
                    'current_frame': 0,
                    'total_frames': self._calculate_total_frames(capture_data),
                    'completed_frames': 0,
                    'failed_frames': 0
                },
                'results': [],
                'errors': []
            }
            
            # Store capture info
            self.active_captures[capture_id] = capture_info
            
            # Start capture thread
            thread = threading.Thread(
                target=self._execute_capture_sequence,
                args=(capture_id,)
            )
            thread.daemon = True
            thread.start()
            
            self.capture_threads[capture_id] = thread
            
            logger.info(f"Started capture sequence {capture_id}")
            print(f"Started capture sequence {capture_id}")
            return capture_id
            
        except Exception as e:
            logger.error(f"Error starting capture: {e}")
            print(f"ERROR starting capture: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _execute_capture_sequence(self, capture_id):
        """
        Execute a capture sequence in a separate thread
        
        Args:
            capture_id: ID of the capture to execute
        """
        if capture_id not in self.active_captures:
            logger.error(f"Capture {capture_id} not found")
            return
        
        capture_info = self.active_captures[capture_id]
        capture_data = capture_info['data']
        
        try:
            # Update status
            capture_info['status'] = 'running'
            self._send_update(capture_id)
            
            # Create save directory
            save_dir = capture_data.get('save_directory', f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # Determine capture mode
            fast_mode = capture_data.get('capture_mode', 'standard') == 'fast'
            
            # Start a fresh capture session
            print("\nStarting fresh capture session...")
            if not self.camera.start_capture_session():
                error_msg = "Failed to start capture session"
                logger.error(error_msg)
                capture_info['errors'].append(error_msg)
                capture_info['status'] = 'error'
                self._send_update(capture_id)
                return
            
            if fast_mode:
                # Fast mode: Save to camera
                logger.info(f"Capture {capture_id} using FAST mode (save to camera)")
                print(f"Using FAST mode (save to camera)")
                
                # Count existing images on card
                try:
                    # Store the count in the capture info for later use
                    images_before = self.camera.camera.get_image_count_on_camera()
                    capture_info['images_before_capture'] = images_before
                    logger.info(f"Images on camera before capture: {images_before}")
                    print(f"Images on camera before capture: {images_before}")
                except Exception as e:
                    logger.warning(f"Could not count images on camera: {e}")
                    capture_info['images_before_capture'] = 0
            else:
                # Standard mode: Save to computer
                logger.info(f"Capture {capture_id} using STANDARD mode (save to computer)")
                print(f"Using STANDARD mode (save to computer)")
                
                # Setup download handler
                self.camera.setup_download_handler(save_dir)
            
            # Execute each bracket
            brackets = capture_data.get('brackets', [])
            for bracket_idx, bracket in enumerate(brackets):
                # Update progress
                capture_info['progress']['current_bracket'] = bracket_idx + 1
                capture_info['progress']['current_frame'] = 0
                self._send_update(capture_id)
                
                # Apply settings for this bracket
                logger.info(f"Applying settings for bracket {bracket_idx+1}/{len(brackets)}: {bracket.get('name', '')}")
                
                settings = {
                    'iso': bracket.get('iso'),
                    'aperture': bracket.get('aperture'),
                    'shutter_speed': bracket.get('shutter_speed')
                }
                
                # Add additional settings if present
                if 'additional_settings' in bracket:
                    settings.update(bracket['additional_settings'])
                
                # Apply settings
                print(f"\nApplying settings for bracket {bracket_idx+1}/{len(brackets)}: {bracket.get('name', '')}")
                print(f"Settings: ISO {settings.get('iso')}, f/{settings.get('aperture')}, {settings.get('shutter_speed')}")
                success, message = self.camera.apply_settings(settings)
                print(f"Apply settings result: {'Success' if success else 'Failed'}")
                if not success:
                    error_msg = f"Failed to apply settings for bracket {bracket_idx+1}: {message}"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    capture_info['errors'].append(error_msg)
                    self._send_update(capture_id)
                    continue
                
                # Check if focus stacking is enabled
                focus_stack_enabled = capture_data.get('focus_stack', {}).get('enabled', False)
                focus_stack_steps = capture_data.get('focus_stack', {}).get('steps', 10)
                focus_stack_step_size = capture_data.get('focus_stack', {}).get('step_size', 3)
                
                if focus_stack_enabled:
                    logger.info(f"Focus stacking enabled: {focus_stack_steps} steps, size {focus_stack_step_size}")
                    print(f"\nFOCUS STACKING ENABLED")
                    print(f"Steps: {focus_stack_steps}, Step Size: {focus_stack_step_size}")
                
                # Execute frames for this bracket
                frames = bracket.get('frames', 0)
                for frame_idx in range(frames):
                    # Check if capture was stopped
                    if capture_info['status'] == 'stopping':
                        logger.info(f"Capture {capture_id} was stopped")
                        capture_info['status'] = 'stopped'
                        self._send_update(capture_id)
                        return
                    
                    # Update progress
                    capture_info['progress']['current_frame'] = frame_idx + 1
                    self._send_update(capture_id)
                    
                    # If focus stacking is enabled, we need to take multiple pictures at different focus positions
                    if focus_stack_enabled:
                        # Get focus stacking parameters
                        focus_stack_speed = capture_data.get('focus_stack', {}).get('speed', 2)
                        focus_stack_direction = capture_data.get('focus_stack', {}).get('direction', 'near')
                        
                        print(f"\nTaking focus stack for frame {frame_idx+1}/{frames}")
                        print(f"Focus positions per frame: {focus_stack_steps}, Step size: {focus_stack_step_size}")
                        print(f"Focus speed: {focus_stack_speed}, Direction: {focus_stack_direction}")
                        print(f"Total shots for this frame: {focus_stack_steps} (1 shot at each focus position)")
                        
                        # Determine the starting position and movement direction based on focus_stack_direction
                        if focus_stack_direction == 'near':
                            # Starting from near focus point and moving outward (farther)
                            print("Starting from NEAR focus point and moving FARTHER")
                            
                            # First move to the starting position (no movement needed if already focused on near point)
                            starting_position = 0  # Already at the near focus point
                            step_direction = focus_stack_step_size  # Positive to move farther
                            
                        else:  # 'far'
                            # Starting from far focus point and moving inward (closer)
                            print("Starting from FAR focus point and moving CLOSER")
                            
                            # First move to the starting position (no movement needed if already focused on far point)
                            starting_position = 0  # Already at the far focus point
                            step_direction = -focus_stack_step_size  # Negative to move closer
                        
                        # Take pictures at each focus position
                        total_movement = 0
                        
                        for focus_idx in range(focus_stack_steps):
                            # Take picture at current focus position
                            logger.info(f"Taking picture for bracket {bracket_idx+1}/{len(brackets)}, frame {frame_idx+1}/{frames}, focus position {focus_idx+1}/{focus_stack_steps}")
                            print(f"Taking picture for bracket {bracket_idx+1}/{len(brackets)}, frame {frame_idx+1}/{frames}, focus position {focus_idx+1}/{focus_stack_steps}")
                            
                            # Take picture with appropriate mode
                            success, message = self.camera.take_picture(save_to_camera=fast_mode)
                            print(f"Take picture result: {'Success' if success else 'Failed'}")
                            
                            if success:
                                capture_info['progress']['completed_frames'] += 1
                                logger.info(f"Picture taken successfully")
                                print(f"Picture taken successfully")
                            else:
                                capture_info['progress']['failed_frames'] += 1
                                error_msg = f"Failed to take picture {frame_idx+1} (focus {focus_idx+1}) for bracket {bracket_idx+1}: {message}"
                                logger.error(error_msg)
                                print(f"ERROR: {error_msg}")
                                capture_info['errors'].append(error_msg)
                            
                            self._send_update(capture_id)
                            
                            # Move to next focus position if not at the last position
                            if focus_idx < focus_stack_steps - 1:
                                direction_text = "farther" if step_direction > 0 else "closer"
                                print(f"Moving focus {direction_text} with speed {focus_stack_speed}...")
                                
                                # Create a step value that includes both direction and speed
                                # The adjust_focus method will use the sign for direction and magnitude for speed
                                step_value = step_direction
                                if abs(step_value) > 0:
                                    # Normalize the step value to have magnitude equal to the speed
                                    step_value = (1 if step_value > 0 else -1) * focus_stack_speed
                                
                                success, message = self.camera.adjust_focus(step_value)
                                if not success:
                                    error_msg = f"Failed to adjust focus: {message}"
                                    logger.error(error_msg)
                                    print(f"ERROR: {error_msg}")
                                    capture_info['errors'].append(error_msg)
                                    break
                                
                                # Keep track of total movement
                                total_movement += step_value
                                
                                # Wait for focus to settle
                                time.sleep(0.5)
                            
                            # Delay between focus positions
                            if fast_mode:
                                print("Fast mode: Waiting 0.5 seconds between focus positions...")
                                time.sleep(0.5)
                            else:
                                print("Standard mode: Waiting 1 second between focus positions...")
                                time.sleep(1.0)
                        
                        # Reset focus to original position
                        print("Resetting focus to original position...")
                        if total_movement != 0:
                            # Move back by the negative of the total movement
                            reset_value = -total_movement
                            self.camera.adjust_focus(reset_value)
                            time.sleep(1.0)
                            
                        # Take picture at this focus position
                        logger.info(f"Taking picture for bracket {bracket_idx+1}/{len(brackets)}, frame {frame_idx+1}/{frames}, reset focus position")
                        print(f"Taking picture for bracket {bracket_idx+1}/{len(brackets)}, frame {frame_idx+1}/{frames}, reset focus position")
                        
                        # Take picture with appropriate mode
                        success, message = self.camera.take_picture(save_to_camera=fast_mode)
                        print(f"Take picture result: {'Success' if success else 'Failed'}")
                            
                        if success:
                            capture_info['progress']['completed_frames'] += 1
                            logger.info(f"Picture taken successfully")
                            print(f"Picture taken successfully")
                        else:
                            capture_info['progress']['failed_frames'] += 1
                            error_msg = f"Failed to take picture {frame_idx+1} (focus {focus_idx+1}) for bracket {bracket_idx+1}: {message}"
                            logger.error(error_msg)
                            print(f"ERROR: {error_msg}")
                            capture_info['errors'].append(error_msg)
                        
                        self._send_update(capture_id)
                        
                        # Delay between focus positions
                        if fast_mode:
                            print("Fast mode: Waiting 0.5 seconds between focus positions...")
                            time.sleep(0.5)
                        else:
                            print("Standard mode: Waiting 1 second between focus positions...")
                            time.sleep(1.0)
                        
                        # Reset focus to center position after the stack
                        print("Resetting focus to center position...")
                        self.camera.adjust_focus(0)
                        time.sleep(0.5)
                        
                    else:
                        # Regular single-focus capture
                        # Take picture
                        logger.info(f"Taking picture {frame_idx+1}/{frames} for bracket {bracket_idx+1}/{len(brackets)}")
                        print(f"Taking picture {frame_idx+1}/{frames} for bracket {bracket_idx+1}/{len(brackets)}")
                        # Take picture with appropriate mode
                        success, message = self.camera.take_picture(save_to_camera=fast_mode)
                        print(f"Take picture result: {'Success' if success else 'Failed'}")
                        
                        if success:
                            capture_info['progress']['completed_frames'] += 1
                            logger.info(f"Picture taken successfully")
                            print(f"Picture taken successfully")
                        else:
                            capture_info['progress']['failed_frames'] += 1
                            error_msg = f"Failed to take picture {frame_idx+1} for bracket {bracket_idx+1}: {message}"
                            logger.error(error_msg)
                            print(f"ERROR: {error_msg}")
                            capture_info['errors'].append(error_msg)
                        
                        self._send_update(capture_id)
                    
                    # Get custom delay from bracket if it exists
                    custom_delay = bracket.get('delay', 0)
                    
                    if custom_delay > 0:
                        print(f"Using custom delay: Waiting {custom_delay} seconds between frames...")
                        time.sleep(custom_delay)
                    else:
                        # Default delay between frames (longer for standard mode)
                        if fast_mode:
                            print("Fast mode: Waiting 1 second between frames...")
                            time.sleep(1.0)
                        else:
                            print("Standard mode: Waiting 3 seconds between frames...")
                            time.sleep(3.0)
            
            # Bulk download if in fast mode
            if fast_mode:
                logger.info(f"Performing bulk download for capture {capture_id}")
                capture_info['status'] = 'downloading'
                self._send_update(capture_id)
                
                # Start a fresh session for download
                print("\nStarting fresh session for download...")
                if not self.camera.start_capture_session():
                    error_msg = "Failed to start session for download"
                    logger.error(error_msg)
                    capture_info['errors'].append(error_msg)
                    # Continue anyway to try to complete the capture
                
                # Count current images
                try:
                    images_after = self.camera.camera.get_image_count_on_camera()
                    images_before = capture_info.get('images_before_capture', 0)
                    new_images = images_after - images_before
                    
                    logger.info(f"Images before capture: {images_before}")
                    logger.info(f"Images after capture: {images_after}")
                    logger.info(f"New images to download: {new_images}")
                    
                    print(f"Images before capture: {images_before}")
                    print(f"Images after capture: {images_after}")
                    print(f"New images to download: {new_images}")
                    
                    if new_images <= 0:
                        logger.warning("No new images to download")
                        print("⚠ No new images to download!")
                        capture_info['status'] = 'completed'
                        capture_info['end_time'] = datetime.now().isoformat()
                        self._send_update(capture_id)
                        return
                except Exception as e:
                    logger.warning(f"Could not count images on camera: {e}")
                    new_images = 0
                new_images = images_after - images_before
                logger.info(f"Images on camera after capture: {images_after}")
                logger.info(f"New images to download: {new_images}")
                
                if new_images > 0:
                    # Download only the new images
                    print(f"\nDownloading {new_images} new images to: {save_dir}")
                    success, message, downloaded_files = self.camera.bulk_download(
                        save_dir,
                        max_images=new_images
                    )
                    
                    if success:
                        logger.info(f"Downloaded {len(downloaded_files)} images")
                        capture_info['results'] = downloaded_files
                    else:
                        error_msg = f"Failed to download images: {message}"
                        logger.error(error_msg)
                        capture_info['errors'].append(error_msg)
                else:
                    logger.warning("No new images to download")
            
            # Save capture info
            self._save_capture_info(capture_id, save_dir)
            
            # Update status
            capture_info['status'] = 'completed'
            capture_info['end_time'] = datetime.now().isoformat()
            self._send_update(capture_id)
            
            logger.info(f"Capture {capture_id} completed")
            
        except Exception as e:
            error_msg = f"Error executing capture {capture_id}: {str(e)}"
            logger.error(error_msg)
            capture_info['errors'].append(error_msg)
            capture_info['status'] = 'error'
            capture_info['end_time'] = datetime.now().isoformat()
            self._send_update(capture_id)
    
    def _save_capture_info(self, capture_id, save_dir):
        """Save capture info to a file"""
        try:
            capture_info = self.active_captures[capture_id]
            
            # Create a copy for saving
            save_info = {
                'id': capture_info['id'],
                'start_time': capture_info['start_time'],
                'end_time': datetime.now().isoformat(),
                'status': capture_info['status'],
                'capture_mode': capture_info['data'].get('capture_mode', 'standard'),
                'brackets': capture_info['data'].get('brackets', []),
                'progress': capture_info['progress'],
                'errors': capture_info['errors'],
                'version': '1.1'  # Adding version to track format changes
            }
            
            # Save to file
            info_file = os.path.join(save_dir, 'capture_info.json')
            with open(info_file, 'w') as f:
                json.dump(save_info, f, indent=2)
            
            logger.info(f"Saved capture info to {info_file}")
            
        except Exception as e:
            logger.error(f"Error saving capture info: {e}")
    
    def _send_update(self, capture_id):
        """Send capture status update via SocketIO"""
        if self.socketio and capture_id in self.active_captures:
            try:
                self.socketio.emit('capture_update', self.active_captures[capture_id])
            except Exception as e:
                logger.error(f"Error sending capture update: {e}")
    
    def get_capture_status(self, capture_id):
        """
        Get the status of a capture sequence
        
        Args:
            capture_id: ID of the capture
        
        Returns:
            dict: Capture status information
        """
        if capture_id in self.active_captures:
            return self.active_captures[capture_id]
        else:
            return {'error': 'Capture not found'}
    
    def stop_capture(self, capture_id):
        """
        Stop a running capture sequence
        
        Args:
            capture_id: ID of the capture to stop
        
        Returns:
            bool: True if successful, False otherwise
        """
        if capture_id in self.active_captures:
            capture_info = self.active_captures[capture_id]
            
            if capture_info['status'] == 'running':
                capture_info['status'] = 'stopping'
                self._send_update(capture_id)
                logger.info(f"Stopping capture {capture_id}")
                return True
            else:
                logger.warning(f"Cannot stop capture {capture_id} with status {capture_info['status']}")
                return False
        else:
            logger.warning(f"Capture {capture_id} not found")
            return False


# Simple test function
def test():
    """Test the capture controller"""
    from camera_interface import CameraInterface
    
    # Initialize components
    camera = CameraInterface()
    controller = CaptureController(camera)
    
    # Connect to camera
    print("Connecting to camera...")
    result = camera.connect()
    if not result:
        print(f"Failed to connect: {camera.get_last_error()}")
        return
    
    print("Connected!")
    
    try:
        # Create a simple capture
        capture_data = {
            'capture_mode': 'standard',
            'save_directory': 'test_capture',
            'brackets': [
                {
                    'name': 'Test Bracket',
                    'iso': 100,
                    'aperture': 8.0,
                    'shutter_speed': '1/125',
                    'frames': 3,
                    'delay': 2.0  # 2 second delay between shots
                }
            ]
        }
        
        # Start capture
        print("Starting capture...")
        capture_id = controller.start_capture(capture_data)
        print(f"Capture ID: {capture_id}")
        
        # Monitor progress
        while True:
            status = controller.get_capture_status(capture_id)
            progress = status['progress']
            print(f"Bracket {progress['current_bracket']}/{progress['total_brackets']}, "
                  f"Frame {progress['current_frame']}/{progress['total_frames']}, "
                  f"Completed: {progress['completed_frames']}, "
                  f"Failed: {progress['failed_frames']}")
            
            if status['status'] in ['completed', 'error', 'stopped']:
                print(f"Capture {status['status']}!")
                break
            
            time.sleep(1)
        
    finally:
        # Disconnect camera
        print("Disconnecting camera...")
        camera.disconnect()


if __name__ == "__main__":
    test()