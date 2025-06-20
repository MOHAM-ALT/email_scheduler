// DEMORI Contact Finder Pro - Popup Interface
class DemoriPopup {
    constructor() {
        this.currentSection = 'dashboard';
        this.userCredits = 0;
        this.dailyUsage = 0;
        this.searchHistory = [];
        this.settings = {};
        
        this.init();
    }

    async init() {
        console.log('🚀 DEMORI Popup Interface Loaded');
        
        await this.loadUserData();
        this.setupEventListeners();
        this.setupNavigation();
        this.updateUI();
        
        // Check if first time user
        await this.checkFirstTimeUser();
        
        // Start real-time updates
        this.startRealTimeUpdates();
    }

    async loadUserData() {
        try {
            // Get user data from storage
            const storage = await chrome.storage.local.get([
                'userCredits', 'dailyUsage', 'searchHistory', 'settings', 
                'isFirstTime', 'userPlan', 'lastUsageReset'
            ]);

            this.userCredits = storage.userCredits || 10; // Default free credits
            this.dailyUsage = storage.dailyUsage || 0;
            this.searchHistory = storage.searchHistory || [];
            this.settings = storage.settings || {
                autoSearch: true,
                showNotifications: true,
                saveHistory: true
            };
            this.isFirstTime = storage.isFirstTime || false;
            this.userPlan = storage.userPlan || 'Free Trial';

            // Check if daily usage needs reset
            await this.checkDailyReset(storage.lastUsageReset);

        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    }

    async checkDailyReset(lastReset) {
        const today = new Date().toDateString();
        if (lastReset !== today) {
            this.dailyUsage = 0;
            await chrome.storage.local.set({
                dailyUsage: 0,
                lastUsageReset: today
            });
        }
    }

    setupEventListeners() {
        // Welcome section
        document.getElementById('start-trial-btn')?.addEventListener('click', () => {
            this.startTrial();
        });

        // Navigation buttons
        document.getElementById('open-linkedin-btn')?.addEventListener('click', () => {
            this.openLinkedIn();
        });

        document.getElementById('view-history-btn')?.addEventListener('click', () => {
            this.showSearchHistory();
        });

        document.getElementById('export-contacts-btn')?.addEventListener('click', () => {
            this.exportContacts();
        });

        // Settings
        document.getElementById('auto-search')?.addEventListener('change', (e) => {
            this.updateSetting('autoSearch', e.target.checked);
        });

        document.getElementById('show-notifications')?.addEventListener('change', (e) => {
            this.updateSetting('showNotifications', e.target.checked);
        });

        document.getElementById('save-history')?.addEventListener('change', (e) => {
            this.updateSetting('saveHistory', e.target.checked);
        });

        // Account actions
        document.getElementById('upgrade-plan-btn')?.addEventListener('click', () => {
            this.showUpgradeSection();
        });

        document.getElementById('login-btn')?.addEventListener('click', () => {
            this.openLoginPage();
        });

        document.getElementById('clear-data-btn')?.addEventListener('click', () => {
            this.clearAllData();
        });

        document.getElementById('export-data-btn')?.addEventListener('click', () => {
            this.exportUserData();
        });

        // Upgrade plan buttons
        document.querySelectorAll('.upgrade-card .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const planName = e.target.closest('.upgrade-card').querySelector('h3').textContent;
                this.selectPlan(planName);
            });
        });
    }

    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            targetSection.classList.add('fade-in');
        }

        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.updateDashboardStats();
                await this.loadRecentSearches();
                break;
            case 'settings':
                this.loadSettingsValues();
                break;
            case 'upgrade':
                this.updateUpgradeInfo();
                break;
        }
    }

    async updateUI() {
        // Update header stats
        document.getElementById('credits-count').textContent = `Credits: ${this.userCredits}`;
        document.getElementById('daily-usage').textContent = `Today: ${this.dailyUsage}/100`;

        // Update account info in settings
        document.getElementById('user-plan').textContent = this.userPlan;
        document.getElementById('account-credits').textContent = this.userCredits;

        // Update LinkedIn status
        await this.updateLinkedInStatus();
    }

    async updateLinkedInStatus() {
        try {
            // Check if user is currently on LinkedIn
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            const currentTab = tabs[0];
            
            const statusElement = document.getElementById('linkedin-status');
            const statusIcon = statusElement.querySelector('.status-icon');
            const statusTitle = statusElement.querySelector('.status-title');
            const statusDescription = statusElement.querySelector('.status-description');

            if (currentTab && currentTab.url && currentTab.url.includes('linkedin.com')) {
                statusIcon.textContent = '✅';
                statusTitle.textContent = 'LinkedIn Detected';
                statusDescription.textContent = 'Ready to search for contact information';
                statusElement.style.borderLeft = '4px solid #27ae60';
            } else {
                statusIcon.textContent = '🔍';
                statusTitle.textContent = 'Ready to Search';
                statusDescription.textContent = 'Visit any LinkedIn profile to find contact information';
                statusElement.style.borderLeft = '4px solid #667eea';
            }
        } catch (error) {
            console.error('Error updating LinkedIn status:', error);
        }
    }

    async updateDashboardStats() {
        const today = new Date().toDateString();
        const todaySearches = this.searchHistory.filter(search => 
            new Date(search.timestamp).toDateString() === today
        );

        const contactsFound = todaySearches.filter(search => search.found).length;
        const successRate = todaySearches.length > 0 
            ? Math.round((contactsFound / todaySearches.length) * 100) 
            : 0;

        document.getElementById('searches-today').textContent = todaySearches.length;
        document.getElementById('contacts-found').textContent = contactsFound;
        document.getElementById('success-rate').textContent = `${successRate}%`;
    }

    async loadRecentSearches() {
        const recentContainer = document.getElementById('recent-searches');
        
        if (this.searchHistory.length === 0) {
            recentContainer.innerHTML = `
                <div class="empty-state">
                    <p>No recent searches</p>
                    <small>Start by visiting a LinkedIn profile</small>
                </div>
            `;
            return;
        }

        // Show last 5 searches
        const recentSearches = this.searchHistory
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 5);

        recentContainer.innerHTML = recentSearches.map(search => `
            <div class="recent-item">
                <div class="recent-avatar">
                    ${search.name ? search.name.charAt(0).toUpperCase() : '?'}
                </div>
                <div class="recent-info">
                    <div class="recent-name">${search.name || 'Unknown'}</div>
                    <div class="recent-company">${search.company || 'No company'}</div>
                </div>
                <div class="recent-meta">
                    <div class="recent-status ${search.found ? 'found' : 'not-found'}">
                        ${search.found ? '✅ Found' : '❌ Not Found'}
                    </div>
                    <div class="recent-time">${this.formatRelativeTime(search.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }

    loadSettingsValues() {
        document.getElementById('auto-search').checked = this.settings.autoSearch;
        document.getElementById('show-notifications').checked = this.settings.showNotifications;
        document.getElementById('save-history').checked = this.settings.saveHistory;
    }

    async updateSetting(key, value) {
        this.settings[key] = value;
        await chrome.storage.local.set({ settings: this.settings });
        
        // Send message to background script
        chrome.runtime.sendMessage({
            action: 'updateSettings',
            settings: this.settings
        });
    }

    async checkFirstTimeUser() {
        if (this.isFirstTime) {
            this.showSection('welcome');
            
            // Mark as not first time anymore
            await chrome.storage.local.set({ isFirstTime: false });
        }
    }

    async startTrial() {
        // Set initial credits
        await chrome.storage.local.set({
            userCredits: 10,
            isFirstTime: false
        });
        
        this.userCredits = 10;
        this.showSection('dashboard');
        this.updateUI();
        
        this.showSuccessMessage('🎉 Welcome to DEMORI! You have 10 free searches to get started.');
    }

    openLinkedIn() {
        chrome.tabs.create({ url: 'https://linkedin.com' });
        window.close();
    }

    showSearchHistory() {
        // Create a new window or tab with search history
        chrome.tabs.create({
            url: chrome.runtime.getURL('history.html')
        });
    }

    async exportContacts() {
        try {
            const contactsData = this.searchHistory
                .filter(search => search.found && search.contactInfo)
                .map(search => ({
                    name: search.name,
                    company: search.company,
                    email: search.contactInfo.email,
                    phone: search.contactInfo.phone,
                    searchDate: search.timestamp
                }));

            if (contactsData.length === 0) {
                this.showWarningMessage('No contacts found to export. Search for some contacts first!');
                return;
            }

            // Convert to CSV
            const csvContent = this.convertToCSV(contactsData);
            
            // Download CSV
            this.downloadCSV(csvContent, 'demori-contacts.csv');
            
            this.showSuccessMessage(`✅ Exported ${contactsData.length} contacts successfully!`);

        } catch (error) {
            console.error('Export failed:', error);
            this.showErrorMessage('❌ Failed to export contacts. Please try again.');
        }
    }

    convertToCSV(data) {
        const headers = ['Name', 'Company', 'Email', 'Phone', 'Search Date'];
        const csvRows = [headers.join(',')];

        data.forEach(contact => {
            const row = [
                `"${contact.name || ''}"`,
                `"${contact.company || ''}"`,
                `"${contact.email || ''}"`,
                `"${contact.phone || ''}"`,
                `"${new Date(contact.searchDate).toLocaleDateString()}"`
            ];
            csvRows.push(row.join(','));
        });

        return csvRows.join('\n');
    }

    downloadCSV(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        chrome.downloads.download({
            url: url,
            filename: filename,
            saveAs: true
        });
    }

    showUpgradeSection() {
        this.showSection('upgrade');
    }

    updateUpgradeInfo() {
        // Update current plan info and recommendations
        const currentPlanElement = document.querySelector('.upgrade-card.featured h3');
        if (currentPlanElement) {
            if (this.userPlan === 'Free Trial') {
                // Highlight Professional plan for free users
                document.querySelectorAll('.upgrade-card').forEach(card => {
                    card.classList.remove('featured');
                });
                
                const proCard = Array.from(document.querySelectorAll('.upgrade-card h3'))
                    .find(h => h.textContent === 'Professional')?.closest('.upgrade-card');
                    
                if (proCard) {
                    proCard.classList.add('featured');
                }
            }
        }
    }

    selectPlan(planName) {
        // Open pricing page with selected plan
        chrome.tabs.create({
            url: `https://your-website.com/pricing?plan=${planName.toLowerCase()}&source=extension`
        });
        window.close();
    }

    openLoginPage() {
        chrome.tabs.create({
            url: 'https://your-website.com/login?source=extension'
        });
        window.close();
    }

    async clearAllData() {
        if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
            await chrome.storage.local.clear();
            
            // Reset to defaults
            this.userCredits = 10;
            this.dailyUsage = 0;
            this.searchHistory = [];
            this.settings = {
                autoSearch: true,
                showNotifications: true,
                saveHistory: true
            };

            await chrome.storage.local.set({
                userCredits: 10,
                dailyUsage: 0,
                searchHistory: [],
                settings: this.settings,
                lastUsageReset: new Date().toDateString()
            });

            this.updateUI();
            this.showSuccessMessage('✅ All data cleared successfully!');
        }
    }

    async exportUserData() {
        try {
            const userData = await chrome.storage.local.get();
            const dataBlob = new Blob([JSON.stringify(userData, null, 2)], { 
                type: 'application/json' 
            });
            
            const url = window.URL.createObjectURL(dataBlob);
            chrome.downloads.download({
                url: url,
                filename: 'demori-user-data.json',
                saveAs: true
            });

            this.showSuccessMessage('✅ User data exported successfully!');
        } catch (error) {
            console.error('Export failed:', error);
            this.showErrorMessage('❌ Failed to export user data.');
        }
    }

    startRealTimeUpdates() {
        // Update stats every 30 seconds
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.updateDashboardStats();
                this.updateLinkedInStatus();
            }
        }, 30000);

        // Listen for messages from background script
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.type === 'stats_update') {
                this.userCredits = message.credits;
                this.dailyUsage = message.dailyUsage;
                this.updateUI();
            } else if (message.type === 'new_search') {
                this.searchHistory.unshift(message.search);
                if (this.currentSection === 'dashboard') {
                    this.loadRecentSearches();
                    this.updateDashboardStats();
                }
            }
        });
    }

    // Utility functions
    formatRelativeTime(timestamp) {
        const now = new Date();
        const searchTime = new Date(timestamp);
        const diffInMinutes = Math.floor((now - searchTime) / (1000 * 60));

        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours}h ago`;
        
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d ago`;
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showWarningMessage(message) {
        this.showMessage(message, 'warning');
    }

    showMessage(message, type) {
        // Remove existing messages
        document.querySelectorAll('.success-message, .error-message, .warning-message').forEach(el => {
            el.remove();
        });

        const messageEl = document.createElement('div');
        messageEl.className = `${type}-message`;
        messageEl.textContent = message;
        messageEl.style.animation = 'slideUp 0.3s ease';

        const content = document.querySelector('.content');
        content.insertBefore(messageEl, content.firstChild);

        // Auto remove after 5 seconds
        setTimeout(() => {
            messageEl.remove();
        }, 5000);
    }

    showLoading(text = 'Loading...') {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DemoriPopup();
});