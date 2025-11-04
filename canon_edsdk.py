"""
Canon EDSDK Python Wrapper
A ctypes-based wrapper for the Canon EOS Digital SDK (EDSDK)

This module provides Python bindings for the Canon EDSDK DLL,
allowing control of Canon cameras from Python.
"""

import ctypes
from ctypes import *
from ctypes import WINFUNCTYPE  # For Windows stdcall callbacks
from enum import IntEnum
import platform
import os

# Load the EDSDK DLL
if platform.system() == 'Windows':
    try:
        # Try to load from current directory first
        edsdk = ctypes.WinDLL('./EDSDK.dll')
    except OSError:
        # Fall back to system path
        edsdk = ctypes.WinDLL('EDSDK.dll')
else:
    raise OSError("This wrapper currently only supports Windows. For Mac/Linux, use CDLL with appropriate library.")


# =============================================================================
# Basic Type Definitions
# =============================================================================

EdsError = c_uint32
EdsBool = c_int
EdsInt8 = c_char
EdsUInt8 = c_ubyte
EdsInt16 = c_short
EdsUInt16 = c_ushort
EdsInt32 = c_int32
EdsUInt32 = c_uint32
EdsInt64 = c_int64
EdsUInt64 = c_uint64
EdsFloat = c_float
EdsDouble = c_double

# Reference Types (all are pointers to opaque structures)
EdsBaseRef = c_void_p
EdsCameraListRef = c_void_p
EdsCameraRef = c_void_p
EdsVolumeRef = c_void_p
EdsDirectoryItemRef = c_void_p
EdsStreamRef = c_void_p
EdsImageRef = c_void_p
EdsEvfImageRef = c_void_p

EdsPropertyID = EdsUInt32


# =============================================================================
# Error Codes
# =============================================================================

class EdsErrorCodes:
    """Canon SDK Error Codes"""
    EDS_ERR_OK = 0x00000000
    
    # Generic errors
    EDS_ERR_UNIMPLEMENTED = 0x00000001
    EDS_ERR_INTERNAL_ERROR = 0x00000002
    EDS_ERR_MEM_ALLOC_FAILED = 0x00000003
    EDS_ERR_MEM_FREE_FAILED = 0x00000004
    EDS_ERR_OPERATION_CANCELLED = 0x00000005
    EDS_ERR_INCOMPATIBLE_VERSION = 0x00000006
    EDS_ERR_NOT_SUPPORTED = 0x00000007
    EDS_ERR_UNEXPECTED_EXCEPTION = 0x00000008
    EDS_ERR_PROTECTION_VIOLATION = 0x00000009
    EDS_ERR_MISSING_SUBCOMPONENT = 0x0000000A
    EDS_ERR_SELECTION_UNAVAILABLE = 0x0000000B
    
    # File errors
    EDS_ERR_FILE_IO_ERROR = 0x00000020
    EDS_ERR_FILE_NOT_FOUND = 0x00000022
    EDS_ERR_FILE_OPEN_ERROR = 0x00000023
    
    # Device errors
    EDS_ERR_DEVICE_NOT_FOUND = 0x00000080
    EDS_ERR_DEVICE_BUSY = 0x00000081
    EDS_ERR_DEVICE_INVALID = 0x00000082
    EDS_ERR_DEVICE_EMERGENCY = 0x00000083
    EDS_ERR_DEVICE_MEMORY_FULL = 0x00000084
    EDS_ERR_DEVICE_INTERNAL_ERROR = 0x00000085
    
    # Communications errors
    EDS_ERR_COMM_DISCONNECTED = 0x000000C1
    EDS_ERR_COMM_DEVICE_INCOMPATIBLE = 0x000000C2
    
    # Function Parameter errors
    EDS_ERR_INVALID_PARAMETER = 0x00000060
    EDS_ERR_INVALID_HANDLE = 0x00000061
    EDS_ERR_INVALID_POINTER = 0x00000062
    
    # Take picture errors
    EDS_ERR_TAKE_PICTURE_AF_NG = 0x00008D01
    EDS_ERR_TAKE_PICTURE_NO_CARD_NG = 0x00008D06
    EDS_ERR_TAKE_PICTURE_CARD_NG = 0x00008D07

    @staticmethod
    def get_error_name(error_code):
        """Get the name of an error code"""
        for name, value in vars(EdsErrorCodes).items():
            if not name.startswith('_') and value == error_code:
                return name
        return f"UNKNOWN_ERROR_0x{error_code:08X}"


# =============================================================================
# Enumerations
# =============================================================================

class EdsDataType(IntEnum):
    """Data types for properties"""
    Unknown = 0
    Bool = 1
    String = 2
    Int8 = 3
    UInt8 = 6
    Int16 = 4
    UInt16 = 7
    Int32 = 8
    UInt32 = 9
    Int64 = 10
    UInt64 = 11
    Float = 12
    Double = 13
    ByteBlock = 14
    Rational = 20
    Point = 21
    Rect = 22
    Time = 23


class EdsPropertyID_:
    """Property IDs for camera settings"""
    # Camera Setting Properties
    ProductName = 0x00000002
    OwnerName = 0x00000004
    MakerName = 0x00000005
    DateTime = 0x00000006
    FirmwareVersion = 0x00000007
    BatteryLevel = 0x00000008
    SaveTo = 0x0000000b
    
    # Image Properties
    ImageQuality = 0x00000100
    Orientation = 0x00000102
    
    # Capture Properties
    AEMode = 0x00000400
    DriveMode = 0x00000401
    ISOSpeed = 0x00000402
    MeteringMode = 0x00000403
    AFMode = 0x00000404
    Av = 0x00000405  # Aperture
    Tv = 0x00000406  # Shutter Speed
    ExposureCompensation = 0x00000407
    AvailableShots = 0x0000040a
    
    # EVF Properties
    Evf_OutputDevice = 0x00000500
    Evf_Mode = 0x00000501
    Evf_WhiteBalance = 0x00000502
    Evf_Zoom = 0x00000507


class EdsSaveTo(IntEnum):
    """Save destination for captured images"""
    Camera = 1
    Host = 2
    Both = Camera | Host


class EdsFileCreateDisposition(IntEnum):
    """File creation disposition"""
    CreateNew = 1
    CreateAlways = 2
    OpenExisting = 3
    OpenAlways = 4
    TruncateExisting = 5


class EdsAccess(IntEnum):
    """File access modes"""
    Read = 0
    Write = 1
    ReadWrite = 2
    Error = 0xFFFFFFFF


class EdsCameraCommand(IntEnum):
    """Camera commands"""
    TakePicture = 0x00000000
    ExtendShutDownTimer = 0x00000001
    BulbStart = 0x00000002
    BulbEnd = 0x00000003
    DoEvfAf = 0x00000102
    DriveLensEvf = 0x00000103
    DoClickWBEvf = 0x00000104


class EdsEvfOutputDevice(IntEnum):
    """EVF (Live View) output device"""
    TFT = 1
    PC = 2
    TFT_AND_PC = 3


