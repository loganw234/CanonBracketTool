/**
 * Canon Exposure Bracketing Tool
 * Main JavaScript File
 */

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize app components
    const app = new App();
    app.init();
});

/**
 * Main App Class
 */
class App {
    constructor() {
        // App state
        this.state = {
            connected: false,
            cameraInfo: null,
            currentSettings: null,
            presets: [],
            currentPreset: null,
            currentBrackets: [],
            captureMode: 'standard',
            focusStack: {
                enabled: false,
                steps: 10,
                step_size: 3,
                speed: 2,
                direction: 'near'
            },
            activeCapture: null,
            theme: 'dark'
        };

        // Socket.io connection
        this.socket = io();

        // DOM elements
        this.elements = {};

        // Event handlers
        this.handlers = {};
    }

    /**
     * Initialize the app
     */
    init() {
        console.log('Initializing app...');
        console.log('DEBUG: Starting init method');
        
        // Cache DOM elements
        this.cacheElements();
        
        // We'll initialize delay unit handlers later when the DOM is fully loaded
        // this.initDelayUnitHandlers();
        
        // Create and add the Test Settings button
        this.createTestSettingsButton();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup socket events
        this.setupSocketEvents();
        
        // Load settings
        this.loadSettings();
        
        // Load presets
        this.loadPresets();
        
        // Check camera connection
        this.checkCameraConnection();
        
        // Show toast notification
        this.showToast('Application Started', 'Canon Exposure Bracketing Tool is ready', 'info');
        
        console.log('DEBUG: Completed init method');
    }
    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        // Connection elements
        this.elements.connectionStatus = document.getElementById('connection-status');
        this.elements.connectBtn = document.getElementById('connect-btn');
        
        // Camera info elements
        this.elements.cameraModel = document.getElementById('camera-model');
        this.elements.cameraBattery = document.getElementById('camera-battery');
        this.elements.cameraShots = document.getElementById('camera-shots');
        
        // Current settings elements
        this.elements.currentIso = document.getElementById('current-iso');
        this.elements.currentAperture = document.getElementById('current-aperture');
        this.elements.currentShutter = document.getElementById('current-shutter');
        
        // Preset elements
        this.elements.presetList = document.getElementById('preset-list');
        this.elements.newPresetBtn = document.getElementById('new-preset-btn');
        this.elements.importPresetBtn = document.getElementById('import-preset-btn');
        this.elements.presetName = document.getElementById('preset-name');
        this.elements.presetDescription = document.getElementById('preset-description');
        this.elements.savePresetBtn = document.getElementById('save-preset-btn');
        this.elements.exportPresetBtn = document.getElementById('export-preset-btn');
        
        // Bracket elements
        this.elements.bracketList = document.getElementById('bracket-list');
        this.elements.addBracketBtn = document.getElementById('add-bracket-btn');
        this.elements.addBracketBtnBottom = document.getElementById('add-bracket-btn-bottom');
        this.elements.generateEvBracketsBtn = document.getElementById('generate-ev-brackets-btn');
        
        // Focus stack elements
        this.elements.focusStackEnabled = document.getElementById('focus-stack-enabled');
        this.elements.focusStackOptions = document.getElementById('focus-stack-options');
        this.elements.focusSteps = document.getElementById('focus-steps');
        this.elements.focusStepSize = document.getElementById('focus-step-size');
        this.elements.focusSpeed = document.getElementById('focus-speed');
        this.elements.focusDirection = document.getElementById('focus-direction');
        
        // Capture elements
        this.elements.captureModeBtns = document.querySelectorAll('[data-mode]');
        this.elements.saveDirectory = document.getElementById('save-directory');
        this.elements.summaryBrackets = document.getElementById('summary-brackets');
        this.elements.summaryFrames = document.getElementById('summary-frames');
        this.elements.summaryTime = document.getElementById('summary-time');
        this.elements.startCaptureBtn = document.getElementById('start-capture-btn');
        this.elements.stopCaptureBtn = document.getElementById('stop-capture-btn');
        this.elements.captureProgress = document.getElementById('capture-progress');
        this.elements.progressFill = document.querySelector('.progress-fill');
        this.elements.progressText = document.querySelector('.progress-text');
        this.elements.progressBracket = document.getElementById('progress-bracket');
        this.elements.progressFrame = document.getElementById('progress-frame');
        this.elements.progressCompleted = document.getElementById('progress-completed');
        this.elements.progressFailed = document.getElementById('progress-failed');
        
        // Tab elements
        this.elements.tabBtns = document.querySelectorAll('.tab-btn');
        this.elements.tabContents = document.querySelectorAll('.tab-content');
        
        // Settings elements
        this.elements.themeSelect = document.getElementById('theme-select');
        this.elements.defaultSaveDir = document.getElementById('default-save-dir');
        this.elements.autoConnect = document.getElementById('auto-connect');
        this.elements.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.elements.resetSettingsBtn = document.getElementById('reset-settings-btn');
        
        // Modal elements
        this.elements.bracketModal = document.getElementById('bracket-modal');
        this.elements.bracketModalSave = document.getElementById('bracket-modal-save');
        this.elements.bracketModalCancel = document.getElementById('bracket-modal-cancel');
        this.elements.bracketName = document.getElementById('bracket-name');
        this.elements.bracketIso = document.getElementById('bracket-iso');
        this.elements.bracketAperture = document.getElementById('bracket-aperture');
        this.elements.bracketShutter = document.getElementById('bracket-shutter');
        this.elements.bracketFrames = document.getElementById('bracket-frames');
        this.elements.bracketDelay = document.getElementById('bracket-delay');
        this.elements.bracketDelayUnit = document.getElementById('bracket-delay-unit');
        
        this.elements.evBracketsModal = document.getElementById('ev-brackets-modal');
        this.elements.evModalGenerate = document.getElementById('ev-modal-generate');
        this.elements.evModalCancel = document.getElementById('ev-modal-cancel');
        this.elements.evBaseIso = document.getElementById('ev-base-iso');
        this.elements.evBaseAperture = document.getElementById('ev-base-aperture');
        this.elements.evBaseShutter = document.getElementById('ev-base-shutter');
        this.elements.evSteps = document.getElementById('ev-steps');
        this.elements.evNumBrackets = document.getElementById('ev-num-brackets');
        this.elements.evPriority = document.getElementById('ev-priority');
        this.elements.evFrames = document.getElementById('ev-frames');
        this.elements.evDelay = document.getElementById('ev-delay');
        this.elements.evDelayUnit = document.getElementById('ev-delay-unit');
        
