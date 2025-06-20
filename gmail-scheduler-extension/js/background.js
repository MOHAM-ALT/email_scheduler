// DEMORI Contact Finder Pro - Background Service Worker
class DemoriBackgroundService {
    constructor() {
        this.apiEndpoint = 'https://your-api-domain.com/api';
        this.isAuthenticated = false;
        this.userCredits = 0;
        this.dailyUsage = 0;
        
        this.init();
    }

    init() {
        console.log('🚀 DEMORI Background Service Worker Started');
        
        // Handle extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            this.handleInstallation(details);
        });

        // Handle messages from content script and popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async responses
        });

        // Handle browser action (extension icon click)
        chrome.action.onClicked.addListener((tab) => {
            this.handleActionClick(tab);
        });

        // Initialize daily usage reset
        this.initDailyUsageReset();
    }

    async handleInstallation(details) {
        if (details.reason === 'install') {
            console.log('🎉 DEMORI Contact Finder Pro installed');
            
            // Set initial storage values
            await chrome.storage.local.set({
                isFirstTime: true,
                userCredits: 10, // Free trial credits
                dailyUsage: 0,
                installDate: new Date().toISOString(),
                settings: {
                    autoSearch: true,
                    showNotifications: true,
                    saveToHistory: true
                }
            });

            // Open welcome page
            chrome.tabs.create({
                url: 'https://your-website.com/welcome?source=extension'
            });

        } else if (details.reason === 'update') {
            console.log('🔄 DEMORI Contact Finder Pro updated');
            this.handleUpdate(details);
        }
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'searchContact':
                    const searchResult = await this.searchContact(request.data);
                    sendResponse(searchResult);
                    break;

                case 'getCredits':
                    const credits = await this.getUserCredits();
                    sendResponse({ credits });
                    break;

                case 'trackUsage':
                    await this.trackUsage(request.data);
                    sendResponse({ success: true });
                    break;

                case 'saveContact':
                    const saveResult = await this.saveContact(request.data);
                    sendResponse(saveResult);
                    break;

                case 'getSettings':
                    const settings = await this.getSettings();
                    sendResponse({ settings });
                    break;

                case 'updateSettings':
                    await this.updateSettings(request.settings);
                    sendResponse({ success: true });
                    break;

                case 'authenticateUser':
                    const authResult = await this.authenticateUser(request.credentials);
                    sendResponse(authResult);
                    break;

                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background message error:', error);
            sendResponse({ error: error.message });
        }
    }

    async searchContact(profileData) {
        try {
            // Check if user has credits
            const hasCredits = await this.checkUserCredits();
            if (!hasCredits) {
                return {
                    error: 'insufficient_credits',
                    message: 'You have no remaining credits. Please upgrade your plan.'
                };
            }

            // Check daily usage limits
            const dailyUsage = await this.getDailyUsage();
            if (dailyUsage >= 100) { // Free tier daily limit
                return {
                    error: 'daily_limit_exceeded',
                    message: 'Daily search limit reached. Upgrade for unlimited searches.'
                };
            }

            // Prepare search request with ContactOut-style parameters
            const searchRequest = {
                query: {
                    fullName: profileData.name,
                    company: profileData.company,
                    title: profileData.title,
                    location: profileData.location
                },
                source: 'professional_database_search',
                searchType: 'comprehensive',
                includeEmailVerification: true,
                includePhoneVerification: true,
                timestamp: new Date().toISOString()
            };

            // Search our database via API
            const response = await fetch(`${this.apiEndpoint}/search-contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': await this.getApiKey(),
                    'X-Extension-Version': '1.0.0',
                    'X-User-Agent': 'DEMORI-ContactFinder-Pro/1.0.0'
                },
                body: JSON.stringify(searchRequest)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const result = await response.json();

            // Update usage tracking
            await this.incrementUsage();
            
            // Track analytics
            await this.trackAnalytics('contact_search', {
                found: result.found,
                company: profileData.company,
                hasEmail: result.contacts?.[0]?.email ? true : false,
                hasPhone: result.contacts?.[0]?.phone ? true : false
            });

            return {
                success: true,
                found: result.found,
                contacts: result.contacts || [],
                searchId: result.searchId,
                creditsRemaining: await this.getUserCredits() - 1
            };

        } catch (error) {
            console.error('Contact search error:', error);
            return {
                error: 'search_failed',
                message: 'Unable to search database. Please try again.'
            };
        }
    }

    async checkUserCredits() {
        const storage = await chrome.storage.local.get(['userCredits']);
        const credits = storage.userCredits || 0;
        return credits > 0;
    }

    async getUserCredits() {
        const storage = await chrome.storage.local.get(['userCredits']);
        return storage.userCredits || 0;
    }

    async getDailyUsage() {
        const storage = await chrome.storage.local.get(['dailyUsage', 'lastUsageReset']);
        const today = new Date().toDateString();
        const lastReset = storage.lastUsageReset;

        // Reset if it's a new day
        if (lastReset !== today) {
            await chrome.storage.local.set({
                dailyUsage: 0,
                lastUsageReset: today
            });
            return 0;
        }

        return storage.dailyUsage || 0;
    }

    async incrementUsage() {
        const currentUsage = await this.getDailyUsage();
        const currentCredits = await this.getUserCredits();

        await chrome.storage.local.set({
            dailyUsage: currentUsage + 1,
            userCredits: Math.max(0, currentCredits - 1)
        });
    }

    async trackUsage(data) {
        try {
            await fetch(`${this.apiEndpoint}/track-usage`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': await this.getApiKey()
                },
                body: JSON.stringify({
                    ...data,
                    extensionVersion: '1.0.0',
                    userAgent: navigator.userAgent,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.log('Usage tracking failed:', error);
        }
    }

    async trackAnalytics(event, properties) {
        try {
            await fetch(`${this.apiEndpoint}/analytics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': await this.getApiKey()
                },
                body: JSON.stringify({
                    event,
                    properties,
                    timestamp: new Date().toISOString(),
                    source: 'chrome_extension'
                })
            });
        } catch (error) {
            console.log('Analytics tracking failed:', error);
        }
    }

    async saveContact(contactData) {
        try {
            const response = await fetch(`${this.apiEndpoint}/save-contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': await this.getApiKey()
                },
                body: JSON.stringify({
                    ...contactData,
                    source: 'extension_save',
                    timestamp: new Date().toISOString()
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Update local storage
                const storage = await chrome.storage.local.get(['savedContacts']);
                const savedContacts = storage.savedContacts || [];
                savedContacts.push({
                    ...contactData,
                    savedAt: new Date().toISOString()
                });
                
                await chrome.storage.local.set({ savedContacts });
            }

            return result;
        } catch (error) {
            console.error('Save contact error:', error);
            return { error: 'save_failed' };
        }
    }

    async getSettings() {
        const storage = await chrome.storage.local.get(['settings']);
        return storage.settings || {
            autoSearch: true,
            showNotifications: true,
            saveToHistory: true
        };
    }

    async updateSettings(newSettings) {
        await chrome.storage.local.set({ settings: newSettings });
    }

    async authenticateUser(credentials) {
        try {
            const response = await fetch(`${this.apiEndpoint}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            const result = await response.json();

            if (result.success) {
                await chrome.storage.local.set({
                    isAuthenticated: true,
                    userCredits: result.credits,
                    userPlan: result.plan,
                    apiKey: result.apiKey
                });

                this.isAuthenticated = true;
                this.userCredits = result.credits;
            }

            return result;
        } catch (error) {
            console.error('Authentication error:', error);
            return { error: 'auth_failed' };
        }
    }

    async getApiKey() {
        const storage = await chrome.storage.local.get(['apiKey']);
        return storage.apiKey || 'demo_key_free_tier';
    }

    async handleActionClick(tab) {
        // Check if we're on LinkedIn
        if (tab.url && tab.url.includes('linkedin.com')) {
            // Inject content script if not already injected
            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    files: ['js/content.js']
                });
            } catch (error) {
                console.log('Content script already injected or failed:', error);
            }
        } else {
            // Open popup or redirect to LinkedIn
            chrome.tabs.create({
                url: 'https://linkedin.com'
            });
        }
    }

    initDailyUsageReset() {
        // Check every hour if we need to reset daily usage
        setInterval(async () => {
            const storage = await chrome.storage.local.get(['lastUsageReset']);
            const today = new Date().toDateString();
            
            if (storage.lastUsageReset !== today) {
                await chrome.storage.local.set({
                    dailyUsage: 0,
                    lastUsageReset: today
                });
                console.log('Daily usage reset');
            }
        }, 60 * 60 * 1000); // Check every hour
    }

    async handleUpdate(details) {
        // Handle extension updates
        const previousVersion = details.previousVersion;
        const currentVersion = chrome.runtime.getManifest().version;

        console.log(`Updated from ${previousVersion} to ${currentVersion}`);

        // Migration logic if needed
        if (this.needsMigration(previousVersion, currentVersion)) {
            await this.migrateData(previousVersion, currentVersion);
        }
    }

    needsMigration(oldVersion, newVersion) {
        // Add migration logic here
        return false;
    }

    async migrateData(oldVersion, newVersion) {
        // Add data migration logic here
        console.log('Data migration completed');
    }

    // Utility methods
    async showNotification(title, message, type = 'info') {
        const settings = await this.getSettings();
        if (!settings.showNotifications) return;

        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: title,
            message: message
        });
    }

    async clearUserData() {
        await chrome.storage.local.clear();
        console.log('User data cleared');
    }

    async exportUserData() {
        const data = await chrome.storage.local.get();
        return data;
    }
}

// Initialize background service
new DemoriBackgroundService();