class EdsObjectEvent(IntEnum):
    """Object event types"""
    All = 0x00000200
    VolumeInfoChanged = 0x00000201
    VolumeUpdateItems = 0x00000202
    FolderUpdateItems = 0x00000203
    DirItemCreated = 0x00000204
    DirItemRemoved = 0x00000205
    DirItemInfoChanged = 0x00000206
    DirItemContentChanged = 0x00000207
    DirItemRequestTransfer = 0x00000208  # This is the download event!
    DirItemRequestTransferDT = 0x00000209
    DirItemCancelTransferDT = 0x0000020a
    VolumeAdded = 0x0000020c
    VolumeRemoved = 0x0000020d


class EdsPropertyEvent(IntEnum):
    """Property event types"""
    All = 0x00000100
    PropertyChanged = 0x00000101
    PropertyDescChanged = 0x00000102


class EdsStateEvent(IntEnum):
    """State event types"""
    All = 0x00000300
    Shutdown = 0x00000301
    JobStatusChanged = 0x00000302
    WillSoonShutDown = 0x00000303
    ShutDownTimerUpdate = 0x00000304
    CaptureError = 0x00000305
    InternalError = 0x00000306
    AfResult = 0x00000309
    BulbExposureTime = 0x00000310


# =============================================================================
# Structures
# =============================================================================

class EdsPoint(Structure):
    """Point structure"""
    _fields_ = [
        ('x', EdsInt32),
        ('y', EdsInt32)
    ]


class EdsSize(Structure):
    """Size structure"""
    _fields_ = [
        ('width', EdsInt32),
        ('height', EdsInt32)
    ]


class EdsRect(Structure):
    """Rectangle structure"""
    _fields_ = [
        ('point', EdsPoint),
        ('size', EdsSize)
    ]


class EdsTime(Structure):
    """Time structure"""
    _fields_ = [
        ('year', EdsUInt32),
        ('month', EdsUInt32),
        ('day', EdsUInt32),
        ('hour', EdsUInt32),
        ('minute', EdsUInt32),
        ('second', EdsUInt32),
        ('milliseconds', EdsUInt32)
    ]


class EdsDeviceInfo(Structure):
    """Device information structure"""
    _fields_ = [
        ('szPortName', c_char * 256),
        ('szDeviceDescription', c_char * 256),
        ('deviceSubType', EdsUInt32),
        ('reserved', EdsUInt32)
    ]


class EdsVolumeInfo(Structure):
    """Volume information structure"""
    _fields_ = [
        ('storageType', EdsUInt32),
        ('access', EdsUInt32),
        ('maxCapacity', EdsUInt64),
        ('freeSpaceInBytes', EdsUInt64),
        ('szVolumeLabel', c_char * 256)
    ]


class EdsDirectoryItemInfo(Structure):
    """Directory item information structure"""
    _fields_ = [
        ('size', EdsUInt64),
        ('isFolder', EdsBool),
        ('groupID', EdsUInt32),
        ('option', EdsUInt32),
        ('szFileName', c_char * 256),
        ('format', EdsUInt32),
        ('dateTime', EdsUInt32)
    ]


class EdsCapacity(Structure):
    """Capacity structure"""
    _fields_ = [
        ('numberOfFreeClusters', EdsInt32),
        ('bytesPerSector', EdsInt32),
        ('reset', EdsBool)
    ]


class EdsPropertyDesc(Structure):
    """Property description structure"""
    _fields_ = [
        ('form', EdsInt32),
        ('access', EdsInt32),
        ('numElements', EdsInt32),
        ('propDesc', EdsInt32 * 128)
    ]


# =============================================================================
# Callback Function Types
# =============================================================================

# CRITICAL: Canon SDK uses __stdcall convention on Windows
# Must use WINFUNCTYPE (not CFUNCTYPE) to match the calling convention
if platform.system() == 'Windows':
    # Windows: Use WINFUNCTYPE for __stdcall convention
    EdsProgressCallback = WINFUNCTYPE(EdsError, EdsUInt32, c_void_p, POINTER(EdsBool))
    EdsCameraAddedHandler = WINFUNCTYPE(EdsError, c_void_p)
    EdsPropertyEventHandler = WINFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, EdsUInt32, c_void_p)
    EdsObjectEventHandler = WINFUNCTYPE(EdsError, EdsUInt32, EdsBaseRef, c_void_p)
    EdsStateEventHandler = WINFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, c_void_p)
else:
    # Other platforms: Use CFUNCTYPE
    EdsProgressCallback = CFUNCTYPE(EdsError, EdsUInt32, c_void_p, POINTER(EdsBool))
    EdsCameraAddedHandler = CFUNCTYPE(EdsError, c_void_p)
    EdsPropertyEventHandler = CFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, EdsUInt32, c_void_p)
    EdsObjectEventHandler = CFUNCTYPE(EdsError, EdsUInt32, EdsBaseRef, c_void_p)
    EdsStateEventHandler = CFUNCTYPE(EdsError, EdsUInt32, EdsUInt32, c_void_p)


# =============================================================================
# SDK Function Definitions
# =============================================================================

# Basic Functions
EdsInitializeSDK = edsdk.EdsInitializeSDK
EdsInitializeSDK.argtypes = []
EdsInitializeSDK.restype = EdsError

EdsTerminateSDK = edsdk.EdsTerminateSDK
EdsTerminateSDK.argtypes = []
EdsTerminateSDK.restype = EdsError

# Reference Counter Functions
EdsRetain = edsdk.EdsRetain
EdsRetain.argtypes = [EdsBaseRef]
EdsRetain.restype = EdsUInt32

EdsRelease = edsdk.EdsRelease
EdsRelease.argtypes = [EdsBaseRef]
EdsRelease.restype = EdsUInt32

# Item-tree Functions
EdsGetChildCount = edsdk.EdsGetChildCount
EdsGetChildCount.argtypes = [EdsBaseRef, POINTER(EdsUInt32)]
EdsGetChildCount.restype = EdsError

EdsGetChildAtIndex = edsdk.EdsGetChildAtIndex
EdsGetChildAtIndex.argtypes = [EdsBaseRef, EdsInt32, POINTER(EdsBaseRef)]
EdsGetChildAtIndex.restype = EdsError

EdsGetParent = edsdk.EdsGetParent
EdsGetParent.argtypes = [EdsBaseRef, POINTER(EdsBaseRef)]
EdsGetParent.restype = EdsError

# Property Functions
EdsGetPropertySize = edsdk.EdsGetPropertySize
EdsGetPropertySize.argtypes = [EdsBaseRef, EdsPropertyID, EdsInt32, 
                                POINTER(EdsUInt32), POINTER(EdsInt32)]
EdsGetPropertySize.restype = EdsError

EdsGetPropertyData = edsdk.EdsGetPropertyData
EdsGetPropertyData.argtypes = [EdsBaseRef, EdsPropertyID, EdsInt32, 
                                EdsInt32, c_void_p]
EdsGetPropertyData.restype = EdsError

EdsSetPropertyData = edsdk.EdsSetPropertyData
EdsSetPropertyData.argtypes = [EdsBaseRef, EdsPropertyID, EdsInt32, 
                                EdsInt32, c_void_p]
EdsSetPropertyData.restype = EdsError

EdsGetPropertyDesc = edsdk.EdsGetPropertyDesc
EdsGetPropertyDesc.argtypes = [EdsBaseRef, EdsPropertyID, POINTER(EdsPropertyDesc)]
EdsGetPropertyDesc.restype = EdsError