        // Toast container
        this.elements.toastContainer = document.getElementById('toast-container');
    }
        
    /**
     * Render bracket list
     */
    renderBracketList() {
        // Clear the list
        this.elements.bracketList.innerHTML = '';
        
        // Check if there are brackets
        if (this.state.currentBrackets.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = 'No brackets defined. Add a bracket to start.';
            this.elements.bracketList.appendChild(emptyMessage);
            return;
        }
        
        // Add each bracket to the list
        this.state.currentBrackets.forEach((bracket, index) => {
            const bracketEl = document.createElement('div');
            bracketEl.className = 'bracket-item';
            
            // Create bracket content
            // Prepare the delay HTML if delay exists and is greater than 0
            let delayHtml = '';
            if (bracket.delay && bracket.delay > 0) {
                let displayValue = bracket.delay;
                let unit = 's';
                
                if (bracket.delay >= 3600) {
                    // Convert to hours if >= 1 hour
                    displayValue = (bracket.delay / 3600).toFixed(2);
                    unit = 'h';
                } else if (bracket.delay >= 60) {
                    // Convert to minutes if >= 1 minute
                    displayValue = (bracket.delay / 60).toFixed(1);
                    unit = 'm';
                }
                
                delayHtml = `<div class="bracket-detail">
                    <span class="detail-label">Delay:</span>
                    <span class="detail-value">${displayValue}${unit}</span>
                </div>`;
            }
            
            bracketEl.innerHTML = `
                <div class="bracket-header">
                    <h3>${bracket.name}</h3>
                    <div class="bracket-actions">
                        <button class="edit-bracket-btn" data-index="${index}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="delete-bracket-btn" data-index="${index}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="bracket-details">
                    <div class="bracket-detail">
                        <span class="detail-label">ISO:</span>
                        <span class="detail-value">${bracket.iso}</span>
                    </div>
                    <div class="bracket-detail">
                        <span class="detail-label">Aperture:</span>
                        <span class="detail-value">f/${bracket.aperture}</span>
                    </div>
                    <div class="bracket-detail">
                        <span class="detail-label">Shutter:</span>
                        <span class="detail-value">${bracket.shutter_speed}</span>
                    </div>
                    <div class="bracket-detail">
                        <span class="detail-label">Frames:</span>
                        <span class="detail-value">${bracket.frames}</span>
                    </div>
                    ${delayHtml}
                </div>
            `;
            
            // Add to list
            this.elements.bracketList.appendChild(bracketEl);
            
            // Add event listeners
            bracketEl.querySelector('.edit-bracket-btn').addEventListener('click', () => {
                this.editBracket(index);
            });
            
            bracketEl.querySelector('.delete-bracket-btn').addEventListener('click', () => {
                this.deleteBracket(index);
            });
        });
    }
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Connect/disconnect button
        this.elements.connectBtn.addEventListener('click', () => {
            if (this.state.connected) {
                this.disconnectCamera();
            } else {
                this.connectCamera();
            }
        });
        
        // Tab buttons
        this.elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });
        
        // Capture mode buttons
        this.elements.captureModeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                this.setCaptureMode(mode);
            });
        });
        
        // Focus stack toggle
        this.elements.focusStackEnabled.addEventListener('change', () => {
            this.state.focusStack.enabled = this.elements.focusStackEnabled.checked;
            this.updateFocusStackOptions();
            // Update capture summary to reflect the change in total frames
            this.updateCaptureSummary();
        });
        
        // Focus stack options
        this.elements.focusSteps.addEventListener('change', () => {
            this.state.focusStack.steps = parseInt(this.elements.focusSteps.value);
            // Update capture summary to reflect the change in total frames
            if (this.state.focusStack.enabled) {
                this.updateCaptureSummary();
            }
        });
        
        this.elements.focusStepSize.addEventListener('change', () => {
            this.state.focusStack.step_size = parseInt(this.elements.focusStepSize.value);
        });
        
        this.elements.focusSpeed.addEventListener('change', () => {
            this.state.focusStack.speed = parseInt(this.elements.focusSpeed.value);
        });
        
        this.elements.focusDirection.addEventListener('change', () => {
            this.state.focusStack.direction = this.elements.focusDirection.value;
        });
        
        // Add bracket buttons
        this.elements.addBracketBtn.addEventListener('click', () => {
            console.log('DEBUG: Add bracket button clicked');
            this.openBracketModal();
        });
        
        this.elements.addBracketBtnBottom.addEventListener('click', () => {
            console.log('DEBUG: Add bracket bottom button clicked');
            this.openBracketModal();
        });
        
        // Generate EV brackets button
        this.elements.generateEvBracketsBtn.addEventListener('click', () => {
            this.openEvBracketsModal();
        });
        
        // Bracket modal buttons
        this.elements.bracketModalSave.addEventListener('click', () => {
            this.saveBracketFromModal();
        });
        
        this.elements.bracketModalCancel.addEventListener('click', () => {
            this.closeBracketModal();
        });
        
        // EV brackets modal buttons
        this.elements.evModalGenerate.addEventListener('click', () => {
            this.generateEvBrackets();
        });
        
        this.elements.evModalCancel.addEventListener('click', () => {
            this.closeEvBracketsModal();
        });
        
        // Save preset button
        this.elements.savePresetBtn.addEventListener('click', () => {
            this.savePreset();
        });
        
        // Export preset button
        this.elements.exportPresetBtn.addEventListener('click', () => {
            this.exportPreset();
        });
        
        // Start capture button
        this.elements.startCaptureBtn.addEventListener('click', () => {
            this.startCapture();
        });
        
        // Stop capture button
        this.elements.stopCaptureBtn.addEventListener('click', () => {
            this.stopCapture();
        });
        
        // Test settings button
        if (this.elements.testSettingsBtn) {
            this.elements.testSettingsBtn.addEventListener('click', () => {
                this.testAllSettings();
            });
        }
        
        // Theme select
        this.elements.themeSelect.addEventListener('change', () => {
            this.setTheme(this.elements.themeSelect.value);
        });
        
        // Save settings button
        this.elements.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Reset settings button
        this.elements.resetSettingsBtn.addEventListener('click', () => {
            this.resetSettings();
        });
        
        // Close modal buttons
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });
        
        // Ensure the import modal close button works
        const importModalCloseBtn = document.querySelector('#import-preset-modal .close-btn');
        if (importModalCloseBtn) {
            importModalCloseBtn.addEventListener('click', () => {
                document.getElementById('import-preset-modal').style.display = 'none';
            });
        }
        
        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });
        
        // New preset button
        this.elements.newPresetBtn.addEventListener('click', () => {
            this.newPreset();
        });
        
        // Import preset button
        this.elements.importPresetBtn.addEventListener('click', () => {
            this.importPreset();
        });
        
        // Delay unit handlers
        if (this.elements.bracketDelayUnit) {
            this.elements.bracketDelayUnit.addEventListener('change', () => {
                // Update the step value based on the unit
                const unit = parseInt(this.elements.bracketDelayUnit.value);
                if (unit === 1) { // seconds
                    this.elements.bracketDelay.step = "0.5";
                } else if (unit === 60) { // minutes
                    this.elements.bracketDelay.step = "0.5";
                } else { // hours
                    this.elements.bracketDelay.step = "0.25";
                }
            });
        }
        
        if (this.elements.evDelayUnit) {
            this.elements.evDelayUnit.addEventListener('change', () => {
                // Update the step value based on the unit
                const unit = parseInt(this.elements.evDelayUnit.value);
                if (unit === 1) { // seconds
                    this.elements.evDelay.step = "0.5";
                } else if (unit === 60) { // minutes
                    this.elements.evDelay.step = "0.5";
                } else { // hours
                    this.elements.evDelay.step = "0.25";
                }
            });
        }
    }
    /**
     * Setup Socket.IO event listeners
     */
    setupSocketEvents() {
        // Connect event
        this.socket.on('connect', () => {
            console.log('Socket connected');
        });
        
        // Disconnect event
        this.socket.on('disconnect', () => {
            console.log('Socket disconnected');
        });
        
        // Capture update event
        this.socket.on('capture_update', (data) => {
            this.updateCaptureProgress(data);
        });
    }

    /**
     * Load presets from server
     */
    loadPresets() {
        console.log('DEBUG: Loading presets from server');
        fetch('/api/presets')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('DEBUG: Presets loaded successfully', data.presets);
                    this.state.presets = data.presets || [];
                    this.renderPresetList();
                } else {
                    console.error('Error loading presets:', data.message);
                }
            })
            .catch(error => {
                console.error('Error loading presets:', error);
            });
    }
    
    /**
     * Render preset list in the UI
     */
    renderPresetList() {
        // Clear the list
        this.elements.presetList.innerHTML = '';
        
        // Check if there are presets
        if (this.state.presets.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = 'No presets available. Create a new preset to get started.';
            this.elements.presetList.appendChild(emptyMessage);
            return;
        }
        
        // Group presets by folder
        const presetsByFolder = {};
        const rootPresets = [];
        
        this.state.presets.forEach(preset => {
            if (preset.folder) {
                if (!presetsByFolder[preset.folder]) {
                    presetsByFolder[preset.folder] = [];
                }
                presetsByFolder[preset.folder].push(preset);
            } else {
                rootPresets.push(preset);
            }
        });
        
        // Add root presets first
        rootPresets.forEach(preset => {
            this.addPresetToList(preset);
        });
        
        // Add folder sections with their presets
        Object.keys(presetsByFolder).sort().forEach(folder => {
            // Create folder section
            const folderEl = document.createElement('div');
            folderEl.className = 'preset-folder';
            
            // Create folder header
            const folderHeader = document.createElement('div');
            folderHeader.className = 'folder-header';
            folderHeader.innerHTML = `
                <i class="fas fa-folder"></i>
                <span>${folder}</span>
            `;
            folderEl.appendChild(folderHeader);
            
            // Create folder content
            const folderContent = document.createElement('div');
            folderContent.className = 'folder-content';
            
            // Add presets to folder
            presetsByFolder[folder].forEach(preset => {
                const presetEl = this.createPresetElement(preset);
                folderContent.appendChild(presetEl);
            });
            
            folderEl.appendChild(folderContent);
            
            // Add folder to list
            this.elements.presetList.appendChild(folderEl);
            
            // Add toggle functionality
            folderHeader.addEventListener('click', () => {
                folderEl.classList.toggle('expanded');
            });
        });
    }
    
    /**
     * Add a preset to the list
     */
    addPresetToList(preset) {
        const presetEl = this.createPresetElement(preset);
        this.elements.presetList.appendChild(presetEl);
    }
    
    /**
     * Create a preset element
     */
    createPresetElement(preset) {
        const presetEl = document.createElement('div');
        presetEl.className = 'preset-item';
        if (this.state.currentPreset === preset.id) {
            presetEl.classList.add('active');
        }
        
        // Create preset content
        presetEl.innerHTML = `
            <div class="preset-header">
                <h3>${preset.name}</h3>
            </div>
            <div class="preset-description">${preset.description || ''}</div>
            <div class="preset-info">
                <span>${preset.brackets.length} brackets</span>
                ${preset.folder ? `<span class="preset-folder-tag">${preset.folder}</span>` : ''}
            </div>
        `;
        
        // Add click event to load preset
        presetEl.addEventListener('click', () => {
            this.loadPreset(preset.id);
        });
        
        return presetEl;
    }
    
    /**
     * Load a specific preset by ID
     */
    loadPreset(presetId) {
        fetch(`/api/presets/${presetId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const preset = data.preset;
                    
                    // Update state
                    this.state.currentPreset = preset.id;
                    this.state.currentBrackets = preset.brackets || [];
                    if (preset.focus_stack) {
                        this.state.focusStack = preset.focus_stack;
                    }
                    
                    // Update UI
                    this.elements.presetName.value = preset.name;
                    this.elements.presetDescription.value = preset.description || '';
                    this.elements.focusStackEnabled.checked = this.state.focusStack.enabled;
                    this.elements.focusSteps.value = this.state.focusStack.steps;
                    this.elements.focusStepSize.value = this.state.focusStack.step_size;
                    this.elements.focusSpeed.value = this.state.focusStack.speed || 2;
                    this.elements.focusDirection.value = this.state.focusStack.direction || 'near';
                    
                    // Update focus stack options visibility
                    this.updateFocusStackOptions();
                    
                    // Render brackets
                    this.renderBracketList();
                    
                    // Update capture summary
                    this.updateCaptureSummary();
                    
                    // Show toast
                    this.showToast('Preset Loaded', `Loaded preset: ${preset.name}`, 'success');
                } else {
                    this.showToast('Error', data.message || 'Failed to load preset', 'error');
                }
            })
            .catch(error => {
                console.error('Error loading preset:', error);
                this.showToast('Error', 'Failed to load preset', 'error');
            });
    }

    /**
     * Check camera connection status
     */
    checkCameraConnection() {
        fetch('/api/camera/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.status.connected) {
                        this.state.connected = true;
                        this.state.cameraInfo = data.status.info;
                        this.state.currentSettings = data.status.settings;
                        this.updateCameraStatus();
                    }
                }
            })
            .catch(error => {
                console.error('Error checking camera status:', error);
            });
    }

    /**
     * Connect to camera
     */
    connectCamera() {
        this.elements.connectBtn.disabled = true;
        this.elements.connectBtn.textContent = 'Connecting...';
        
        fetch('/api/camera/connect', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.connected = true;
                    this.showToast('Connected', 'Camera connected successfully', 'success');
                    
                    // Get camera status
                    this.checkCameraConnection();
                } else {
                    this.showToast('Connection Failed', data.message, 'error');
                }
                
                this.elements.connectBtn.disabled = false;
                this.updateConnectionStatus();
            })
            .catch(error => {
                console.error('Error connecting to camera:', error);
                this.showToast('Connection Error', 'Failed to connect to camera', 'error');
                this.elements.connectBtn.disabled = false;
                this.updateConnectionStatus();
            });
    }

    /**
     * Disconnect from camera
     */
    disconnectCamera() {
        this.elements.connectBtn.disabled = true;
        this.elements.connectBtn.textContent = 'Disconnecting...';
        
        fetch('/api/camera/disconnect', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.connected = false;
                    this.state.cameraInfo = null;
                    this.state.currentSettings = null;
                    this.showToast('Disconnected', 'Camera disconnected successfully', 'info');
                } else {
                    this.showToast('Disconnection Failed', data.message, 'error');
                }
                
                this.elements.connectBtn.disabled = false;
                this.updateConnectionStatus();
                this.updateCameraStatus();
            })
            .catch(error => {
                console.error('Error disconnecting from camera:', error);
                this.showToast('Disconnection Error', 'Failed to disconnect from camera', 'error');
                this.elements.connectBtn.disabled = false;
                this.updateConnectionStatus();
            });
    }

    /**
     * Update connection status UI
     */
    updateConnectionStatus() {
        if (this.state.connected) {
            this.elements.connectionStatus.className = 'status-indicator connected';
            this.elements.connectionStatus.innerHTML = '<i class="fas fa-circle"></i> Connected';
            this.elements.connectBtn.textContent = 'Disconnect';
        } else {
            this.elements.connectionStatus.className = 'status-indicator disconnected';
            this.elements.connectionStatus.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
            this.elements.connectBtn.textContent = 'Connect Camera';
        }
    }

    /**
     * Update camera status UI
     */
    updateCameraStatus() {
        if (this.state.connected && this.state.cameraInfo) {
            this.elements.cameraModel.textContent = this.state.cameraInfo.name || 'Unknown';
            this.elements.cameraBattery.textContent = `${this.state.cameraInfo.battery || '--'}%`;
            this.elements.cameraShots.textContent = this.state.cameraInfo.available_shots || '--';
        } else {
            this.elements.cameraModel.textContent = 'Not connected';
            this.elements.cameraBattery.textContent = '--';
            this.elements.cameraShots.textContent = '--';
        }
        
        if (this.state.connected && this.state.currentSettings) {
            this.elements.currentIso.textContent = this.state.currentSettings.iso || '--';
            this.elements.currentAperture.textContent = this.state.currentSettings.aperture ? `f/${this.state.currentSettings.aperture}` : '--';
            this.elements.currentShutter.textContent = this.state.currentSettings.shutter_speed || '--';
        } else {
            this.elements.currentIso.textContent = '--';
            this.elements.currentAperture.textContent = '--';
            this.elements.currentShutter.textContent = '--';
        }
    }
    /**
     * Switch between tabs
     */
    switchTab(tabId) {
        // Update tab buttons
        this.elements.tabBtns.forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update tab content
        this.elements.tabContents.forEach(content => {
            if (content.id === tabId) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    }

    /**
     * Set capture mode (standard, fast)
     */
    setCaptureMode(mode) {
        // Update buttons
        this.elements.captureModeBtns.forEach(btn => {
            if (btn.dataset.mode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update state
        this.state.captureMode = mode;
        
        // Update capture summary
        this.updateCaptureSummary();
    }

    /**
     * Update focus stack options visibility
     */
    updateFocusStackOptions() {
        if (this.state.focusStack.enabled) {
            this.elements.focusStackOptions.style.display = 'grid';
        } else {
            this.elements.focusStackOptions.style.display = 'none';
        }
    }

    /**
     * Update capture summary
     */
    updateCaptureSummary() {
        const totalBrackets = this.state.currentBrackets.length;
        
        // Calculate total frames, accounting for focus stacking if enabled
        let totalFrames = 0;
        if (this.state.focusStack.enabled) {
            // When focus stacking is enabled, each frame in a bracket results in
            // (focus_stack_steps + 1) actual shots
            const focusMultiplier = this.state.focusStack.steps + 1;
            totalFrames = this.state.currentBrackets.reduce((sum, bracket) =>
                sum + (bracket.frames * focusMultiplier), 0);
        } else {
            // Without focus stacking, just count the frames directly
            totalFrames = this.state.currentBrackets.reduce((sum, bracket) =>
                sum + bracket.frames, 0);
        }
        
        this.elements.summaryBrackets.textContent = totalBrackets;
        this.elements.summaryFrames.textContent = totalFrames;
        
        // Calculate estimated time
        let timePerFrame = 0;
        if (this.state.captureMode === 'standard') {
            timePerFrame = 3.5; // ~3.5 seconds per frame in standard mode
        } else {
            timePerFrame = 1.0; // ~1 second per frame in fast mode
        }
        
        // Add delay time if any brackets have delays
        let totalDelayTime = 0;
        this.state.currentBrackets.forEach(bracket => {
            if (bracket.delay && bracket.delay > 0) {
                totalDelayTime += bracket.delay * bracket.frames;
            }
        });
        
        // Format the estimated time nicely
        const formatTime = (seconds) => {
            if (seconds < 60) {
                return `${seconds.toFixed(1)} sec`;
            } else if (seconds < 3600) {
                return `${(seconds / 60).toFixed(1)} min`;
            } else {
                return `${(seconds / 3600).toFixed(2)} hours`;
            }
        };
        
        const estimatedSeconds = (totalFrames * timePerFrame) + totalDelayTime;
        
        this.elements.summaryTime.textContent = formatTime(estimatedSeconds);
    }

    /**
     * Open bracket modal for adding/editing
     */
    openBracketModal(bracketIndex = null) {
        console.log('DEBUG: Opening bracket modal', { bracketIndex });
        
        // Check if modal element exists
        if (!this.elements.bracketModal) {
            console.error('DEBUG: Bracket modal element not found');
            return;
        }
        
        // Set modal title
        const modalTitle = this.elements.bracketModal.querySelector('.modal-header h2');
        if (!modalTitle) {
            console.error('DEBUG: Modal title element not found');
            return;
        }
        modalTitle.textContent = bracketIndex !== null ? 'Edit Bracket' : 'Add Bracket';
        
        // Cache the delay elements
        this.elements.bracketDelay = document.getElementById('bracket-delay');
        this.elements.bracketDelayUnit = document.getElementById('bracket-delay-unit');
        
        // Clear form
        this.elements.bracketName.value = '';
        this.elements.bracketIso.value = '100';
        this.elements.bracketAperture.value = '8.0';
        this.elements.bracketShutter.value = '1/125';
        this.elements.bracketFrames.value = '10';
        this.elements.bracketDelay.value = '0';
        this.elements.bracketDelayUnit.value = '1'; // Default to seconds
        
        // Fill form if editing
        if (bracketIndex !== null) {
            const bracket = this.state.currentBrackets[bracketIndex];
            this.elements.bracketName.value = bracket.name;
            this.elements.bracketIso.value = bracket.iso.toString();
            this.elements.bracketAperture.value = bracket.aperture.toFixed(1);
            this.elements.bracketShutter.value = bracket.shutter_speed;
            this.elements.bracketFrames.value = bracket.frames.toString();
            
            // Set delay if it exists, otherwise default to 0
            if (bracket.delay !== undefined && bracket.delay > 0) {
                // Determine the best unit for display
                let displayValue = bracket.delay;
                let unitValue = 1; // Default to seconds
                
                if (bracket.delay >= 3600) {
                    // Convert to hours if >= 1 hour
                    displayValue = bracket.delay / 3600;
                    unitValue = 3600;
                } else if (bracket.delay >= 60) {
                    // Convert to minutes if >= 1 minute
                    displayValue = bracket.delay / 60;
                    unitValue = 60;
                }
                
                this.elements.bracketDelay.value = displayValue.toString();
                this.elements.bracketDelayUnit.value = unitValue.toString();
            } else {
                this.elements.bracketDelay.value = '0';
                this.elements.bracketDelayUnit.value = '1'; // Default to seconds
            }
        }
        
        // Store bracket index for saving
        this.elements.bracketModal.dataset.index = bracketIndex !== null ? bracketIndex : '';
        
        // No advanced settings to show
        
        // Show modal
        console.log('DEBUG: Showing bracket modal');
        this.elements.bracketModal.style.display = 'flex';
    }
    /**
     * Close bracket modal
     */
    closeBracketModal() {
        this.elements.bracketModal.style.display = 'none';
    }

    /**
     * Save bracket from modal
     */
    saveBracketFromModal() {
        console.log('DEBUG: Saving bracket from modal');
        
        // Check if form elements exist
        if (!this.elements.bracketName || !this.elements.bracketIso ||
            !this.elements.bracketAperture || !this.elements.bracketShutter ||
            !this.elements.bracketFrames || !this.elements.bracketDelay) {
            console.error('DEBUG: Bracket form elements not found', {
                name: !!this.elements.bracketName,
                iso: !!this.elements.bracketIso,
                aperture: !!this.elements.bracketAperture,
                shutter: !!this.elements.bracketShutter,
                frames: !!this.elements.bracketFrames,
                delay: !!this.elements.bracketDelay
            });
            return;
        }
        
        // Validate
        if (!this.elements.bracketName.value) {
            this.showToast('Error', 'Please enter a bracket name', 'error');
            return;
        }
        
        // Get values
        const name = this.elements.bracketName.value;
        const iso = parseInt(this.elements.bracketIso.value);
        const aperture = parseFloat(this.elements.bracketAperture.value);
        const shutter_speed = this.elements.bracketShutter.value;
        const frames = parseInt(this.elements.bracketFrames.value);
        
        // Calculate delay in seconds based on the unit
        const delayValue = parseFloat(this.elements.bracketDelay.value || 0);
        const delayUnit = parseInt(this.elements.bracketDelayUnit.value || 1);
        const delay = delayValue * delayUnit;
        
        // Create bracket data
        const bracketData = {
            name,
            iso,
            aperture,
            shutter_speed,
            frames,
            delay: delay || 0 // Ensure we have a default of 0 if not specified
        };
        
        // No additional settings to add
        
        // Check if editing or adding
        const bracketIndex = this.elements.bracketModal.dataset.index;
        
        if (bracketIndex !== '') {
            // Update existing bracket
            this.state.currentBrackets[bracketIndex] = bracketData;
        } else {
            // Add new bracket
            this.state.currentBrackets.push(bracketData);
        }
        
        // Update UI
        console.log('DEBUG: Bracket data before render', JSON.stringify(this.state.currentBrackets));
        this.renderBracketList();
        this.updateCaptureSummary();
        
        // Close modal
        this.closeBracketModal();
        
        // Show toast
        this.showToast('Success', bracketIndex !== '' ? 'Bracket updated' : 'Bracket added', 'success');
    }

    /**
     * Delete bracket
     */
    deleteBracket(index) {
        if (confirm('Are you sure you want to delete this bracket?')) {
            this.state.currentBrackets.splice(index, 1);
            this.renderBracketList();
            this.updateCaptureSummary();
            this.showToast('Success', 'Bracket deleted', 'success');
        }
    }

    /**
     * Edit bracket
     */
    editBracket(index) {
        this.openBracketModal(index);
    }

    /**
     * Open EV brackets modal
     */
    openEvBracketsModal() {
        // Show modal
        this.elements.evBracketsModal.style.display = 'flex';
    }

    /**
     * Close EV brackets modal
     */
    closeEvBracketsModal() {
        this.elements.evBracketsModal.style.display = 'none';
    }

    /**
     * Generate EV brackets
     */
    generateEvBrackets() {
        // Get values
        const baseIso = parseInt(this.elements.evBaseIso.value);
        const baseAperture = parseFloat(this.elements.evBaseAperture.value);
        const baseShutter = this.elements.evBaseShutter.value;
        const evSteps = parseFloat(this.elements.evSteps.value);
        const numBrackets = parseInt(this.elements.evNumBrackets.value);
        const priority = this.elements.evPriority.value;
        const framesPerBracket = parseInt(this.elements.evFrames.value);
        
        // Cache the delay elements
        this.elements.evDelay = document.getElementById('ev-delay');
        this.elements.evDelayUnit = document.getElementById('ev-delay-unit');
        
        // Calculate delay in seconds based on the unit
        const delayValue = parseFloat(this.elements.evDelay.value || 0);
        const delayUnit = parseInt(this.elements.evDelayUnit.value || 1);
        const delayBetweenShots = delayValue * delayUnit;
        
        // Create base settings
        const baseSettings = {
            iso: baseIso,
            aperture: baseAperture,
            shutter_speed: baseShutter
        };
        
        // Calculate EV value for base settings
        const baseEv = this.calculateEv(baseSettings);
        
        // Generate brackets
        const brackets = [];
        
        // Calculate starting EV (for the darkest bracket)
        let startEv;
        if (numBrackets % 2 === 1) {  // Odd number of brackets
            startEv = baseEv + (evSteps * (numBrackets / 2));
        } else {  // Even number of brackets
            startEv = baseEv + (evSteps * ((numBrackets - 1) / 2)) + (evSteps / 2);
        }
        
        // Generate each bracket
        for (let i = 0; i < numBrackets; i++) {
            const bracketEv = startEv - (i * evSteps);
            const settings = this.getSettingsForEv(bracketEv, baseIso, priority, baseAperture, baseShutter);
            
            // Calculate EV difference from base
            const evDiff = baseEv - bracketEv;
            
            // Create bracket name
            let name;
            if (evDiff > 0) {
                name = `Under ${evDiff.toFixed(1)} EV`;
            } else if (evDiff < 0) {
                name = `Over ${Math.abs(evDiff).toFixed(1)} EV`;
            } else {
                name = 'Base Exposure';
            }
            
            // Create bracket
            brackets.push({
                name,
                iso: settings.iso,
                aperture: settings.aperture,
                shutter_speed: settings.shutter_speed,
                frames: framesPerBracket,
                delay: delayBetweenShots
            });
        }
        
        // Add brackets to current brackets
        this.state.currentBrackets = [...this.state.currentBrackets, ...brackets];
        
        // Update UI
        this.renderBracketList();
        this.updateCaptureSummary();
        
        // Close modal
        this.closeEvBracketsModal();
        
        // Show toast
        this.showToast('Success', `Generated ${numBrackets} brackets`, 'success');
    }
    /**
     * Calculate EV value for given settings
     */
    calculateEv(settings) {
        // Convert shutter speed to seconds
        let shutterSeconds;
        if (settings.shutter_speed.includes('/')) {
            const parts = settings.shutter_speed.split('/');
            shutterSeconds = parseFloat(parts[0]) / parseFloat(parts[1]);
        } else {
            shutterSeconds = parseFloat(settings.shutter_speed);
        }
        
        // Calculate EV100
        const ev100 = Math.log2((settings.aperture * settings.aperture * 100) / (shutterSeconds * settings.iso));
        
        return ev100;
    }

    /**
     * Get settings for a given EV value
     */
    getSettingsForEv(ev, iso, priority, preferredAperture, baseShutter) {
        // Standard aperture values
        const apertures = [1.4, 2, 2.8, 4, 5.6, 8, 11, 16, 22];
        
        // Standard shutter speeds in seconds
        const shutterSpeeds = [
            '30', '15', '8', '4', '2', '1',
            '1/2', '1/4', '1/8', '1/15', '1/30', '1/60', '1/125',
            '1/250', '1/500', '1/1000', '1/2000', '1/4000', '1/8000'
        ];
        
        // Standard ISO values
        const isoValues = [100, 200, 400, 800, 1600, 3200, 6400];
        
        // NOTE: The priority parameter indicates which setting to KEEP CONSTANT (not which to adjust)
        if (priority === 'shutter') {
            // When shutter is priority, keep shutter speed constant and adjust aperture
            const preferredShutter = baseShutter || '1/60';
            
            // Convert to seconds
            let preferredSeconds;
            if (preferredShutter.includes('/')) {
                const parts = preferredShutter.split('/');
                preferredSeconds = parseFloat(parts[0]) / parseFloat(parts[1]);
            } else {
                preferredSeconds = parseFloat(preferredShutter);
            }
            
            // Calculate required aperture
            const requiredAperture = Math.sqrt((iso * preferredSeconds * (2 ** ev)) / 100);
            
            // Find closest standard aperture
            const aperture = apertures.reduce((prev, curr) => {
                return (Math.abs(curr - requiredAperture) < Math.abs(prev - requiredAperture) ? curr : prev);
            });
            
            return {
                iso,
                aperture,
                shutter_speed: preferredShutter
            };
        } else if (priority === 'aperture') {
            // When aperture is priority, keep aperture constant and adjust shutter speed
            const aperture = preferredAperture;
            
            // Calculate required shutter speed
            const shutterSeconds = (aperture * aperture * 100) / (iso * (2 ** ev));
            
            // Find closest standard shutter speed
            let closestShutter = shutterSpeeds[0];
            let closestDiff = Infinity;
            
            for (const speed of shutterSpeeds) {
                let speedInSeconds;
                if (speed.includes('/')) {
                    const parts = speed.split('/');
                    speedInSeconds = parseFloat(parts[0]) / parseFloat(parts[1]);
                } else {
                    speedInSeconds = parseFloat(speed);
                }
                
                const diff = Math.abs(speedInSeconds - shutterSeconds);
                if (diff < closestDiff) {
                    closestDiff = diff;
                    closestShutter = speed;
                }
            }
            
            return {
                iso,
                aperture,
                shutter_speed: closestShutter
            };
        } else {  // priority === 'iso'
            // When ISO is priority, keep ISO constant and adjust both aperture and shutter
            // For simplicity, we'll adjust shutter speed and keep aperture at the base value
            const aperture = preferredAperture || 8.0;
            
            // Calculate required shutter speed
            const shutterSeconds = (aperture * aperture * 100) / (iso * (2 ** ev));
            
            // Find closest standard shutter speed
            let closestShutter = shutterSpeeds[0];
            let closestDiff = Infinity;
            
            for (const speed of shutterSpeeds) {
                let speedInSeconds;
                if (speed.includes('/')) {
                    const parts = speed.split('/');
                    speedInSeconds = parseFloat(parts[0]) / parseFloat(parts[1]);
                } else {
                    speedInSeconds = parseFloat(speed);
                }
                
                const diff = Math.abs(speedInSeconds - shutterSeconds);
                if (diff < closestDiff) {
                    closestDiff = diff;
                    closestShutter = speed;
                }
            }
            
            return {
                iso: iso,
                aperture,
                shutter_speed: closestShutter
            };
        }
    }

    /**
     * Start capture
     */
    startCapture() {
        if (!this.state.connected) {
            this.showToast('Error', 'Camera not connected', 'error');
            return;
        }
        
        if (this.state.currentBrackets.length === 0) {
            this.showToast('Error', 'No brackets defined', 'error');
            return;
        }
        
        // Create capture data
        const captureData = {
            capture_mode: this.state.captureMode,
            save_directory: this.elements.saveDirectory.value,
            brackets: this.state.currentBrackets,
            focus_stack: this.state.focusStack
        };
        
        // Disable start button, enable stop button
        this.elements.startCaptureBtn.disabled = true;
        this.elements.stopCaptureBtn.disabled = false;
        
        // Show progress section
        this.elements.captureProgress.style.display = 'block';
        
        // Reset progress
        this.elements.progressFill.style.width = '0%';
        this.elements.progressText.textContent = '0%';
        this.elements.progressBracket.textContent = '-';
        this.elements.progressFrame.textContent = '-';
        this.elements.progressCompleted.textContent = '0';
        this.elements.progressFailed.textContent = '0';
        
        console.log('DEBUG: Starting capture with data:', JSON.stringify(captureData));
        
        // Send to server
        fetch('/api/capture/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(captureData)
        })
            .then(response => {
                if (!response.ok) {
                    console.error('DEBUG: Capture API response not OK:', response.status, response.statusText);
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('DEBUG: Capture API response:', data);
                if (data.success) {
                    this.state.activeCapture = data.capture_id;
                    this.showToast('Capture Started', 'Capture sequence has started', 'success');
                    
                    // Switch to capture tab
                    this.switchTab('capture-control');
                } else {
                    const errorMsg = data.message || 'Failed to start capture';
                    console.error('DEBUG: Capture failed:', errorMsg, data);
                    this.showToast('Error', errorMsg, 'error');
                    this.elements.startCaptureBtn.disabled = false;
                    this.elements.stopCaptureBtn.disabled = true;
                }
            })
            .catch(error => {
                console.error('DEBUG: Error starting capture:', error);
                this.showToast('Error', `Failed to start capture: ${error.message}`, 'error');
                this.elements.startCaptureBtn.disabled = false;
                this.elements.stopCaptureBtn.disabled = true;
            });
    }
    /**
     * Stop capture
     */
    stopCapture() {
        if (!this.state.activeCapture) {
            return;
        }
        
        fetch(`/api/capture/${this.state.activeCapture}/stop`, {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showToast('Capture Stopped', 'Capture sequence has been stopped', 'info');
                } else {
                    this.showToast('Error', data.message || 'Failed to stop capture', 'error');
                }
            })
            .catch(error => {
                console.error('Error stopping capture:', error);
                this.showToast('Error', 'Failed to stop capture', 'error');
            });
    }
    
    /**
     * Create and add the Test Settings button
     */
    createTestSettingsButton() {
        // Create the button
        const testBtn = document.createElement('button');
        testBtn.id = 'test-settings-btn';
        testBtn.className = 'btn secondary';
        testBtn.textContent = 'Take Test Shots';
        
        // Store reference to the button
        this.elements.testSettingsBtn = testBtn;
        
        // Find the capture actions container and insert the button before the start button
        const captureActions = document.querySelector('.capture-actions');
        if (captureActions && this.elements.startCaptureBtn) {
            captureActions.insertBefore(testBtn, this.elements.startCaptureBtn);
        } else {
            console.error('DEBUG: Could not find capture actions container or start button');
        }
    }
    
    /**
     * Test all bracket settings
     */
    testAllSettings() {
        if (!this.state.connected) {
            this.showToast('Error', 'Camera not connected', 'error');
            return;
        }
        
        if (this.state.currentBrackets.length === 0) {
            this.showToast('Error', 'No brackets defined', 'error');
            return;
        }
        
        // Disable buttons during test
        this.elements.testSettingsBtn.disabled = true;
        this.elements.startCaptureBtn.disabled = true;
        
        // Show toast to indicate testing has started
        this.showToast('Testing', 'Taking test shots with each bracket setting...', 'info');
        
        console.log('DEBUG: Taking test shots with each bracket setting');
        
        // Create test data
        const testData = {
            brackets: this.state.currentBrackets,
            test_mode: true
        };
        
        // Send to server
        fetch('/api/capture/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        })
            .then(response => {
                if (!response.ok) {
                    console.error('DEBUG: Test API response not OK:', response.status, response.statusText);
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('DEBUG: Test API response:', data);
                
                // Re-enable buttons
                this.elements.testSettingsBtn.disabled = false;
                this.elements.startCaptureBtn.disabled = false;
                
                if (data.success) {
                    // All settings are valid
                    this.showToast('Test Complete', 'All test shots were successful', 'success');
                    
                    // Show detailed results if available
                    if (data.results && data.results.length > 0) {
                        console.log('DEBUG: Test results:', data.results);
                        
                        // Check if any warnings
                        const warnings = data.results.filter(r => r.warning);
                        if (warnings.length > 0) {
                            setTimeout(() => {
                                this.showToast('Warning', `${warnings.length} settings may cause issues`, 'warning');
                            }, 1000);
                        }
                    }
                } else {
                    // Some settings are invalid
                    const errorMsg = data.message || 'Some test shots failed';
                    console.error('DEBUG: Test failed:', errorMsg, data);
                    
                    // Show error toast
                    this.showToast('Test Failed', errorMsg, 'error');
                    
                    // Show detailed errors if available
                    if (data.results && data.results.length > 0) {
                        const errors = data.results.filter(r => r.error);
                        if (errors.length > 0) {
                            const firstError = errors[0];
                            setTimeout(() => {
                                this.showToast('Error Details',
                                    `Test shot failed for "${firstError.bracket_name}": ${firstError.error}`,
                                    'error');
                            }, 1000);
                        }
                    }
                }
            })
            .catch(error => {
                console.error('DEBUG: Error taking test shots:', error);
                this.showToast('Error', `Failed to take test shots: ${error.message}`, 'error');
                
                // Re-enable buttons
                this.elements.testSettingsBtn.disabled = false;
                this.elements.startCaptureBtn.disabled = false;
            });
    }

    /**
     * Update capture progress
     */
    updateCaptureProgress(data) {
        if (!data || !data.progress) {
            return;
        }
        
        const progress = data.progress;
        const totalFrames = progress.total_frames;
        const completedFrames = progress.completed_frames;
        const percent = totalFrames > 0 ? (completedFrames / totalFrames * 100) : 0;
        
        // Update progress bar
        this.elements.progressFill.style.width = `${percent}%`;
        this.elements.progressText.textContent = `${percent.toFixed(0)}%`;
        
        // Update progress details
        this.elements.progressBracket.textContent = `${progress.current_bracket}/${progress.total_brackets}`;
        this.elements.progressFrame.textContent = `${progress.current_frame}/${totalFrames}`;
        this.elements.progressCompleted.textContent = completedFrames;
        this.elements.progressFailed.textContent = progress.failed_frames;
        
        // Check if capture is complete
        if (data.status === 'completed') {
            this.elements.startCaptureBtn.disabled = false;
            this.elements.stopCaptureBtn.disabled = true;
            this.state.activeCapture = null;
            
            this.showToast('Capture Complete', 'Capture sequence has completed', 'success');
        } else if (data.status === 'error') {
            this.elements.startCaptureBtn.disabled = false;
            this.elements.stopCaptureBtn.disabled = true;
            this.state.activeCapture = null;
            
            this.showToast('Capture Error', 'Capture sequence encountered an error', 'error');
        }
    }

    /**
     * Close all modals
     */
    closeAllModals() {
        this.closeBracketModal();
        this.closeEvBracketsModal();
        
        // Close import preset modal
        const importModal = document.getElementById('import-preset-modal');
        if (importModal) {
            importModal.style.display = 'none';
        }
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon;
        switch (type) {
            case 'success':
                icon = 'check-circle';
                break;
            case 'error':
                icon = 'exclamation-circle';
                break;
            case 'warning':
                icon = 'exclamation-triangle';
                break;
            default:
                icon = 'info-circle';
        }
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        // Add to container
        this.elements.toastContainer.appendChild(toast);
        
        // Add close event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            const settings = JSON.parse(localStorage.getItem('exposure_tool_settings'));
            
            if (settings) {
                // Apply theme
                this.setTheme(settings.theme || 'dark', false);
                this.elements.themeSelect.value = settings.theme || 'dark';
                
                // Apply default save directory
                this.elements.defaultSaveDir.value = settings.defaultSaveDir || 'captures';
                
                // Apply auto connect setting
                this.elements.autoConnect.checked = settings.autoConnect !== false;
                
                // Auto connect if enabled
                if (settings.autoConnect !== false) {
                    setTimeout(() => {
                        this.connectCamera();
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        try {
            const settings = {
                theme: this.elements.themeSelect.value,
                defaultSaveDir: this.elements.defaultSaveDir.value,
                autoConnect: this.elements.autoConnect.checked
            };
            
            localStorage.setItem('exposure_tool_settings', JSON.stringify(settings));
            
            this.showToast('Settings Saved', 'Your settings have been saved', 'success');
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('Error', 'Failed to save settings', 'error');
        }
    }

    /**
     * Reset settings to defaults
     */
    resetSettings() {
        // Set default values
        this.elements.themeSelect.value = 'dark';
        this.elements.defaultSaveDir.value = 'captures';
        this.elements.autoConnect.checked = true;
        
        // Apply theme
        this.setTheme('dark');
        
        // Save settings
        this.saveSettings();
        
        this.showToast('Settings Reset', 'Settings have been reset to defaults', 'info');
    }

    /**
     * Set theme (dark, light)
     */
    setTheme(theme, save = true) {
        document.body.className = theme;
        this.state.theme = theme;
        
        if (save) {
            // Update localStorage if needed
            try {
                const settings = JSON.parse(localStorage.getItem('exposure_tool_settings')) || {};
                settings.theme = theme;
                localStorage.setItem('exposure_tool_settings', JSON.stringify(settings));
            } catch (error) {
                console.error('Error saving theme setting:', error);
            }
        }
    }

    /**
     * Create a new preset
     */
    newPreset() {
        // Clear current preset
        this.state.currentPreset = null;
        this.state.currentBrackets = [];
        
        // Clear form
        this.elements.presetName.value = '';
        this.elements.presetDescription.value = '';
        
        // Update UI
        this.renderBracketList();
        this.updateCaptureSummary();
        
        this.showToast('New Preset', 'Created a new empty preset', 'info');
    }

    /**
     * Import a preset from JSON
     */
    importPreset() {
        // Show the import modal
        const importModal = document.getElementById('import-preset-modal');
        importModal.style.display = 'flex';
        
        // Clear previous content
        const jsonTextarea = document.getElementById('import-json');
        const fileInput = document.getElementById('import-file');
        jsonTextarea.value = '';
        fileInput.value = '';
        
        // Set up file input handler
        fileInput.onchange = (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    jsonTextarea.value = e.target.result;
                };
                reader.readAsText(file);
            }
        };
        
        // Set up import button handler
        const importButton = document.getElementById('import-modal-import');
        const cancelButton = document.getElementById('import-modal-cancel');
        
        // Remove any existing event listeners
        const newImportButton = importButton.cloneNode(true);
        importButton.parentNode.replaceChild(newImportButton, importButton);
        
        const newCancelButton = cancelButton.cloneNode(true);
        cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
        
        // Add new event listeners
        newImportButton.addEventListener('click', () => {
            this.processImportedPreset(jsonTextarea.value);
            importModal.style.display = 'none';
        });
        
        newCancelButton.addEventListener('click', () => {
            importModal.style.display = 'none';
        });
    }
    
    /**
     * Process the imported preset JSON
     */
    processImportedPreset(jsonString) {
        try {
            // Parse the JSON
            const preset = JSON.parse(jsonString);
            
            // Validate the preset
            if (!preset.name || !Array.isArray(preset.brackets)) {
                throw new Error('Invalid preset format: missing name or brackets array');
            }
            
            // Update state
            this.state.currentPreset = null; // This is a new preset, not yet saved
            this.state.currentBrackets = preset.brackets || [];
            
            if (preset.focus_stack) {
                this.state.focusStack = preset.focus_stack;
            }
            
            // Preserve folder information if present
            if (preset.folder) {
                // Store folder info to be used when saving
                this.state.importedFolder = preset.folder;
            }
            
            // Update UI
            this.elements.presetName.value = preset.name;
            this.elements.presetDescription.value = preset.description || '';
            this.elements.focusStackEnabled.checked = this.state.focusStack.enabled;
            this.elements.focusSteps.value = this.state.focusStack.steps;
            this.elements.focusStepSize.value = this.state.focusStack.step_size;
            this.elements.focusSpeed.value = this.state.focusStack.speed || 2;
            this.elements.focusDirection.value = this.state.focusStack.direction || 'near';
            
            // Update focus stack options visibility
            this.updateFocusStackOptions();
            
            // Render brackets
            this.renderBracketList();
            
            // Update capture summary
            this.updateCaptureSummary();
            
            // Show toast
            this.showToast('Success', `Imported preset: ${preset.name}`, 'success');
            
            // Save the imported preset to the server
            this.savePreset();
            
        } catch (error) {
            console.error('Error importing preset:', error);
            this.showToast('Error', `Failed to import preset: ${error.message}`, 'error');
        }
    }

    /**
     * Save the current preset
     */
    savePreset() {
        console.log('DEBUG: Saving preset');
        
        // Check if form elements exist
        if (!this.elements.presetName || !this.elements.presetDescription) {
            console.error('DEBUG: Preset form elements not found', {
                presetName: !!this.elements.presetName,
                presetDescription: !!this.elements.presetDescription
            });
            return;
        }
        
        const name = this.elements.presetName.value;
        const description = this.elements.presetDescription.value;
        
        if (!name) {
            this.showToast('Error', 'Please enter a preset name', 'error');
            return;
        }
        
        const preset = {
            name,
            description,
            brackets: this.state.currentBrackets,
            focus_stack: this.state.focusStack
        };
        
        // Preserve folder information if this is an existing preset
        if (this.state.currentPreset) {
            const existingPreset = this.state.presets.find(p => p.id === this.state.currentPreset);
            if (existingPreset && existingPreset.folder) {
                preset.folder = existingPreset.folder;
            }
        }
        // Or use folder information from imported preset
        else if (this.state.importedFolder) {
            preset.folder = this.state.importedFolder;
            // Clear the imported folder after using it
            delete this.state.importedFolder;
        }
        
        // Send to server
        console.log('DEBUG: Sending preset to server', preset);
        fetch('/api/presets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(preset)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.state.currentPreset = data.preset_id;
                    this.showToast('Success', 'Preset saved successfully', 'success');
                    
                    // Refresh presets list
                    this.loadPresets();
                } else {
                    this.showToast('Error', data.message || 'Failed to save preset', 'error');
                }
            })
            .catch(error => {
                console.error('Error saving preset:', error);
                this.showToast('Error', 'Failed to save preset', 'error');
            });
    }

    /**
     * Export the current preset to a JSON file
     */
    exportPreset() {
        // Check if there's a current preset
        if (this.state.currentBrackets.length === 0) {
            this.showToast('Error', 'No brackets defined to export', 'error');
            return;
        }
        
        // Create the preset object
        const preset = {
            name: this.elements.presetName.value || 'Exported Preset',
            description: this.elements.presetDescription.value || '',
            brackets: this.state.currentBrackets,
            focus_stack: this.state.focusStack,
            exported_at: new Date().toISOString()
        };
        
        // Convert to JSON string
        const presetJson = JSON.stringify(preset, null, 2);
        
        // Create a blob and download link
        const blob = new Blob([presetJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create a temporary link and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = `${preset.name.replace(/\s+/g, '_')}_preset.json`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
        this.showToast('Success', 'Preset exported successfully', 'success');
    }
}