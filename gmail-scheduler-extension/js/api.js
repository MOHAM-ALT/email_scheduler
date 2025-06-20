// Demori API Client
class DemoriAPI {
    constructor() {
        this.baseUrl = 'https://api.demori.com/v1';
        this.apiKey = null;
        this.init();
    }

    async init() {
        this.apiKey = await this.getStoredApiKey();
    }

    async getStoredApiKey() {
        return new Promise((resolve) => {
            chrome.storage.local.get(['apiKey'], (result) => {
                resolve(result.apiKey || 'demo_api_key_123');
            });
        });
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey,
                'User-Agent': 'Demori-Extension/1.0.0',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    async searchContacts(searchData) {
        return this.makeRequest('/contacts/search', {
            method: 'POST',
            body: JSON.stringify({
                query: {
                    name: searchData.name,
                    company: searchData.company,
                    title: searchData.title,
                    location: searchData.location
                },
                options: {
                    includeEmails: true,
                    includePhones: true,
                    includeSocialMedia: true,
                    includeEducation: true,
                    maxResults: 10
                },
                timestamp: new Date().toISOString()
            })
        });
    }

    async enrichProfile(profileData) {
        return this.makeRequest('/profiles/enrich', {
            method: 'POST',
            body: JSON.stringify({
                profile: profileData,
                enrichmentLevel: 'comprehensive',
                sources: [
                    'company_websites',
                    'professional_directories', 
                    'social_platforms',
                    'public_records'
                ]
            })
        });
    }

    async verifyEmail(email) {
        return this.makeRequest('/verification/email', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async verifyPhone(phone) {
        return this.makeRequest('/verification/phone', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });
    }

    async getSearchHistory() {
        return this.makeRequest('/user/search-history');
    }

    async logActivity(activity) {
        return this.makeRequest('/analytics/activity', {
            method: 'POST',
            body: JSON.stringify({
                action: activity.action,
                data: activity.data,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                extension_version: '1.0.0'
            })
        });
    }

    // Batch operations
    async batchSearchContacts(profiles) {
        return this.makeRequest('/contacts/batch-search', {
            method: 'POST',
            body: JSON.stringify({
                profiles: profiles,
                batchId: this.generateBatchId(),
                options: {
                    priority: 'normal',
                    notifyOnComplete: true
                }
            })
        });
    }

    async exportResults(results, format = 'json') {
        return this.makeRequest('/export/results', {
            method: 'POST',
            body: JSON.stringify({
                results: results,
                format: format,
                options: {
                    includeMetadata: true,
                    anonymize: false
                }
            })
        });
    }

    // Data sources management
    async getAvailableSources() {
        return this.makeRequest('/sources/available');
    }

    async enableSource(sourceId) {
        return this.makeRequest(`/sources/${sourceId}/enable`, {
            method: 'POST'
        });
    }

    async disableSource(sourceId) {
        return this.makeRequest(`/sources/${sourceId}/disable`, {
            method: 'POST'
        });
    }

    // User preferences
    async getUserPreferences() {
        return this.makeRequest('/user/preferences');
    }

    async updateUserPreferences(preferences) {
        return this.makeRequest('/user/preferences', {
            method: 'PUT',
            body: JSON.stringify(preferences)
        });
    }

    // Utility methods
    generateBatchId() {
        return 'batch_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async testConnection() {
        try {
            const response = await this.makeRequest('/health');
            return { success: true, data: response };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Error handling and retry logic
    async makeRequestWithRetry(endpoint, options = {}, maxRetries = 3) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await this.makeRequest(endpoint, options);
            } catch (error) {
                lastError = error;
                
                if (i < maxRetries - 1) {
                    // Wait before retry (exponential backoff)
                    const delay = Math.pow(2, i) * 1000;
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        throw lastError;
    }

    // Rate limiting
    async makeRateLimitedRequest(endpoint, options = {}) {
        const rateLimitKey = `rate_limit_${endpoint}`;
        const lastRequestTime = await this.getLastRequestTime(rateLimitKey);
        const minInterval = 1000; // 1 second between requests
        
        const now = Date.now();
        const timeSinceLastRequest = now - lastRequestTime;
        
        if (timeSinceLastRequest < minInterval) {
            const waitTime = minInterval - timeSinceLastRequest;
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        await this.setLastRequestTime(rateLimitKey, Date.now());
        return this.makeRequest(endpoint, options);
    }

    async getLastRequestTime(key) {
        return new Promise((resolve) => {
            chrome.storage.local.get([key], (result) => {
                resolve(result[key] || 0);
            });
        });
    }

    async setLastRequestTime(key, time) {
        return new Promise((resolve) => {
            chrome.storage.local.set({ [key]: time }, resolve);
        });
    }
}

// Export for use in other scripts
window.DemoriAPI = DemoriAPI;