# Camera List and Device Functions
EdsGetCameraList = edsdk.EdsGetCameraList
EdsGetCameraList.argtypes = [POINTER(EdsCameraListRef)]
EdsGetCameraList.restype = EdsError

EdsGetDeviceInfo = edsdk.EdsGetDeviceInfo
EdsGetDeviceInfo.argtypes = [EdsCameraRef, POINTER(EdsDeviceInfo)]
EdsGetDeviceInfo.restype = EdsError

# Session Functions
EdsOpenSession = edsdk.EdsOpenSession
EdsOpenSession.argtypes = [EdsCameraRef]
EdsOpenSession.restype = EdsError

EdsCloseSession = edsdk.EdsCloseSession
EdsCloseSession.argtypes = [EdsCameraRef]
EdsCloseSession.restype = EdsError

# Command Functions
EdsSendCommand = edsdk.EdsSendCommand
EdsSendCommand.argtypes = [EdsCameraRef, EdsUInt32, EdsInt32]
EdsSendCommand.restype = EdsError

EdsSendStatusCommand = edsdk.EdsSendStatusCommand
EdsSendStatusCommand.argtypes = [EdsCameraRef, EdsUInt32, EdsInt32]
EdsSendStatusCommand.restype = EdsError

EdsSetCapacity = edsdk.EdsSetCapacity
EdsSetCapacity.argtypes = [EdsCameraRef, EdsCapacity]
EdsSetCapacity.restype = EdsError

# Volume Functions
EdsGetVolumeInfo = edsdk.EdsGetVolumeInfo
EdsGetVolumeInfo.argtypes = [EdsVolumeRef, POINTER(EdsVolumeInfo)]
EdsGetVolumeInfo.restype = EdsError

# Directory Item Functions
EdsGetDirectoryItemInfo = edsdk.EdsGetDirectoryItemInfo
EdsGetDirectoryItemInfo.argtypes = [EdsDirectoryItemRef, POINTER(EdsDirectoryItemInfo)]
EdsGetDirectoryItemInfo.restype = EdsError

EdsDeleteDirectoryItem = edsdk.EdsDeleteDirectoryItem
EdsDeleteDirectoryItem.argtypes = [EdsDirectoryItemRef]
EdsDeleteDirectoryItem.restype = EdsError

# Download Functions
EdsDownload = edsdk.EdsDownload
EdsDownload.argtypes = [EdsDirectoryItemRef, EdsUInt64, EdsStreamRef]
EdsDownload.restype = EdsError

EdsDownloadComplete = edsdk.EdsDownloadComplete
EdsDownloadComplete.argtypes = [EdsDirectoryItemRef]
EdsDownloadComplete.restype = EdsError

EdsDownloadCancel = edsdk.EdsDownloadCancel
EdsDownloadCancel.argtypes = [EdsDirectoryItemRef]
EdsDownloadCancel.restype = EdsError

# Stream Functions
EdsCreateFileStream = edsdk.EdsCreateFileStream
EdsCreateFileStream.argtypes = [c_char_p, EdsUInt32, EdsUInt32, POINTER(EdsStreamRef)]
EdsCreateFileStream.restype = EdsError

# Unicode version for Windows (handles long paths and Unicode filenames better)
EdsCreateFileStreamEx = edsdk.EdsCreateFileStreamEx
EdsCreateFileStreamEx.argtypes = [c_wchar_p, EdsUInt32, EdsUInt32, POINTER(EdsStreamRef)]
EdsCreateFileStreamEx.restype = EdsError

EdsCreateMemoryStream = edsdk.EdsCreateMemoryStream
EdsCreateMemoryStream.argtypes = [EdsUInt64, POINTER(EdsStreamRef)]
EdsCreateMemoryStream.restype = EdsError

EdsGetPointer = edsdk.EdsGetPointer
EdsGetPointer.argtypes = [EdsStreamRef, POINTER(c_void_p)]
EdsGetPointer.restype = EdsError

EdsGetLength = edsdk.EdsGetLength
EdsGetLength.argtypes = [EdsStreamRef, POINTER(EdsUInt64)]
EdsGetLength.restype = EdsError

# Event Handler Functions
EdsSetCameraAddedHandler = edsdk.EdsSetCameraAddedHandler
EdsSetCameraAddedHandler.argtypes = [EdsCameraAddedHandler, c_void_p]
EdsSetCameraAddedHandler.restype = EdsError

EdsSetPropertyEventHandler = edsdk.EdsSetPropertyEventHandler
EdsSetPropertyEventHandler.argtypes = [EdsCameraRef, EdsUInt32, 
                                        EdsPropertyEventHandler, c_void_p]
EdsSetPropertyEventHandler.restype = EdsError

EdsSetObjectEventHandler = edsdk.EdsSetObjectEventHandler
EdsSetObjectEventHandler.argtypes = [EdsCameraRef, EdsUInt32, 
                                      EdsObjectEventHandler, c_void_p]
EdsSetObjectEventHandler.restype = EdsError

EdsSetCameraStateEventHandler = edsdk.EdsSetCameraStateEventHandler
EdsSetCameraStateEventHandler.argtypes = [EdsCameraRef, EdsUInt32, 
                                           EdsStateEventHandler, c_void_p]
EdsSetCameraStateEventHandler.restype = EdsError

EdsGetEvent = edsdk.EdsGetEvent
EdsGetEvent.argtypes = []
EdsGetEvent.restype = EdsError

# EVF (Live View) Functions
EdsCreateEvfImageRef = edsdk.EdsCreateEvfImageRef
EdsCreateEvfImageRef.argtypes = [EdsStreamRef, POINTER(EdsEvfImageRef)]
EdsCreateEvfImageRef.restype = EdsError

EdsDownloadEvfImage = edsdk.EdsDownloadEvfImage
EdsDownloadEvfImage.argtypes = [EdsCameraRef, EdsEvfImageRef]
EdsDownloadEvfImage.restype = EdsError


# =============================================================================
# Helper Functions
# =============================================================================

def check_error(err, func_name=""):
    """Check error code and raise exception if not OK"""
    if err != EdsErrorCodes.EDS_ERR_OK:
        error_name = EdsErrorCodes.get_error_name(err)
        if func_name:
            raise RuntimeError(f"{func_name} failed: {error_name} (0x{err:08X})")
        else:
            raise RuntimeError(f"SDK Error: {error_name} (0x{err:08X})")


def get_property_uint32(camera_ref, property_id, param=0):
    """Helper to get a UInt32 property"""
    value = EdsUInt32()
    err = EdsGetPropertyData(camera_ref, property_id, param, sizeof(value), byref(value))
    check_error(err, "EdsGetPropertyData")
    return value.value


def get_property_string(camera_ref, property_id, param=0, max_len=256):
    """Helper to get a string property"""
    buffer = create_string_buffer(max_len)
    err = EdsGetPropertyData(camera_ref, property_id, param, max_len, buffer)
    check_error(err, "EdsGetPropertyData")
    return buffer.value.decode('utf-8', errors='ignore')


