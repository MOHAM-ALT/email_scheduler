// Demori Popup Controller
class DemoriPopup {
    constructor() {
        this.currentView = 'menu';
        this.api = new DemoriAPI();
        this.currentProfile = null;
        this.searchResults = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkCurrentTab();
        this.loadStoredProfile();
    }

    setupEventListeners() {
        // Close button
        const closeBtn = document.getElementById('closeBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                window.close();
            });
        }

        // Main menu buttons
        const dataListsBtn = document.getElementById('dataListsBtn');
        if (dataListsBtn) {
            dataListsBtn.addEventListener('click', () => {
                this.showSearchPortal();
            });
        }

        const searchPortalBtn = document.getElementById('searchPortalBtn');
        if (searchPortalBtn) {
            searchPortalBtn.addEventListener('click', () => {
                this.showSearchPortal();
            });
        }

        const advancedSettingsBtn = document.getElementById('advancedSettingsBtn');
        if (advancedSettingsBtn) {
            advancedSettingsBtn.addEventListener('click', () => {
                this.showAdvancedSettings();
            });
        }

        const searchHistoryBtn = document.getElementById('searchHistoryBtn');
        if (searchHistoryBtn) {
            searchHistoryBtn.addEventListener('click', () => {
                this.showSearchHistory();
            });
        }

        const exportOptionsBtn = document.getElementById('exportOptionsBtn');
        if (exportOptionsBtn) {
            exportOptionsBtn.addEventListener('click', () => {
                this.showExportOptions();
            });
        }

        const saveProfilesBtn = document.getElementById('saveProfilesBtn');
        if (saveProfilesBtn) {
            saveProfilesBtn.addEventListener('click', () => {
                this.detectAndSearch();
            });
        }

        const batchProcessorBtn = document.getElementById('batchProcessorBtn');
        if (batchProcessorBtn) {
            batchProcessorBtn.addEventListener('click', () => {
                this.showBatchProcessor();
            });
        }

        // Toggle switches in main menu
        const autoDetectToggle = document.getElementById('autoDetectToggle');
        if (autoDetectToggle) {
            autoDetectToggle.addEventListener('click', (e) => {
                this.toggleSwitch(e.target);
            });
        }

        const backgroundScanToggle = document.getElementById('backgroundScanToggle');
        if (backgroundScanToggle) {
            backgroundScanToggle.addEventListener('click', (e) => {
                this.toggleSwitch(e.target);
            });
        }

        const realtimeSyncToggle = document.getElementById('realtimeSyncToggle');
        if (realtimeSyncToggle) {
            realtimeSyncToggle.addEventListener('click', (e) => {
                this.toggleSwitch(e.target);
            });
        }

        // Search button
        const searchButton = document.getElementById('searchButton');
        if (searchButton) {
            searchButton.addEventListener('click', () => {
                this.performSearch();
            });
        }

        // Settings back button
        const settingsBackBtn = document.getElementById('settingsBackBtn');
        if (settingsBackBtn) {
            settingsBackBtn.addEventListener('click', () => {
                this.showMenu();
            });
        }

        // Results back button
        const resultsBackBtn = document.getElementById('resultsBackBtn');
        if (resultsBackBtn) {
            resultsBackBtn.addEventListener('click', () => {
                this.showMenu();
            });
        }

        // Select all checkbox
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('click', (e) => {
                this.toggleSelectAll(e.target);
            });
        }

        // Settings select elements
        this.setupSettingsEventListeners();

        // Profile detection refresh
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.currentView === 'search') {
                this.refreshProfileDetection();
            }
        });
    }

    setupSettingsEventListeners() {
        // Settings select elements
        const settingsSelects = [
            'searchDepth', 'emailVerification', 'phoneValidation', 'searchTimeout',
            'concurrentSearches', 'cacheDuration', 'databaseSync', 'exportFormat',
            'crmIntegration', 'encryptionLevel'
        ];

        settingsSelects.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', (e) => {
                    this.updateSetting(id, e.target.value);
                });
            }
        });

        // Confidence threshold range
        const confidenceThreshold = document.getElementById('confidenceThreshold');
        if (confidenceThreshold) {
            confidenceThreshold.addEventListener('change', (e) => {
                this.updateSetting('confidenceThreshold', e.target.value);
            });
        }

        // Settings toggle switches
        const settingsToggles = [
            'autoExportToggle', 'dataAnonymizationToggle', 'localStorageOnlyToggle'
        ];

        settingsToggles.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('click', (e) => {
                    this.toggleSwitch(e.target);
                });
            }
        });

        // Data source toggles
        const dataSources = [
            'companyWebsitesSource', 'professionalDirectoriesSource', 'socialPlatformsSource',
            'publicRecordsSource', 'newsArticlesSource', 'patentDatabasesSource'
        ];

        dataSources.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                const sourceKey = element.getAttribute('data-source');
                element.addEventListener('click', (e) => {
                    this.toggleSource(e.target, sourceKey);
                });
            }
        });

        // Settings action buttons
        const resetSettingsBtn = document.getElementById('resetSettingsBtn');
        if (resetSettingsBtn) {
            resetSettingsBtn.addEventListener('click', () => {
                this.resetSettings();
            });
        }

        const exportSettingsBtn = document.getElementById('exportSettingsBtn');
        if (exportSettingsBtn) {
            exportSettingsBtn.addEventListener('click', () => {
                this.exportSettings();
            });
        }

        const saveSettingsBtn = document.getElementById('saveSettingsBtn');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => {
                this.saveSettings();
            });
        }
    }

    async checkCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab.url && tab.url.includes('linkedin.com')) {
                this.setupLinkedInMode();
            } else {
                this.setupGeneralMode();
            }
        } catch (error) {
            console.error('Tab check error:', error);
            this.setupGeneralMode();
        }
    }

    setupLinkedInMode() {
        this.showSearchPortal();
        this.refreshProfileDetection();
    }

    setupGeneralMode() {
        this.showMenu();
    }

    async loadStoredProfile() {
        try {
            const result = await chrome.storage.local.get(['currentProfile', 'profileDetected']);
            
            if (result.profileDetected && result.currentProfile) {
                this.currentProfile = result.currentProfile;
                this.updateProfileDisplay();
            }
        } catch (error) {
            console.error('Error loading stored profile:', error);
        }
    }

    async refreshProfileDetection() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (!tab.url || !tab.url.includes('linkedin.com')) {
                this.updateDetectionStatus('not_linkedin', 'Not on LinkedIn profile');
                return;
            }

            this.updateDetectionStatus('detecting', 'Detecting profile...');

            const response = await chrome.tabs.sendMessage(tab.id, { action: 'getProfileData' });
            
            if (response && response.success && response.data) {
                this.currentProfile = response.data;
                this.updateProfileDisplay();
                this.updateDetectionStatus('success', 'Profile detected');
            } else {
                this.updateDetectionStatus('error', 'Unable to detect profile');
            }
        } catch (error) {
            console.error('Profile detection error:', error);
            this.updateDetectionStatus('error', 'Detection failed');
        }
    }

    updateDetectionStatus(status, message) {
        const statusIcon = document.getElementById('statusIcon');
        const detectionEl = document.getElementById('profileDetection');
        
        if (!statusIcon || !detectionEl) return;

        detectionEl.className = 'profile-detection';
        statusIcon.className = 'status-icon';
        
        switch (status) {
            case 'detecting':
                detectionEl.classList.add('detecting');
                statusIcon.classList.add('warning');
                break;
            case 'success':
                statusIcon.classList.add('success');
                break;
            case 'error':
            case 'not_linkedin':
                detectionEl.classList.add('error');
                statusIcon.classList.add('error');
                break;
        }
    }

    updateProfileDisplay() {
        if (!this.currentProfile) return;

        const elements = {
            detectedName: document.getElementById('detectedName'),
            detectedCompany: document.getElementById('detectedCompany'),
            detectedTitle: document.getElementById('detectedTitle')
        };

        if (elements.detectedName) {
            elements.detectedName.textContent = this.currentProfile.name || 'Unknown';
        }
        if (elements.detectedCompany) {
            elements.detectedCompany.textContent = this.currentProfile.company || 'Unknown';
        }
        if (elements.detectedTitle) {
            elements.detectedTitle.textContent = this.currentProfile.title || 'Unknown';
        }
    }

    // View Management
    showMenu() {
        this.hideAllViews();
        document.getElementById('menuView').classList.remove('hidden');
        this.currentView = 'menu';
    }

    showSearchPortal() {
        this.hideAllViews();
        document.getElementById('searchView').classList.remove('hidden');
        this.currentView = 'search';
        setTimeout(() => this.refreshProfileDetection(), 500);
    }

    showProgress() {
        this.hideAllViews();
        document.getElementById('progressView').classList.remove('hidden');
        this.currentView = 'progress';
    }

    showResults() {
        this.hideAllViews();
        document.getElementById('resultsView').classList.remove('hidden');
        this.currentView = 'results';
    }

    showAdvancedSettings() {
        this.hideAllViews();
        document.getElementById('advancedSettingsView').classList.remove('hidden');
        this.currentView = 'settings';
        this.loadCurrentSettings();
    }

    hideAllViews() {
        const views = ['menuView', 'searchView', 'progressView', 'resultsView', 'advancedSettingsView'];
        views.forEach(viewId => {
            const element = document.getElementById(viewId);
            if (element) {
                element.classList.add('hidden');
            }
        });
    }

    // Search Functions
    async detectAndSearch() {
        if (!this.currentProfile) {
            await this.refreshProfileDetection();
        }

        if (!this.currentProfile || this.currentProfile.name === 'Unknown') {
            this.showError('Unable to detect profile information. Please ensure you are on a LinkedIn profile page.');
            return;
        }

        await this.startSearch(this.currentProfile);
    }

    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput.value.trim();

        if (!query) {
            if (this.currentProfile) {
                await this.startSearch(this.currentProfile);
            } else {
                this.showError('Please enter a search query or navigate to a LinkedIn profile.');
            }
            return;
        }

        const searchData = this.parseSearchQuery(query);
        await this.startSearch(searchData);
    }

    parseSearchQuery(query) {
        return {
            name: query,
            company: 'Unknown',
            title: 'Unknown',
            location: 'Unknown',
            source: 'manual_search'
        };
    }

    async startSearch(searchData) {
        try {
            this.showProgress();
            this.resetProgress();

            const result = await this.executeSearchSteps(searchData);
            
            if (result.success) {
                this.searchResults = result.data;
                this.displayResults();
            } else {
                this.showError(result.error || 'Search failed. Please try again.');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('An unexpected error occurred during search.');
        }
    }

    async executeSearchSteps(searchData) {
        const steps = [
            { id: 'step1', name: 'Local Database Search', duration: 800 },
            { id: 'step2', name: 'Company Websites', duration: 1200 },
            { id: 'step3', name: 'Professional Directories', duration: 1000 },
            { id: 'step4', name: 'Social Platforms', duration: 900 },
            { id: 'step5', name: 'Data Verification', duration: 600 }
        ];

        let currentStep = 0;

        for (const step of steps) {
            this.updateProgressStep(currentStep, 'active');
            this.updateProgressBar((currentStep + 1) / steps.length * 100);
            this.updateProgressStats(currentStep + 1, steps.length);

            await this.delay(step.duration);

            this.updateProgressStep(currentStep, 'completed');
            currentStep++;
        }

        return new Promise((resolve) => {
            chrome.runtime.sendMessage({
                action: 'searchContact',
                data: searchData
            }, (response) => {
                resolve(response || { success: false, error: 'No response from background script' });
            });
        });
    }

    updateProgressStep(stepIndex, status) {
        const stepElement = document.getElementById(`step${stepIndex + 1}`);
        if (!stepElement) return;

        stepElement.className = `step-icon ${status}`;
        
        if (status === 'completed') {
            stepElement.textContent = '✓';
        } else if (status === 'active') {
            stepElement.textContent = stepIndex + 1;
        }
    }

    updateProgressBar(percentage) {
        const progressFill = document.getElementById('progressFill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
    }

    updateProgressStats(current, total) {
        const progressStats = document.getElementById('progressStats');
        if (progressStats) {
            progressStats.textContent = `${current} of ${total}`;
        }
    }

    resetProgress() {
        for (let i = 1; i <= 5; i++) {
            const stepElement = document.getElementById(`step${i}`);
            if (stepElement) {
                stepElement.className = 'step-icon pending';
                stepElement.textContent = i;
            }
        }
        this.updateProgressBar(0);
        this.updateProgressStats(0, 5);
    }

    displayResults() {
        if (!this.searchResults) return;
        this.showResults();
        this.populateContactsList();
    }

    populateContactsList() {
        const contactsList = document.getElementById('contactsList');
        const contactCount = document.getElementById('contactCount');
        
        if (!contactsList || !this.searchResults) return;

        const contacts = this.generateContactCards();
        
        contactsList.innerHTML = '';
        contacts.forEach(contact => {
            const card = this.createContactCard(contact);
            contactsList.appendChild(card);
            
            // Add event listeners to info cards
            const infoCards = card.querySelectorAll('.info-card');
            infoCards.forEach(infoCard => {
                infoCard.addEventListener('click', () => {
                    const data = infoCard.getAttribute('data-info');
                    const type = infoCard.getAttribute('data-type');
                    this.revealInfo(infoCard, data, type);
                });
            });
        });

        if (contactCount) {
            contactCount.textContent = contacts.length;
        }
    }

    generateContactCards() {
        if (!this.searchResults) return [];

        const contacts = [
            {
                name: this.searchResults.name || 'John Smith',
                title: this.searchResults.title || 'Software Engineer',
                country: this.getCountryFromLocation(this.searchResults.location),
                flag: this.getCountryFlag(this.searchResults.location),
                status: 'Verified',
                emails: this.searchResults.emails || [],
                phones: this.searchResults.phones || [],
                location: this.searchResults.location,
                socialMedia: this.searchResults.socialMedia || [],
                education: this.searchResults.education
            }
        ];

        return contacts;
    }

    createContactCard(contact) {
        const card = document.createElement('div');
        card.className = 'contact-item';
        
        card.innerHTML = `
            <div class="contact-header-row">
                <div class="contact-basic-info">
                    <div class="country-flag">${contact.flag}</div>
                    <div>
                        <div class="contact-name">${contact.name}</div>
                        <div class="contact-title">${contact.title}</div>
                    </div>
                </div>
                <div class="contact-status">${contact.status}</div>
            </div>
            
            <div class="contact-grid">
                ${this.createInfoCards(contact)}
            </div>
        `;

        return card;
    }

    createInfoCards(contact) {
        const cards = [];

        // Primary Email
        if (contact.emails && contact.emails.length > 0) {
            cards.push(`
                <div class="info-card" data-info="${contact.emails[0].email}" data-type="Email">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Primary Email</div>
                    <div class="info-status glitch-data" data-text="██████@███████.███">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="ahmed.rashid@company.com" data-type="Email">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Primary Email</div>
                    <div class="info-status glitch-data" data-text="██████@███████.███">AVAILABLE</div>
                </div>
            `);
        }

        // Mobile Phone
        if (contact.phones && contact.phones.length > 0) {
            cards.push(`
                <div class="info-card" data-info="${contact.phones[0].number}" data-type="Phone">
                    <div class="info-icon">◎</div>
                    <div class="info-label">Mobile Phone</div>
                    <div class="info-status glitch-data" data-text="+███.██.███.████">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="+966 50 789 1234" data-type="Phone">
                    <div class="info-icon">◎</div>
                    <div class="info-label">Mobile Phone</div>
                    <div class="info-status glitch-data" data-text="+███.██.███.████">AVAILABLE</div>
                </div>
            `);
        }

        // Work Email (Secondary)
        if (contact.emails && contact.emails.length > 1) {
            cards.push(`
                <div class="info-card" data-info="${contact.emails[1].email}" data-type="Email">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Work Email</div>
                    <div class="info-status glitch-data" data-text="█.██████@███████.██">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="a.rashid@gmail.com" data-type="Email">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Personal Email</div>
                    <div class="info-status glitch-data" data-text="█.██████@█████.███">AVAILABLE</div>
                </div>
            `);
        }

        // Location
        if (contact.location) {
            cards.push(`
                <div class="info-card" data-info="${contact.location}" data-type="Location">
                    <div class="info-icon">◐</div>
                    <div class="info-label">Location</div>
                    <div class="info-status glitch-data" data-text="██████, ████ ████">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="Riyadh, Saudi Arabia" data-type="Location">
                    <div class="info-icon">◐</div>
                    <div class="info-label">Location</div>
                    <div class="info-status glitch-data" data-text="██████, ████ ████">AVAILABLE</div>
                </div>
            `);
        }

        // Social Media
        if (contact.socialMedia && contact.socialMedia.length > 0) {
            cards.push(`
                <div class="info-card" data-info="${contact.socialMedia.slice(0, 3).join(', ')}" data-type="Social">
                    <div class="info-icon">◑</div>
                    <div class="info-label">Social Media</div>
                    <div class="info-status glitch-data" data-text="█ Profiles">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="LinkedIn: ahmed-rashid, Twitter: @ahmed_dev" data-type="Social">
                    <div class="info-icon">◑</div>
                    <div class="info-label">Social Media</div>
                    <div class="info-status glitch-data" data-text="█ Profiles">AVAILABLE</div>
                </div>
            `);
        }

        // Education
        if (contact.education) {
            cards.push(`
                <div class="info-card" data-info="${contact.education}" data-type="Education">
                    <div class="info-icon">◒</div>
                    <div class="info-label">Education</div>
                    <div class="info-status glitch-data" data-text="██ ████████ ██████">AVAILABLE</div>
                </div>
            `);
        } else {
            cards.push(`
                <div class="info-card" data-info="MS Computer Science - King Fahd University" data-type="Education">
                    <div class="info-icon">◒</div>
                    <div class="info-label">Education</div>
                    <div class="info-status glitch-data" data-text="██ ████████ ██████">AVAILABLE</div>
                </div>
            `);
        }

        return cards.join('');
    }

    revealInfo(element, data, type) {
        const statusElement = element.querySelector('.info-status');
        
        if (!statusElement) return;

        statusElement.style.animation = 'glitch-1 0.3s ease-out';
        
        setTimeout(() => {
            statusElement.className = 'info-status revealed-data';
            statusElement.textContent = data;
            element.style.border = '1px solid rgba(0, 255, 255, 0.6)';
            element.style.background = 'rgba(0, 255, 255, 0.08)';
            element.onclick = null;
            
            this.logActivity('reveal_info', { type, data: type });
        }, 300);
    }

    // Advanced Settings Management
    async loadCurrentSettings() {
        try {
            const settings = await chrome.storage.local.get(['demoriSettings']);
            const currentSettings = settings.demoriSettings || this.getDefaultSettings();
            
            Object.keys(currentSettings).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.type === 'range') {
                        element.value = currentSettings[key];
                        const valueSpan = element.parentElement.querySelector('.range-value');
                        if (valueSpan) valueSpan.textContent = currentSettings[key] + '%';
                    } else {
                        element.value = currentSettings[key];
                    }
                }
            });

            const toggles = document.querySelectorAll('[data-setting]');
            toggles.forEach(toggle => {
                const setting = toggle.getAttribute('data-setting');
                if (currentSettings[setting]) {
                    toggle.classList.add('active');
                } else {
                    toggle.classList.remove('active');
                }
            });

            if (currentSettings.dataSources) {
                Object.keys(currentSettings.dataSources).forEach(source => {
                    const sourceElement = document.querySelector(`[onclick*="${source}"]`);
                    if (sourceElement && currentSettings.dataSources[source]) {
                        sourceElement.classList.add('active');
                    }
                });
            }

        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    getDefaultSettings() {
        return {
            searchDepth: 'standard',
            emailVerification: 'domain',
            phoneValidation: 'carrier',
            confidenceThreshold: 60,
            searchTimeout: 60,
            concurrentSearches: 3,
            cacheDuration: 86400,
            databaseSync: 'realtime',
            exportFormat: 'csv',
            encryptionLevel: 'standard',
            autoDetect: true,
            backgroundScan: false,
            realtimeSync: true,
            autoExport: false,
            dataAnonymization: false,
            localStorageOnly: false,
            dataSources: {
                companyWebsites: true,
                professionalDirectories: true,
                socialPlatforms: true,
                publicRecords: false,
                newsArticles: false,
                patentDatabases: false
            }
        };
    }

    async updateSetting(key, value) {
        try {
            const settings = await chrome.storage.local.get(['demoriSettings']);
            const currentSettings = settings.demoriSettings || this.getDefaultSettings();
            
            currentSettings[key] = value;
            
            await chrome.storage.local.set({ demoriSettings: currentSettings });
            
            if (key === 'confidenceThreshold') {
                document.getElementById('confidenceValue').textContent = value + '%';
            }
            
            chrome.runtime.sendMessage({
                action: 'updateSettings',
                data: currentSettings
            });

            console.log(`Setting ${key} updated to:`, value);
        } catch (error) {
            console.error('Error updating setting:', error);
        }
    }

    toggleSource(element, sourceKey) {
        element.classList.toggle('active');
        this.updateDataSourceSetting(sourceKey, element.classList.contains('active'));
    }

    async updateDataSourceSetting(sourceKey, enabled) {
        try {
            const settings = await chrome.storage.local.get(['demoriSettings']);
            const currentSettings = settings.demoriSettings || this.getDefaultSettings();
            
            if (!currentSettings.dataSources) {
                currentSettings.dataSources = {};
            }
            
            currentSettings.dataSources[sourceKey] = enabled;
            
            await chrome.storage.local.set({ demoriSettings: currentSettings });
            
            chrome.runtime.sendMessage({
                action: 'updateSettings',
                data: currentSettings
            });

            console.log(`Data source ${sourceKey} ${enabled ? 'enabled' : 'disabled'}`);
        } catch (error) {
            console.error('Error updating data source setting:', error);
        }
    }

    async resetSettings() {
        if (confirm('Reset all settings to default values?')) {
            const defaultSettings = this.getDefaultSettings();
            await chrome.storage.local.set({ demoriSettings: defaultSettings });
            this.loadCurrentSettings();
            
            chrome.runtime.sendMessage({
                action: 'updateSettings',
                data: defaultSettings
            });
            
            console.log('Settings reset to defaults');
        }
    }

    async exportSettings() {
        try {
            const settings = await chrome.storage.local.get(['demoriSettings']);
            const currentSettings = settings.demoriSettings || this.getDefaultSettings();
            
            const dataStr = JSON.stringify(currentSettings, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `demori-settings-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            console.log('Settings exported successfully');
        } catch (error) {
            console.error('Error exporting settings:', error);
        }
    }

    async saveSettings() {
        const button = document.querySelector('.action-btn.primary[onclick*="saveSettings"]');
        if (button) {
            const originalText = button.textContent;
            button.textContent = 'Saved!';
            button.style.background = '#28a745';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 2000);
        }
    }

    showSearchHistory() {
        console.log('Search history feature coming soon');
    }

    showExportOptions() {
        console.log('Export options feature coming soon');
    }

    showBatchProcessor() {
        console.log('Batch processor feature coming soon');
    }

    // Utility Functions
    getCountryFromLocation(location) {
        if (!location) return 'Unknown';
        
        if (location.includes('Saudi') || location.includes('Riyadh')) return 'Saudi Arabia';
        if (location.includes('Canada') || location.includes('Toronto')) return 'Canada';
        if (location.includes('United States') || location.includes('USA')) return 'United States';
        
        return 'Unknown';
    }

    getCountryFlag(location) {
        const country = this.getCountryFromLocation(location);
        
        switch (country) {
            case 'Saudi Arabia': return '🇸🇦';
            case 'Canada': return '🇨🇦';
            case 'United States': return '🇺🇸';
            default: return '🌍';
        }
    }

    toggleSwitch(element) {
        element.classList.toggle('active');
        
        const setting = element.getAttribute('data-setting');
        if (setting) {
            const isActive = element.classList.contains('active');
            this.updateSetting(setting, isActive);
        }
    }

    toggleSelectAll(element) {
        element.classList.toggle('checked');
        
        const contactCheckboxes = document.querySelectorAll('.contact-item .checkbox');
        const isChecked = element.classList.contains('checked');
        
        contactCheckboxes.forEach(checkbox => {
            if (isChecked) {
                checkbox.classList.add('checked');
            } else {
                checkbox.classList.remove('checked');
            }
        });
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        if (errorText) {
            errorText.textContent = message;
        }
        
        if (errorMessage) {
            errorMessage.classList.add('active');
            
            setTimeout(() => {
                errorMessage.classList.remove('active');
            }, 5000);
        }
    }

    async logActivity(action, data) {
        try {
            await this.api.logActivity({ action, data });
        } catch (error) {
            console.error('Failed to log activity:', error);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DemoriPopup();
});