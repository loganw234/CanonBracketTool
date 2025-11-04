"""
Exposure Calculator Module

This module handles exposure calculations, EV conversions, and bracket generation.
It provides utilities for working with the exposure triangle (ISO, aperture, shutter speed)
and generating exposure brackets based on EV steps or direct parameter specification.
"""

import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class ExposureCalculator:
    """Calculator for exposure settings and brackets"""
    
    # Standard full-stop ISO values
    ISO_VALUES = [
        50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200, 102400
    ]
    
    # Standard full-stop aperture values (f-stops)
    APERTURE_VALUES = [
        1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0, 32.0
    ]
    
    # Standard full-stop shutter speeds (in seconds)
    SHUTTER_SPEEDS = [
        "512", "256", "128", "64", "30", "15", "8", "4", "2", "1", "1/2", "1/4", "1/8", "1/15", "1/30",
        "1/60", "1/125", "1/250", "1/500", "1/1000", "1/2000", "1/4000", "1/8000"
    ]
    
    # Third-stop ISO values
    ISO_VALUES_THIRD = [
        50, 64, 80, 100, 125, 160, 200, 250, 320, 400, 500, 640, 800, 1000, 1250, 
        1600, 2000, 2500, 3200, 4000, 5000, 6400, 8000, 10000, 12800, 16000, 20000, 
        25600, 32000, 40000, 51200, 64000, 80000, 102400
    ]
    
    # Third-stop aperture values
    APERTURE_VALUES_THIRD = [
        1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.2, 3.5, 4.0, 4.5, 5.0, 
        5.6, 6.3, 7.1, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 16.0, 18.0, 20.0, 22.0, 
        25.0, 29.0, 32.0
    ]
    
    # Third-stop shutter speeds
    SHUTTER_SPEEDS_THIRD = [
        "512", "400", "320", "256", "200", "160", "128", "100", "80", "64", "50", "40", "30", "25", "20", "15", "13", "10", "8", "6", "5", "4", "3.2", "2.5", "2",
        "1.6", "1.3", "1", "0.8", "0.6", "0.5", "0.4", "0.3", "1/4", "1/5", "1/6",
        "1/8", "1/10", "1/13", "1/15", "1/20", "1/25", "1/30", "1/40", "1/50",
        "1/60", "1/80", "1/100", "1/125", "1/160", "1/200", "1/250", "1/320",
        "1/400", "1/500", "1/640", "1/800", "1/1000", "1/1250", "1/1600", "1/2000",
        "1/2500", "1/3200", "1/4000", "1/5000", "1/6400", "1/8000"
    ]
    
    def __init__(self):
        """Initialize the exposure calculator"""
        logger.info("Exposure calculator initialized")
    
    def calculate_ev(self, iso, aperture, shutter_speed):
        """
        Calculate the Exposure Value (EV) for given exposure settings
        
        Args:
            iso: ISO value (e.g., 100, 200, 400)
            aperture: Aperture value (e.g., 2.8, 4.0, 5.6)
            shutter_speed: Shutter speed as string (e.g., "1/125", "1/250")
        
        Returns:
            float: The calculated EV value at ISO 100
        """
        try:
            # Convert shutter speed to seconds
            if "/" in shutter_speed:
                parts = shutter_speed.split("/")
                shutter_seconds = float(parts[0]) / float(parts[1])
            else:
                shutter_seconds = float(shutter_speed)
            
            # Calculate EV100
            ev100 = math.log2((aperture * aperture * 100) / (shutter_seconds * iso))
            
            logger.info(f"Calculated EV100: {ev100:.2f} for ISO {iso}, f/{aperture}, {shutter_speed}")
            return ev100
            
        except Exception as e:
            logger.error(f"Error calculating EV: {e}")
            return None
    
    def get_settings_for_ev(self, ev, iso=100, priority="aperture", preferred_aperture=8.0):
        """
        Get exposure settings for a given EV value
        
        Args:
            ev: Exposure Value at ISO 100
            iso: ISO value to use
            priority: Which parameter to prioritize ("aperture", "shutter", or "iso")
            preferred_aperture: Preferred aperture value if priority is "aperture"
        
        Returns:
            dict: Dictionary with iso, aperture, and shutter_speed
        """
        try:
            if priority == "aperture":
                # Find the closest standard aperture to the preferred value
                aperture = min(self.APERTURE_VALUES, key=lambda x: abs(x - preferred_aperture))
                
                # Calculate required shutter speed
                shutter_seconds = (aperture * aperture * 100) / (iso * (2 ** ev))
                
                # Apply calibration factor for longer exposures
                if shutter_seconds > 30:
                    # The standard EV chart shows longer exposures than the formula calculates
                    # This calibration factor helps match the chart values
                    shutter_seconds *= 1.0  # Adjust this factor if needed
                
                # Find the closest standard shutter speed
                shutter_speed = self._find_closest_shutter_speed(shutter_seconds)
                
            elif priority == "shutter":
                # Use 1/60 as a default preferred shutter speed
                preferred_shutter = "1/60"
                
                # Convert to seconds
                if "/" in preferred_shutter:
                    parts = preferred_shutter.split("/")
                    preferred_seconds = float(parts[0]) / float(parts[1])
                else:
                    preferred_seconds = float(preferred_shutter)
                
                # Calculate required aperture
                aperture_value = math.sqrt((iso * preferred_seconds * (2 ** ev)) / 100)
                
                # Find the closest standard aperture
                aperture = min(self.APERTURE_VALUES, key=lambda x: abs(x - aperture_value))
                
                # Use the preferred shutter speed
                shutter_speed = preferred_shutter
                
            else:  # priority == "iso"
                # Use f/8 as a default aperture
                aperture = 8.0
                
                # Use 1/125 as a default shutter speed
                shutter_speed = "1/125"
                
                # Convert shutter speed to seconds
                if "/" in shutter_speed:
                    parts = shutter_speed.split("/")
                    shutter_seconds = float(parts[0]) / float(parts[1])
                else:
                    shutter_seconds = float(shutter_speed)
                
                # Calculate required ISO
                iso_value = (aperture * aperture * 100) / (shutter_seconds * (2 ** ev))
                
                # Find the closest standard ISO
                iso = min(self.ISO_VALUES, key=lambda x: abs(x - iso_value))
            
            # Format shutter speed for display if needed
            display_shutter = shutter_speed
            
            logger.info(f"Settings for EV {ev:.2f}: ISO {iso}, f/{aperture}, {shutter_speed}")
            return {
                "iso": iso,
                "aperture": aperture,
                "shutter_speed": shutter_speed,
                "display_shutter": display_shutter
            }
            
        except Exception as e:
            logger.error(f"Error getting settings for EV: {e}")
            return None
    
    def _find_closest_shutter_speed(self, seconds):
        """Find the closest standard shutter speed to the given value in seconds"""
        # Convert all standard shutter speeds to seconds for comparison
        speeds_in_seconds = []
        for speed in self.SHUTTER_SPEEDS:
            if "/" in speed:
                parts = speed.split("/")
                speeds_in_seconds.append(float(parts[0]) / float(parts[1]))
            else:
                speeds_in_seconds.append(float(speed))
        
        # Find the closest value
        closest_idx = min(range(len(speeds_in_seconds)),
                           key=lambda i: abs(speeds_in_seconds[i] - seconds))
        
        return self.SHUTTER_SPEEDS[closest_idx]
    
    def _format_shutter_speed(self, seconds):
        """Format shutter speed in a human-readable way"""
        if seconds >= 60:
            minutes = seconds / 60
            return f"{minutes:.0f} min"
        elif seconds >= 1:
            return f"{seconds:.0f}\""
        else:
            return f"1/{int(1/seconds)}"
    
    def adjust_exposure(self, settings, ev_change, priority="aperture"):
        """
        Adjust exposure settings by a specified EV change
        
        Args:
            settings: Dictionary with current iso, aperture, and shutter_speed
            ev_change: EV change to apply (positive = brighter, negative = darker)
            priority: Which parameter to adjust first ("aperture", "shutter", or "iso")
        
        Returns:
            dict: Dictionary with adjusted iso, aperture, and shutter_speed
        """
        try:
            # Calculate current EV
            current_ev = self.calculate_ev(
                settings["iso"], 
                settings["aperture"], 
                settings["shutter_speed"]
            )
            
            if current_ev is None:
                return None
            
            # Calculate target EV
            target_ev = current_ev - ev_change
            
            # Get settings for target EV
            return self.get_settings_for_ev(
                target_ev, 
                iso=settings["iso"], 
                priority=priority, 
                preferred_aperture=settings["aperture"]
            )
            
        except Exception as e:
            logger.error(f"Error adjusting exposure: {e}")
            return None
    
    def generate_brackets_by_ev(self, base_settings, ev_steps, num_brackets=3, priority="shutter"):
        """
        Generate exposure brackets based on EV steps
        
        Args:
            base_settings: Dictionary with base iso, aperture, and shutter_speed
            ev_steps: EV difference between brackets
            num_brackets: Number of brackets to generate
            priority: Which parameter to adjust first ("aperture", "shutter", or "iso")
        
        Returns:
            list: List of dictionaries with bracket settings
        """
        try:
            brackets = []
            
            # Calculate base EV
            base_ev = self.calculate_ev(
                base_settings["iso"], 
                base_settings["aperture"], 
                base_settings["shutter_speed"]
            )
            
            if base_ev is None:
                return []
            
            # Calculate starting EV (for the darkest bracket)
            if num_brackets % 2 == 1:  # Odd number of brackets
                start_ev = base_ev + (ev_steps * (num_brackets // 2))
                ev_values = [start_ev - (i * ev_steps) for i in range(num_brackets)]
            else:  # Even number of brackets
                start_ev = base_ev + (ev_steps * ((num_brackets - 1) // 2)) + (ev_steps / 2)
                ev_values = [start_ev - (i * ev_steps) for i in range(num_brackets)]
            
            # Generate brackets
            for i, ev in enumerate(ev_values):
                # Get settings for this EV
                bracket_settings = self.get_settings_for_ev(
                    ev, 
                    iso=base_settings["iso"], 
                    priority=priority, 
                    preferred_aperture=base_settings["aperture"]
                )
                
                if bracket_settings:
                    # Add bracket name and EV difference
                    ev_diff = base_ev - ev
                    if ev_diff > 0:
                        name = f"Under {ev_diff:.1f}EV"
                    elif ev_diff < 0:
                        name = f"Over {abs(ev_diff):.1f}EV"
                    else:
                        name = "Base Exposure"
                    
                    bracket_settings["name"] = name
                    bracket_settings["ev_diff"] = ev_diff
                    
                    brackets.append(bracket_settings)
            
            logger.info(f"Generated {len(brackets)} brackets with {ev_steps} EV steps")
            return brackets
            
        except Exception as e:
            logger.error(f"Error generating brackets by EV: {e}")
            return []
    
    def generate_brackets_direct(self, brackets_data):
        """
        Generate exposure brackets based on direct parameter specification
        
        Args:
            brackets_data: List of dictionaries with bracket parameters
        
        Returns:
            list: List of dictionaries with validated bracket settings
        """
        try:
            validated_brackets = []
            
            for bracket in brackets_data:
                # Ensure required fields are present
                if not all(key in bracket for key in ["iso", "aperture", "shutter_speed"]):
                    logger.warning(f"Skipping bracket with missing parameters: {bracket}")
                    continue
                
                # Validate ISO
                if bracket["iso"] not in self.ISO_VALUES_THIRD:
                    # Find closest ISO
                    bracket["iso"] = min(self.ISO_VALUES_THIRD, 
                                         key=lambda x: abs(x - bracket["iso"]))
                
                # Validate aperture
                if bracket["aperture"] not in self.APERTURE_VALUES_THIRD:
                    # Find closest aperture
                    bracket["aperture"] = min(self.APERTURE_VALUES_THIRD, 
                                             key=lambda x: abs(x - bracket["aperture"]))
                
                # Validate shutter speed
                if bracket["shutter_speed"] not in self.SHUTTER_SPEEDS_THIRD:
                    # Try to convert to a standard format
                    try:
                        # If it's a fraction like 1/125
                        if "/" in bracket["shutter_speed"]:
                            parts = bracket["shutter_speed"].split("/")
                            seconds = float(parts[0]) / float(parts[1])
                        else:
                            # If it's a decimal like 0.5
                            seconds = float(bracket["shutter_speed"])
                        
                        # Find closest standard shutter speed
                        bracket["shutter_speed"] = self._find_closest_shutter_speed(seconds)
                    except:
                        logger.warning(f"Invalid shutter speed: {bracket['shutter_speed']}")
                        continue
                
                # Calculate EV for this bracket
                ev = self.calculate_ev(
                    bracket["iso"], 
                    bracket["aperture"], 
                    bracket["shutter_speed"]
                )
                
                if ev is not None:
                    bracket["ev"] = ev
                
                # Add to validated brackets
                validated_brackets.append(bracket)
            
            logger.info(f"Validated {len(validated_brackets)} direct brackets")
            return validated_brackets
            
        except Exception as e:
            logger.error(f"Error generating direct brackets: {e}")
            return []


# Simple test function
def test():
    """Test the exposure calculator"""
    calc = ExposureCalculator()
    
    # Test EV calculation
    settings = {"iso": 100, "aperture": 8.0, "shutter_speed": "1/125"}
    ev = calc.calculate_ev(settings["iso"], settings["aperture"], settings["shutter_speed"])
    print(f"EV for ISO 100, f/8, 1/125: {ev:.2f}")
    
    # Test EV 0 calculations
    ev0_settings = [
        {"iso": 100, "aperture": 1.0, "shutter_speed": "1"},
        {"iso": 100, "aperture": 2.0, "shutter_speed": "4"},
        {"iso": 100, "aperture": 4.0, "shutter_speed": "16"},
        {"iso": 100, "aperture": 8.0, "shutter_speed": "64"},
        {"iso": 100, "aperture": 16.0, "shutter_speed": "256"}
    ]
    
    print("\nTesting EV 0 calculations:")
    for setting in ev0_settings:
        ev = calc.calculate_ev(setting["iso"], setting["aperture"], setting["shutter_speed"])
        print(f"ISO {setting['iso']}, f/{setting['aperture']}, {setting['shutter_speed']}: EV {ev:.2f}")
    
    # Test bracket generation by EV
    brackets = calc.generate_brackets_by_ev(settings, 1.0, 5, "shutter")
    print("\nBrackets by EV:")
    for bracket in brackets:
        print(f"{bracket['name']}: ISO {bracket['iso']}, f/{bracket['aperture']}, {bracket['shutter_speed']}")
    
    # Test long exposure calculations
    print("\nTesting long exposure calculations:")
    long_ev_settings = calc.get_settings_for_ev(0, iso=100, priority="aperture", preferred_aperture=8.0)
    print(f"EV 0, ISO 100, f/8: {long_ev_settings['shutter_speed']} seconds")
    
    long_ev_settings = calc.get_settings_for_ev(0, iso=100, priority="aperture", preferred_aperture=16.0)
    print(f"EV 0, ISO 100, f/16: {long_ev_settings['shutter_speed']} seconds")
    
    # Test direct bracket generation
    direct_brackets = [
        {"name": "Dark", "iso": 100, "aperture": 11.0, "shutter_speed": "1/250", "frames": 10},
        {"name": "Normal", "iso": 100, "aperture": 8.0, "shutter_speed": "1/125", "frames": 10},
        {"name": "Bright", "iso": 100, "aperture": 5.6, "shutter_speed": "1/60", "frames": 10}
    ]
    validated = calc.generate_brackets_direct(direct_brackets)
    print("\nDirect Brackets:")
    for bracket in validated:
        print(f"{bracket['name']}: ISO {bracket['iso']}, f/{bracket['aperture']}, {bracket['shutter_speed']}, EV: {bracket.get('ev', 'N/A'):.2f}")


if __name__ == "__main__":
    test()