def set_property_uint32(camera_ref, property_id, value, param=0):
    """Helper to set a UInt32 property"""
    data = EdsUInt32(value)
    err = EdsSetPropertyData(camera_ref, property_id, param, sizeof(data), byref(data))
    check_error(err, "EdsSetPropertyData")


# =============================================================================
# High-Level Wrapper Class
# =============================================================================

class CanonCamera:
    """High-level wrapper class for Canon camera operations"""
    
    def __init__(self):
        self.camera_ref = None
        self.camera_list = None
        self._object_event_handler = None
        self._property_event_handler = None
        self._state_event_handler = None
        
    def initialize_sdk(self):
        """Initialize the Canon SDK"""
        err = EdsInitializeSDK()
        check_error(err, "EdsInitializeSDK")
        
    def terminate_sdk(self):
        """Terminate the Canon SDK"""
        if self.camera_ref:
            self.close_session()
        if self.camera_list:
            EdsRelease(self.camera_list)
            self.camera_list = None
        err = EdsTerminateSDK()
        check_error(err, "EdsTerminateSDK")
    
    def get_camera_list(self):
        """Get list of available cameras"""
        camera_list = EdsCameraListRef()
        err = EdsGetCameraList(byref(camera_list))
        check_error(err, "EdsGetCameraList")
        self.camera_list = camera_list
        
        # Get camera count
        count = EdsUInt32()
        err = EdsGetChildCount(camera_list, byref(count))
        check_error(err, "EdsGetChildCount")
        
        return count.value
    
    def get_camera(self, index=0):
        """Get camera reference at the specified index"""
        if not self.camera_list:
            raise RuntimeError("Camera list not initialized. Call get_camera_list() first.")
        
        camera = EdsCameraRef()
        err = EdsGetChildAtIndex(self.camera_list, index, byref(camera))
        check_error(err, "EdsGetChildAtIndex")
        self.camera_ref = camera
        
        return camera
    
    def get_device_info(self):
        """Get device information for the current camera"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected. Call get_camera() first.")
        
        device_info = EdsDeviceInfo()
        err = EdsGetDeviceInfo(self.camera_ref, byref(device_info))
        check_error(err, "EdsGetDeviceInfo")
        
        return {
            'port': device_info.szPortName.decode('utf-8', errors='ignore'),
            'description': device_info.szDeviceDescription.decode('utf-8', errors='ignore'),
            'subtype': device_info.deviceSubType
        }
    
    def open_session(self):
        """Open a session with the camera"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected. Call get_camera() first.")
        
        err = EdsOpenSession(self.camera_ref)
        check_error(err, "EdsOpenSession")
    
    def close_session(self):
        """Close the session with the camera"""
        if self.camera_ref:
            try:
                err = EdsCloseSession(self.camera_ref)
                # Only check error if it's not already released/shutdown
                if err != EdsErrorCodes.EDS_ERR_OK:
                    # Ignore errors if camera already shut down
                    pass
            except OSError:
                # Handle access violations from already-closed sessions
                pass
            finally:
                try:
                    EdsRelease(self.camera_ref)
                except:
                    pass
                self.camera_ref = None
    
    def take_picture(self, retries=3, retry_delay=1.0):
        """
        Take a picture with automatic retry on common errors
        
        Args:
            retries: Number of retry attempts for recoverable errors
            retry_delay: Delay between retries in seconds
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected and session not opened.")
        
        import time
        
        for attempt in range(retries + 1):
            try:
                err = EdsSendCommand(self.camera_ref, EdsCameraCommand.TakePicture, 0)
                check_error(err, "EdsSendCommand(TakePicture)")
                return  # Success!
                
            except RuntimeError as e:
                error_str = str(e)
                
                # Check for recoverable errors
                if "DEVICE_BUSY" in error_str and attempt < retries:
                    print(f"   Camera busy, retrying in {retry_delay}s... (attempt {attempt+1}/{retries})")
                    time.sleep(retry_delay)
                    continue
                    
                elif "AF_NG" in error_str and attempt < retries:
                    print(f"   Autofocus failed, retrying in {retry_delay}s... (attempt {attempt+1}/{retries})")
                    time.sleep(retry_delay)
                    continue
                
                # Non-recoverable or out of retries
                raise
    
    def get_property(self, property_id, as_string=False):
        """Get a camera property"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        if as_string:
            return get_property_string(self.camera_ref, property_id)
        else:
            return get_property_uint32(self.camera_ref, property_id)
    
    def set_property(self, property_id, value):
        """Set a camera property"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        set_property_uint32(self.camera_ref, property_id, value)
    
    def set_save_to(self, destination):
        """Set where to save captured images (Camera, Host, or Both)"""
        self.set_property(EdsPropertyID_.SaveTo, destination)
    
    def set_capacity(self, free_clusters, bytes_per_sector, reset=True):
        """Set the capacity information for the host computer"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        capacity = EdsCapacity()
        capacity.numberOfFreeClusters = free_clusters
        capacity.bytesPerSector = bytes_per_sector
        capacity.reset = 1 if reset else 0
        
        err = EdsSetCapacity(self.camera_ref, capacity)
        check_error(err, "EdsSetCapacity")
    
    # =============================================================================
    # Download Helper Methods
    # =============================================================================
    
    def download_file(self, directory_item_ref, save_path):
        """
        Download a file from camera to specified path
        
        Args:
            directory_item_ref: EdsDirectoryItemRef from download event
            save_path: Full path where file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        import os
        
        try:
            # Get file info
            info = EdsDirectoryItemInfo()
            err = EdsGetDirectoryItemInfo(directory_item_ref, byref(info))
            if err != EdsErrorCodes.EDS_ERR_OK:
                return False
            
            # Ensure absolute path
            save_path = os.path.abspath(save_path)
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(save_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # CRITICAL: Create empty file first - SDK requires file to exist!
            with open(save_path, 'wb') as f:
                pass  # Create empty file
            
            # Create file stream
            stream = EdsStreamRef()
            err = EdsCreateFileStream(
                save_path.encode('utf-8'),
                EdsFileCreateDisposition.CreateAlways,
                EdsAccess.Write,
                byref(stream)
            )
            
            if err != EdsErrorCodes.EDS_ERR_OK:
                return False
            
            # Download the file
            err = EdsDownload(directory_item_ref, info.size, stream)
            
            if err != EdsErrorCodes.EDS_ERR_OK:
                EdsRelease(stream)
                return False
            
            # Complete download
            err = EdsDownloadComplete(directory_item_ref)
            
            # Release stream
            EdsRelease(stream)
            
            return err == EdsErrorCodes.EDS_ERR_OK
            
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def setup_download_handler(self, callback, save_directory=None):
        """
        Setup automatic download handler for captured images
        
        Args:
            callback: Optional callback function(filename, save_path) called after download
            save_directory: Directory to save files (default: current directory)
            
        Returns:
            The event handler function (keep reference to prevent garbage collection)
        """
        import os
        
        if save_directory is None:
            save_directory = os.getcwd()
        
        downloaded_files = []
        
        def handler(event, obj_ref, context):
            try:
                if event == EdsObjectEvent.DirItemRequestTransfer and obj_ref:
                    # Get file info
                    info = EdsDirectoryItemInfo()
                    err = EdsGetDirectoryItemInfo(obj_ref, byref(info))
                    
                    if err == EdsErrorCodes.EDS_ERR_OK:
                        filename = info.szFileName.decode('utf-8', errors='ignore')
                        save_path = os.path.join(save_directory, filename)
                        
                        # Download the file
                        if self.download_file(obj_ref, save_path):
                            downloaded_files.append(save_path)
                            if callback:
                                callback(filename, save_path)
                
                # Always release object reference
                if obj_ref:
                    try:
                        EdsRelease(obj_ref)
                    except:
                        pass
                        
            except Exception as e:
                print(f"Handler error: {e}")
            
            return EdsErrorCodes.EDS_ERR_OK
        
        # Create callback and register
        self._object_event_handler = EdsObjectEventHandler(handler)
        err = EdsSetObjectEventHandler(
            self.camera_ref,
            EdsObjectEvent.All,
            self._object_event_handler,
            None
        )
        check_error(err, "EdsSetObjectEventHandler")
        
        return self._object_event_handler
    
    # =============================================================================
    # Live View Methods
    # =============================================================================
    
    def start_live_view(self):
        """Start Live View (EVF) on PC"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        # Set EVF output to PC
        self.set_property(EdsPropertyID_.Evf_OutputDevice, EdsEvfOutputDevice.PC)
    
    def stop_live_view(self):
        """Stop Live View (EVF)"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        # Set EVF output to camera TFT (off PC)
        try:
            self.set_property(EdsPropertyID_.Evf_OutputDevice, EdsEvfOutputDevice.TFT)
        except:
            pass  # Ignore errors if camera disconnected
    
    def get_live_view_image(self):
        """
        Capture current Live View image
        
        Returns:
            bytes: JPEG image data, or None if failed
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        # Create memory stream
        stream = EdsStreamRef()
        err = EdsCreateMemoryStream(0, byref(stream))
        if err != EdsErrorCodes.EDS_ERR_OK:
            return None
        
        # Create EVF image reference
        evf_image = EdsEvfImageRef()
        err = EdsCreateEvfImageRef(stream, byref(evf_image))
        if err != EdsErrorCodes.EDS_ERR_OK:
            EdsRelease(stream)
            return None
        
        # Download EVF image
        err = EdsDownloadEvfImage(self.camera_ref, evf_image)
        if err != EdsErrorCodes.EDS_ERR_OK:
            EdsRelease(evf_image)
            EdsRelease(stream)
            return None
        
        # Get image data from stream
        length = EdsUInt64()
        err = EdsGetLength(stream, byref(length))
        if err != EdsErrorCodes.EDS_ERR_OK:
            EdsRelease(evf_image)
            EdsRelease(stream)
            return None
        
        # Get pointer to data
        data_ptr = c_void_p()
        err = EdsGetPointer(stream, byref(data_ptr))
        if err != EdsErrorCodes.EDS_ERR_OK:
            EdsRelease(evf_image)
            EdsRelease(stream)
            return None
        
        # Copy data to Python bytes
        image_data = (c_ubyte * length.value).from_address(data_ptr.value)
        result = bytes(image_data)
        
        # Cleanup
        EdsRelease(evf_image)
        EdsRelease(stream)
        
        return result
    
    # =============================================================================
    # Focus Control Methods
    # =============================================================================
    
    def focus_near(self, speed=3):
        """
        Move focus closer (speed: 1=slow, 2=medium, 3=fast)
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.DriveLensEvf, speed)
        check_error(err, "DriveLensEvf(Near)")
    
    def focus_far(self, speed=3):
        """
        Move focus farther (speed: 1=slow, 2=medium, 3=fast)
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.DriveLensEvf, speed + 0x8000)
        check_error(err, "DriveLensEvf(Far)")
    
    def autofocus(self):
        """Trigger autofocus in Live View mode"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.DoEvfAf, 0)
        check_error(err, "DoEvfAf")
    
    # =============================================================================
    # Bulb Mode Methods
    # =============================================================================
    
    def bulb_start(self):
        """Start bulb exposure"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.BulbStart, 0)
        check_error(err, "BulbStart")
    
    def bulb_end(self):
        """End bulb exposure"""
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.BulbEnd, 0)
        check_error(err, "BulbEnd")
    
    def bulb_exposure(self, duration_seconds):
        """
        Take a bulb exposure for specified duration
        
        Args:
            duration_seconds: Exposure time in seconds
        """
        import time
        self.bulb_start()
        time.sleep(duration_seconds)
        self.bulb_end()
    
    # =============================================================================
    # Information Methods
    # =============================================================================
    
    def get_battery_level(self):
        """
        Get camera battery level
        
        Returns:
            int: Battery level (0-100), or None if unavailable
        """
        try:
            level = self.get_property(EdsPropertyID_.BatteryLevel)
            return level
        except:
            return None
    
    def get_available_shots(self):
        """
        Get number of available shots remaining
        
        Returns:
            int: Number of shots, or None if unavailable
        """
        try:
            shots = self.get_property(EdsPropertyID_.AvailableShots)
            return shots
        except:
            return None
    
    def get_firmware_version(self):
        """Get camera firmware version"""
        try:
            return self.get_property(EdsPropertyID_.FirmwareVersion, as_string=True)
        except:
            return "Unknown"
    
    def get_product_name(self):
        """Get camera product name"""
        try:
            return self.get_property(EdsPropertyID_.ProductName, as_string=True)
        except:
            return "Unknown"
    
    # =============================================================================
    # Camera Settings Helpers
    # =============================================================================
    
    def get_iso(self):
        """Get current ISO setting"""
        try:
            return self.get_property(EdsPropertyID_.ISOSpeed)
        except:
            return None
    
    def set_iso(self, iso_value):
        """
        Set ISO value
        
        Args:
            iso_value: ISO value (e.g., 100, 200, 400, etc.)
                      Use specific Canon ISO constants for exact values
        """
        self.set_property(EdsPropertyID_.ISOSpeed, iso_value)
    
    def get_aperture(self):
        """Get current aperture setting"""
        try:
            return self.get_property(EdsPropertyID_.Av)
        except:
            return None
    
    def set_aperture(self, av_value):
        """
        Set aperture value
        
        Args:
            av_value: Canon aperture constant (see SDK documentation)
        """
        self.set_property(EdsPropertyID_.Av, av_value)
    
    def get_shutter_speed(self):
        """Get current shutter speed setting"""
        try:
            return self.get_property(EdsPropertyID_.Tv)
        except:
            return None
    
    def set_shutter_speed(self, tv_value):
        """
        Set shutter speed
        
        Args:
            tv_value: Canon shutter speed constant (see SDK documentation)
        """
        self.set_property(EdsPropertyID_.Tv, tv_value)
    
    # =============================================================================
    # Quick-Set Helper Methods (Human-Readable Values)
    # =============================================================================
    
    # ISO value mappings (reverse lookup from human-readable to hex)
    _ISO_VALUES = {
        6: 0x00000028,
        12: 0x00000030,
        25: 0x00000038,
        50: 0x00000040,
        100: 0x00000048,
        125: 0x0000004b,
        160: 0x0000004d,
        200: 0x00000050,
        250: 0x00000053,
        320: 0x00000055,
        400: 0x00000058,
        500: 0x0000005b,
        640: 0x0000005d,
        800: 0x00000060,
        1000: 0x00000063,
        1250: 0x00000065,
        1600: 0x00000068,
        2000: 0x0000006b,
        2500: 0x0000006d,
        3200: 0x00000070,
        4000: 0x00000073,
        5000: 0x00000075,
        6400: 0x00000078,
        8000: 0x0000007b,
        10000: 0x0000007d,
        12800: 0x00000080,
        16000: 0x00000083,
        20000: 0x00000085,
        25600: 0x00000088,
        32000: 0x0000008b,
        40000: 0x0000008d,
        51200: 0x00000090,
        102400: 0x00000098,
    }
    
    # Aperture value mappings (reverse lookup from f-stop to hex)
    _APERTURE_VALUES = {
        1.0: 0x00000008,
        1.1: 0x0000000B,
        1.2: 0x0000000C,
        1.4: 0x00000010,
        1.6: 0x00000013,
        1.8: 0x00000014,
        2.0: 0x00000018,
        2.2: 0x0000001B,
        2.5: 0x0000001C,
        2.8: 0x00000020,
        3.2: 0x00000023,
        3.5: 0x00000024,
        4.0: 0x00000028,
        4.5: 0x0000002B,
        5.0: 0x0000002D,
        5.6: 0x00000030,
        6.3: 0x00000033,
        6.7: 0x00000034,
        7.1: 0x00000035,
        8.0: 0x00000038,
        9.0: 0x0000003B,
        9.5: 0x0000003C,
        10: 0x0000003D,
        11: 0x00000040,
        13: 0x00000043,
        14: 0x00000045,
        16: 0x00000048,
        18: 0x0000004B,
        19: 0x0000004C,
        20: 0x0000004D,
        22: 0x00000050,
        25: 0x00000053,
        27: 0x00000054,
        29: 0x00000055,
        32: 0x00000058,
    }
    
    # Shutter speed value mappings (reverse lookup from string to hex)
    _SHUTTER_VALUES = {
        'bulb': 0x0000000C,
        '30': 0x00000010,
        '25': 0x00000013,
        '20': 0x00000014,
        '15': 0x00000018,
        '13': 0x0000001B,
        '10': 0x0000001C,
        '8': 0x00000020,
        '6': 0x00000023,
        '5': 0x00000025,
        '4': 0x00000028,
        '3.2': 0x0000002B,
        '3': 0x0000002C,
        '2.5': 0x0000002D,
        '2': 0x00000030,
        '1.6': 0x00000033,
        '1.5': 0x00000034,
        '1.3': 0x00000035,
        '1': 0x00000038,
        '0.8': 0x0000003B,
        '0.7': 0x0000003C,
        '0.6': 0x0000003D,
        '0.5': 0x00000040,
        '0.4': 0x00000043,
        '0.3': 0x00000044,
        '1/4': 0x00000048,
        '1/5': 0x0000004B,
        '1/6': 0x0000004C,
        '1/8': 0x00000050,
        '1/10': 0x00000053,
        '1/13': 0x00000055,
        '1/15': 0x00000058,
        '1/20': 0x0000005B,
        '1/25': 0x0000005D,
        '1/30': 0x00000060,
        '1/40': 0x00000063,
        '1/45': 0x00000064,
        '1/50': 0x00000065,
        '1/60': 0x00000068,
        '1/80': 0x0000006B,
        '1/90': 0x0000006C,
        '1/100': 0x0000006D,
        '1/125': 0x00000070,
        '1/160': 0x00000073,
        '1/180': 0x00000074,
        '1/200': 0x00000075,
        '1/250': 0x00000078,
        '1/320': 0x0000007B,
        '1/350': 0x0000007C,
        '1/400': 0x0000007D,
        '1/500': 0x00000080,
        '1/640': 0x00000083,
        '1/750': 0x00000084,
        '1/800': 0x00000085,
        '1/1000': 0x00000088,
        '1/1250': 0x0000008B,
        '1/1500': 0x0000008C,
        '1/1600': 0x0000008D,
        '1/2000': 0x00000090,
        '1/2500': 0x00000093,
        '1/3000': 0x00000094,
        '1/3200': 0x00000095,
        '1/4000': 0x00000098,
        '1/5000': 0x0000009B,
        '1/6000': 0x0000009C,
        '1/6400': 0x0000009D,
        '1/8000': 0x000000A0,
    }
    
    def set_iso_quick(self, iso_value):
        """
        Set ISO using a simple numeric value
        
        Args:
            iso_value: ISO number (e.g., 100, 200, 400, 800, 1600, 3200, 6400)
        
        Example:
            camera.set_iso_quick(400)  # Set to ISO 400
            camera.set_iso_quick(1600)  # Set to ISO 1600
        
        Raises:
            ValueError: If the ISO value is not supported
        """
        if iso_value not in self._ISO_VALUES:
            # Try to find closest value
            available = sorted(self._ISO_VALUES.keys())
            closest = min(available, key=lambda x: abs(x - iso_value))
            raise ValueError(
                f"ISO {iso_value} not directly supported. "
                f"Available values: {available}. "
                f"Closest match: ISO {closest}. "
                f"Use camera.set_iso_quick({closest}) instead."
            )
        
        hex_value = self._ISO_VALUES[iso_value]
        self.set_iso(hex_value)
    
    def set_aperture_quick(self, f_stop):
        """
        Set aperture using f-stop value
        
        Args:
            f_stop: Aperture f-stop (e.g., 1.4, 2.8, 4.0, 5.6, 8.0, 11, 16, 22)
        
        Example:
            camera.set_aperture_quick(2.8)  # Set to f/2.8
            camera.set_aperture_quick(5.6)  # Set to f/5.6
        
        Raises:
            ValueError: If the aperture value is not supported
        
        Note:
            Available apertures depend on the attached lens. Camera must typically
            be in Manual (M) or Aperture Priority (Av) mode.
        """
        if f_stop not in self._APERTURE_VALUES:
            # Try to find closest value
            available = sorted(self._APERTURE_VALUES.keys())
            closest = min(available, key=lambda x: abs(x - f_stop))
            raise ValueError(
                f"f/{f_stop} not directly supported. "
                f"Available values: {available}. "
                f"Closest match: f/{closest}. "
                f"Use camera.set_aperture_quick({closest}) instead."
            )
        
        hex_value = self._APERTURE_VALUES[f_stop]
        self.set_aperture(hex_value)
    
    def set_shutter_speed_quick(self, speed):
        """
        Set shutter speed using human-readable notation
        
        Args:
            speed: Shutter speed as string (e.g., '1/60', '1/125', '1/1000')
                   Or as number for long exposures (e.g., '1', '2', '30')
                   Or 'bulb' for bulb mode
        
        Examples:
            camera.set_shutter_speed_quick('1/60')    # 1/60 second
            camera.set_shutter_speed_quick('1/125')   # 1/125 second
            camera.set_shutter_speed_quick('1/1000')  # 1/1000 second
            camera.set_shutter_speed_quick('1')       # 1 second
            camera.set_shutter_speed_quick('30')      # 30 seconds
            camera.set_shutter_speed_quick('bulb')    # Bulb mode
        
        Raises:
            ValueError: If the shutter speed is not supported
        
        Note:
            Camera must typically be in Manual (M) or Shutter Priority (Tv) mode.
        """
        # Normalize the input
        speed_str = str(speed).lower().strip()
        
        if speed_str not in self._SHUTTER_VALUES:
            # Try some common variations
            if '/' not in speed_str and speed_str.replace('.', '').isdigit():
                # User might have entered a decimal like 0.5 or integer like 2
                # Try to find it in our long exposure values
                if speed_str not in self._SHUTTER_VALUES:
                    available = sorted([k for k in self._SHUTTER_VALUES.keys() 
                                      if '/' not in k and k != 'bulb'])
                    raise ValueError(
                        f"Shutter speed '{speed}' not directly supported. "
                        f"Available long exposures: {available}. "
                        f"Available fast speeds: 1/60, 1/125, 1/250, 1/500, 1/1000, etc."
                    )
            else:
                # Show available fractional speeds
                available_fractions = sorted([k for k in self._SHUTTER_VALUES.keys() if '/' in k])
                available_long = sorted([k for k in self._SHUTTER_VALUES.keys() 
                                       if '/' not in k and k != 'bulb'])
                raise ValueError(
                    f"Shutter speed '{speed}' not directly supported. "
                    f"Available fractional speeds: {available_fractions[:10]}... "
                    f"Available long exposures: {available_long}"
                )
        
        hex_value = self._SHUTTER_VALUES[speed_str]
        self.set_shutter_speed(hex_value)
    
    def get_iso_readable(self):
        """
        Get current ISO in human-readable format
        
        Returns:
            int: ISO value (e.g., 100, 400, 1600) or None if not available
        """
        hex_value = self.get_iso()
        if hex_value is None:
            return None
        
        # Reverse lookup
        for iso, code in self._ISO_VALUES.items():
            if code == hex_value:
                return iso
        return None
    
    def get_aperture_readable(self):
        """
        Get current aperture in human-readable format
        
        Returns:
            float: Aperture f-stop (e.g., 2.8, 5.6, 11) or None if not available
        """
        hex_value = self.get_aperture()
        if hex_value is None:
            return None
        
        # Reverse lookup
        for f_stop, code in self._APERTURE_VALUES.items():
            if code == hex_value:
                return f_stop
        return None
    
    def get_shutter_speed_readable(self):
        """
        Get current shutter speed in human-readable format
        
        Returns:
            str: Shutter speed (e.g., '1/60', '1/125', '2') or None if not available
        """
        hex_value = self.get_shutter_speed()
        if hex_value is None:
            return None
        
        # Reverse lookup
        for speed, code in self._SHUTTER_VALUES.items():
            if code == hex_value:
                return speed
        return None
    
    def get_exposure_compensation(self):
        """Get exposure compensation value"""
        try:
            return self.get_property(EdsPropertyID_.ExposureCompensation)
        except:
            return None
    
    def set_exposure_compensation(self, value):
        """
        Set exposure compensation
        
        Args:
            value: Canon exposure compensation constant
        """
        self.set_property(EdsPropertyID_.ExposureCompensation, value)
    
    def get_image_quality(self):
        """Get current image quality setting"""
        try:
            return self.get_property(EdsPropertyID_.ImageQuality)
        except:
            return None
    
    def set_image_quality(self, quality_value):
        """
        Set image quality
        
        Args:
            quality_value: Canon image quality constant
        """
        self.set_property(EdsPropertyID_.ImageQuality, quality_value)
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def keep_alive(self):
        """
        Reset shutdown timer to keep camera awake
        Call this periodically during long operations
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        err = EdsSendCommand(self.camera_ref, EdsCameraCommand.ExtendShutDownTimer, 0)
        check_error(err, "ExtendShutDownTimer")
    
    def process_events(self, duration_seconds=0.1):
        """
        Process camera events for specified duration
        
        Args:
            duration_seconds: How long to process events (default: 0.1s)
        """
        import time
        start = time.time()
        while time.time() - start < duration_seconds:
            EdsGetEvent()
            time.sleep(0.01)
    
    def wait_for_events(self, timeout_seconds=10, check_interval=0.1):
        """
        Wait for and process events until timeout
        
        Args:
            timeout_seconds: Maximum time to wait
            check_interval: How often to check for events
        """
        import time
        elapsed = 0
        while elapsed < timeout_seconds:
            EdsGetEvent()
            time.sleep(check_interval)
            elapsed += check_interval
    
    def get_camera_info(self):
        """
        Get comprehensive camera information
        
        Returns:
            dict: Camera information including battery, shots, firmware, etc.
        """
        info = self.get_device_info()
        info['product_name'] = self.get_product_name()
        info['firmware'] = self.get_firmware_version()
        info['battery_level'] = self.get_battery_level()
        info['available_shots'] = self.get_available_shots()
        info['iso'] = self.get_iso()
        info['aperture'] = self.get_aperture()
        info['shutter_speed'] = self.get_shutter_speed()
        return info
    
    def download_images_from_camera(self, save_directory="downloads", 
                                     callback=None, file_filter=None, max_images=None):
        """
        Download images from camera SD card to computer
        FIXED: Now properly recurses into subdirectories like DCIM/100CANON
        
        Args:
            save_directory: Directory to save images to
            callback: Optional callback(filename, save_path, index, total)
            file_filter: Optional function to filter files (takes filename, returns bool)
            max_images: Maximum number of images to download (None for all)
        
        Returns:
            list: Paths to downloaded files
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        
        downloaded_files = []
        total_downloaded = 0
        
        def download_from_directory(dir_ref, depth=0):
            """Recursively download images from directory"""
            nonlocal total_downloaded
            
            if max_images and total_downloaded >= max_images:
                return
            
            item_count = EdsUInt32()
            err = EdsGetChildCount(dir_ref, byref(item_count))
            if err != EdsErrorCodes.EDS_ERR_OK:
                return
            
            # Reverse the order to get newest images first
            for idx in range(item_count.value - 1, -1, -1):
                if max_images and total_downloaded >= max_images:
                    break
                
                item_ref = EdsDirectoryItemRef()
                err = EdsGetChildAtIndex(dir_ref, idx, byref(item_ref))
                if err != EdsErrorCodes.EDS_ERR_OK:
                    continue
                
                info = EdsDirectoryItemInfo()
                err = EdsGetDirectoryItemInfo(item_ref, byref(info))
                if err != EdsErrorCodes.EDS_ERR_OK:
                    EdsRelease(item_ref)
                    continue
                
                if info.isFolder:
                    # Recurse into subdirectory
                    download_from_directory(item_ref, depth + 1)
                    EdsRelease(item_ref)
                else:
                    # Download this file
                    try:
                        filename = info.szFileName.decode('utf-8', errors='ignore')
                        
                        # Apply filter if provided
                        if file_filter and not file_filter(filename):
                            EdsRelease(item_ref)
                            continue
                        
                        # Create file stream
                        save_path = os.path.join(save_directory, filename)
                        
                        # CRITICAL: Create empty file first - SDK requires file to exist!
                        with open(save_path, 'wb') as f:
                            pass  # Create empty file
                            
                        stream = EdsStreamRef()
                        err = EdsCreateFileStream(
                            save_path.encode('utf-8'),
                            EdsFileCreateDisposition.CreateAlways,
                            EdsAccess.Write,
                            byref(stream)
                        )
                        
                        if err == EdsErrorCodes.EDS_ERR_OK:
                            # Download
                            err = EdsDownload(item_ref, info.size, stream)
                            if err == EdsErrorCodes.EDS_ERR_OK:
                                err = EdsDownloadComplete(item_ref)
                                if err == EdsErrorCodes.EDS_ERR_OK:
                                    downloaded_files.append(save_path)
                                    total_downloaded += 1
                                    
                                    if callback:
                                        callback(filename, save_path, total_downloaded, max_images)
                            
                            EdsRelease(stream)
                    except:
                        pass
                    
                    EdsRelease(item_ref)
        
        try:
            # Get volume
            volume_count = EdsUInt32()
            err = EdsGetChildCount(self.camera_ref, byref(volume_count))
            if err != EdsErrorCodes.EDS_ERR_OK or volume_count.value == 0:
                return downloaded_files
            
            volume_ref = EdsVolumeRef()
            err = EdsGetChildAtIndex(self.camera_ref, 0, byref(volume_ref))
            if err != EdsErrorCodes.EDS_ERR_OK:
                return downloaded_files
            
            # Download all images recursively
            download_from_directory(volume_ref)
            
            EdsRelease(volume_ref)
            
        except Exception as e:
            print(f"Error during bulk download: {e}")
        
        return downloaded_files
    
    def get_image_count_on_camera(self):
        """
        Get count of images stored on camera's SD card
        FIXED: Now properly recurses into subdirectories like DCIM/100CANON
        
        Returns:
            int: Number of images on camera
        """
        if not self.camera_ref:
            raise RuntimeError("No camera selected.")
        
        def count_images_recursive(parent_ref):
            """Recursively count images in a directory"""
            total = 0
            
            item_count = EdsUInt32()
            err = EdsGetChildCount(parent_ref, byref(item_count))
            if err != EdsErrorCodes.EDS_ERR_OK:
                return 0
            
            for idx in range(item_count.value):
                item_ref = EdsDirectoryItemRef()
                err = EdsGetChildAtIndex(parent_ref, idx, byref(item_ref))
                if err != EdsErrorCodes.EDS_ERR_OK:
                    continue
                
                info = EdsDirectoryItemInfo()
                err = EdsGetDirectoryItemInfo(item_ref, byref(info))
                if err == EdsErrorCodes.EDS_ERR_OK:
                    if info.isFolder:
                        # Recurse into subdirectory
                        total += count_images_recursive(item_ref)
                    else:
                        # Count this file
                        total += 1
                
                EdsRelease(item_ref)
            
            return total
        
        try:
            # Get volume
            volume_count = EdsUInt32()
            err = EdsGetChildCount(self.camera_ref, byref(volume_count))
            if err != EdsErrorCodes.EDS_ERR_OK or volume_count.value == 0:
                return 0
            
            volume_ref = EdsVolumeRef()
            err = EdsGetChildAtIndex(self.camera_ref, 0, byref(volume_ref))
            if err != EdsErrorCodes.EDS_ERR_OK:
                return 0
            
            # Count all images recursively starting from volume
            total_images = count_images_recursive(volume_ref)
            
            EdsRelease(volume_ref)
            return total_images
            
        except:
            return 0

    
    # =============================================================================
    # Context Manager
    # =============================================================================
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize_sdk()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.terminate_sdk()
        return False


