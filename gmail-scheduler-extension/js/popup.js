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
        document.getElementById('closeBtn').addEventListener('click', () => {
            window.close();
        });

        // Profile detection refresh
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.currentView === 'search') {
                this.refreshProfileDetection();
            }
        });
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
        // Show profile detection automatically if on LinkedIn
        this.showSearchPortal();
        this.refreshProfileDetection();
    }

    setupGeneralMode() {
        // Show regular menu for non-LinkedIn pages
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

            // Request profile data from content script
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

        // Reset classes
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
        
        // Auto-refresh detection when showing search portal
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

    hideAllViews() {
        const views = ['menuView', 'searchView', 'progressView', 'resultsView'];
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

        // Parse search query
        const searchData = this.parseSearchQuery(query);
        await this.startSearch(searchData);
    }

    parseSearchQuery(query) {
        // Simple parsing - could be enhanced
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

            // Start the search process
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

            // Simulate processing time
            await this.delay(step.duration);

            this.updateProgressStep(currentStep, 'completed');
            currentStep++;
        }

        // Perform actual search via background script
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

        // Generate mock results based on search data
        const contacts = this.generateContactCards();
        
        contactsList.innerHTML = '';
        contacts.forEach(contact => {
            contactsList.appendChild(this.createContactCard(contact));
        });

        if (contactCount) {
            contactCount.textContent = contacts.length;
        }
    }

    generateContactCards() {
        if (!this.searchResults) return [];

        // Generate realistic contact data
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
        if (contact.emails.length > 0) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.emails[0].email}', 'Email')">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Primary Email</div>
                    <div class="info-status glitch-data" data-text="██████@███████.███">AVAILABLE</div>
                </div>
            `);
        }

        // Phone
        if (contact.phones.length > 0) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.phones[0].number}', 'Phone')">
                    <div class="info-icon">◎</div>
                    <div class="info-label">Mobile Phone</div>
                    <div class="info-status glitch-data" data-text="+███.██.███.████">AVAILABLE</div>
                </div>
            `);
        }

        // Work Email
        if (contact.emails.length > 1) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.emails[1].email}', 'Email')">
                    <div class="info-icon">◈</div>
                    <div class="info-label">Work Email</div>
                    <div class="info-status glitch-data" data-text="█.██████@███████.██">AVAILABLE</div>
                </div>
            `);
        }

        // Location
        if (contact.location) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.location}', 'Location')">
                    <div class="info-icon">◐</div>
                    <div class="info-label">Location</div>
                    <div class="info-status glitch-data" data-text="██████, ████ ████">AVAILABLE</div>
                </div>
            `);
        }

        // Social Media
        if (contact.socialMedia.length > 0) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.socialMedia.join(', ')}', 'Social')">
                    <div class="info-icon">◑</div>
                    <div class="info-label">Social Media</div>
                    <div class="info-status glitch-data" data-text="█ Profiles">AVAILABLE</div>
                </div>
            `);
        }

        // Education
        if (contact.education) {
            cards.push(`
                <div class="info-card" onclick="DemoriPopup.revealInfo(this, '${contact.education}', 'Education')">
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

        // Add glitch effect before revealing
        statusElement.style.animation = 'glitch-1 0.3s ease-out';
        
        setTimeout(() => {
            statusElement.className = 'info-status revealed-data';
            statusElement.textContent = data;
            element.style.border = '1px solid rgba(0, 255, 255, 0.6)';
            element.style.background = 'rgba(0, 255, 255, 0.08)';
            element.onclick = null; // Disable further clicks
            
            // Log activity
            this.logActivity('reveal_info', { type, data: type }); // Don't log actual data for privacy
        }, 300);
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
    }

    toggleSelectAll(element) {
        element.classList.toggle('checked');
        
        // Toggle all contact checkboxes
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
            
            // Hide after 5 seconds
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
    window.DemoriPopup = new DemoriPopup();
});

// Export for global access
window.DemoriPopup = DemoriPopup;