if __name__ == "__main__":
    print("Canon EDSDK Python Wrapper")
    print("This is a library module. Import it to use in your scripts.")
    print("\n" + "="*60)
    print("BASIC USAGE EXAMPLES")
    print("="*60)
    
    print("""
# Example 1: Simple Photo Capture
from canon_edsdk import CanonCamera, EdsSaveTo

with CanonCamera() as camera:
    num_cameras = camera.get_camera_list()
    if num_cameras > 0:
        camera.get_camera(0)
        camera.open_session()
        camera.set_save_to(EdsSaveTo.Host)
        camera.set_capacity(0x7FFFFFFF, 0x1000)
        camera.take_picture()
        camera.process_events(5)  # Wait for download
    """)
    
    print("""
# Example 2: Auto-Download Handler
from canon_edsdk import CanonCamera, EdsSaveTo
import time

def on_download(filename, save_path):
    print(f"Downloaded: {filename}")

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    
    # Setup auto-download to specific folder
    camera.set_save_to(EdsSaveTo.Host)
    camera.set_capacity(0x7FFFFFFF, 0x1000)
    camera.setup_download_handler(
        callback=on_download,
        save_directory="C:/Photos"
    )
    
    # Take picture - will auto-download
    camera.take_picture()
    camera.wait_for_events(10)
    """)
    
    print("""
# Example 3: Live View
from canon_edsdk import CanonCamera

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    
    # Start live view
    camera.start_live_view()
    
    # Get live view image
    image_data = camera.get_live_view_image()
    if image_data:
        with open("liveview.jpg", "wb") as f:
            f.write(image_data)
    
    camera.stop_live_view()
    """)
    
    print("""
# Example 4: Camera Information
from canon_edsdk import CanonCamera

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    
    # Get comprehensive info
    info = camera.get_camera_info()
    print(f"Camera: {info['product_name']}")
    print(f"Firmware: {info['firmware']}")
    print(f"Battery: {info['battery_level']}%")
    print(f"Shots remaining: {info['available_shots']}")
    """)
    
    print("""
# Example 5: Manual Focus Control
from canon_edsdk import CanonCamera
import time

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    camera.start_live_view()
    
    # Move focus
    camera.focus_near(speed=2)
    time.sleep(0.5)
    
    # Or autofocus
    camera.autofocus()
    time.sleep(1)
    
    camera.stop_live_view()
    """)
    
    print("""
# Example 6: Bulb Exposure
from canon_edsdk import CanonCamera

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    
    # 30 second exposure
    camera.bulb_exposure(30)
    """)
    
    print("""
# Example 7: Change Camera Settings (Easy Way)
from canon_edsdk import CanonCamera

with CanonCamera() as camera:
    camera.get_camera_list()
    camera.get_camera(0)
    camera.open_session()
    
    # Read current settings (human-readable)
    current_iso = camera.get_iso_readable()
    current_aperture = camera.get_aperture_readable()
    current_shutter = camera.get_shutter_speed_readable()
    print(f"Current ISO: {current_iso}")
    print(f"Current Aperture: f/{current_aperture}")
    print(f"Current Shutter: {current_shutter}")
    
    # Change settings using human-readable values
    camera.set_iso_quick(400)           # Set to ISO 400
    camera.set_aperture_quick(2.8)      # Set to f/2.8
    camera.set_shutter_speed_quick('1/60')  # Set to 1/60 second
    
    # Or use hex codes directly if you prefer:
    # camera.set_iso(0x00000058)          # ISO 400
    # camera.set_aperture(0x00000020)     # f/2.8
    # camera.set_shutter_speed(0x00000068)  # 1/60
    """)
    
    print("\n" + "="*60)
    print("For more information, see the Canon EDSDK documentation")
    print("="*60)
