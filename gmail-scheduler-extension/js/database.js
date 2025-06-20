// Real Database Integration for Demori
class DemoriDatabase {
    constructor() {
        this.serverUrl = 'https://api.demori.com/v1'; // سيتم تغييرها للخادم الحقيقي
        this.apiKey = null;
        this.userId = null;
        this.retryAttempts = 3;
        this.timeout = 30000; // 30 seconds
        this.init();
    }

    async init() {
        await this.loadCredentials();
        await this.validateConnection();
    }

    async loadCredentials() {
        const storage = await chrome.storage.local.get(['apiKey', 'userId', 'serverUrl']);
        this.apiKey = storage.apiKey || 'demo_key_' + Date.now();
        this.userId = storage.userId || await this.generateUserId();
        
        if (storage.serverUrl) {
            this.serverUrl = storage.serverUrl;
        }
        
        // Store generated credentials
        await chrome.storage.local.set({
            apiKey: this.apiKey,
            userId: this.userId,
            serverUrl: this.serverUrl
        });
    }

    async generateUserId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `user_${timestamp}_${random}`;
    }

    async validateConnection() {
        try {
            const response = await this.makeRequest('/health', 'GET');
            console.log('Database connection validated:', response);
            return true;
        } catch (error) {
            console.warn('Database connection failed, switching to offline mode:', error);
            return false;
        }
    }

    async makeRequest(endpoint, method = 'GET', data = null, retryCount = 0) {
        const url = `${this.serverUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
                'X-User-ID': this.userId,
                'X-Extension-Version': '1.0.0',
                'X-Request-ID': this.generateRequestId()
            },
            timeout: this.timeout
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                if (response.status === 429 && retryCount < this.retryAttempts) {
                    // Rate limit - wait and retry
                    const waitTime = Math.pow(2, retryCount) * 1000;
                    await this.delay(waitTime);
                    return this.makeRequest(endpoint, method, data, retryCount + 1);
                }
                
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return result;
            
        } catch (error) {
            if (retryCount < this.retryAttempts && this.isRetryableError(error)) {
                const waitTime = Math.pow(2, retryCount) * 1000;
                await this.delay(waitTime);
                return this.makeRequest(endpoint, method, data, retryCount + 1);
            }
            
            throw error;
        }
    }

    isRetryableError(error) {
        return error.name === 'NetworkError' || 
               error.message.includes('timeout') ||
               error.message.includes('500') ||
               error.message.includes('502') ||
               error.message.includes('503');
    }

    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }

    // Core Database Operations
    async searchContacts(searchParams) {
        const searchData = {
            query: {
                name: searchParams.name,
                company: searchParams.company,
                title: searchParams.title,
                location: searchParams.location,
                email_domain: searchParams.emailDomain
            },
            filters: {
                confidence_min: searchParams.confidenceThreshold || 0.6,
                verified_only: searchParams.verifiedOnly || false,
                include_social: searchParams.includeSocial || true,
                max_results: searchParams.maxResults || 50
            },
            options: {
                include_metadata: true,
                include_sources: true,
                real_time_verification: searchParams.realtimeVerification || false
            }
        };

        try {
            const result = await this.makeRequest('/contacts/search', 'POST', searchData);
            
            // Store search in history
            await this.saveSearchHistory(searchParams, result);
            
            return this.formatSearchResults(result);
            
        } catch (error) {
            console.error('Database search failed:', error);
            return this.handleSearchFallback(searchParams, error);
        }
    }

    async enrichProfile(profileData) {
        const enrichmentData = {
            profile: {
                name: profileData.name,
                company: profileData.company,
                title: profileData.title,
                location: profileData.location,
                profile_url: profileData.profileUrl
            },
            enrichment_level: profileData.level || 'comprehensive',
            sources: profileData.sources || [
                'company_websites',
                'professional_directories',
                'social_platforms',
                'public_records'
            ]
        };

        try {
            const result = await this.makeRequest('/profiles/enrich', 'POST', enrichmentData);
            return this.formatEnrichmentResults(result);
        } catch (error) {
            console.error('Profile enrichment failed:', error);
            throw error;
        }
    }

    async verifyEmail(email) {
        try {
            const result = await this.makeRequest('/verification/email', 'POST', { email });
            return {
                email,
                valid: result.valid,
                deliverable: result.deliverable,
                risk_level: result.risk_level,
                provider: result.provider,
                verified_at: new Date().toISOString()
            };
        } catch (error) {
            console.error('Email verification failed:', error);
            return {
                email,
                valid: null,
                error: error.message
            };
        }
    }

    async verifyPhone(phone) {
        try {
            const result = await this.makeRequest('/verification/phone', 'POST', { phone });
            return {
                phone,
                valid: result.valid,
                country: result.country,
                carrier: result.carrier,
                line_type: result.line_type,
                verified_at: new Date().toISOString()
            };
        } catch (error) {
            console.error('Phone verification failed:', error);
            return {
                phone,
                valid: null,
                error: error.message
            };
        }
    }

    async saveContact(contactData) {
        const contact = {
            ...contactData,
            user_id: this.userId,
            created_at: new Date().toISOString(),
            source: 'extension_search'
        };

        try {
            const result = await this.makeRequest('/contacts', 'POST', contact);
            return result;
        } catch (error) {
            console.error('Failed to save contact:', error);
            // Store locally if server fails
            await this.saveContactLocally(contact);
            throw error;
        }
    }

    async saveContactLocally(contact) {
        const storage = await chrome.storage.local.get(['localContacts']);
        const contacts = storage.localContacts || [];
        
        contacts.push({
            ...contact,
            id: `local_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            synced: false
        });
        
        await chrome.storage.local.set({ localContacts: contacts });
    }

    async syncLocalContacts() {
        const storage = await chrome.storage.local.get(['localContacts']);
        const localContacts = storage.localContacts || [];
        const unsyncedContacts = localContacts.filter(c => !c.synced);
        
        if (unsyncedContacts.length === 0) return;

        try {
            const result = await this.makeRequest('/contacts/batch', 'POST', {
                contacts: unsyncedContacts
            });
            
            // Mark as synced
            const updatedContacts = localContacts.map(contact => {
                if (unsyncedContacts.find(uc => uc.id === contact.id)) {
                    return { ...contact, synced: true, server_id: result.contact_ids[contact.id] };
                }
                return contact;
            });
            
            await chrome.storage.local.set({ localContacts: updatedContacts });
            console.log(`Synced ${unsyncedContacts.length} local contacts`);
            
        } catch (error) {
            console.error('Contact sync failed:', error);
        }
    }

    async getSearchHistory(limit = 50) {
        try {
            const result = await this.makeRequest(`/users/${this.userId}/searches?limit=${limit}`);
            return result.searches || [];
        } catch (error) {
            console.error('Failed to fetch search history:', error);
            // Fallback to local history
            const storage = await chrome.storage.local.get(['searchHistory']);
            return storage.searchHistory || [];
        }
    }

    async saveSearchHistory(searchParams, results) {
        const historyEntry = {
            user_id: this.userId,
            search_params: searchParams,
            results_count: results.total_results || 0,
            confidence_avg: results.average_confidence || 0,
            search_time: results.search_time || 0,
            timestamp: new Date().toISOString()
        };

        try {
            await this.makeRequest('/searches', 'POST', historyEntry);
        } catch (error) {
            console.error('Failed to save search history:', error);
            // Store locally
            const storage = await chrome.storage.local.get(['searchHistory']);
            const history = storage.searchHistory || [];
            history.push(historyEntry);
            
            if (history.length > 100) {
                history.shift();
            }
            
            await chrome.storage.local.set({ searchHistory: history });
        }
    }

    async exportData(format = 'csv', filters = {}) {
        try {
            const result = await this.makeRequest('/export', 'POST', {
                user_id: this.userId,
                format,
                filters,
                include_history: true,
                include_contacts: true
            });
            
            return result.download_url;
        } catch (error) {
            console.error('Export failed:', error);
            throw error;
        }
    }

    async getAnalytics() {
        try {
            const result = await this.makeRequest(`/users/${this.userId}/analytics`);
            return {
                total_searches: result.total_searches || 0,
                total_contacts_found: result.total_contacts_found || 0,
                average_confidence: result.average_confidence || 0,
                top_companies: result.top_companies || [],
                search_trends: result.search_trends || [],
                success_rate: result.success_rate || 0
            };
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
            return null;
        }
    }

    // Utility Methods
    formatSearchResults(apiResults) {
        if (!apiResults || !apiResults.contacts) {
            return { contacts: [], metadata: { total: 0 } };
        }

        return {
            contacts: apiResults.contacts.map(contact => ({
                name: contact.name,
                title: contact.title,
                company: contact.company,
                location: contact.location,
                emails: contact.emails || [],
                phones: contact.phones || [],
                socialProfiles: contact.social_profiles || [],
                confidence: contact.confidence || 0,
                verified: contact.verified || false,
                sources: contact.sources || [],
                lastUpdated: contact.last_updated || new Date().toISOString()
            })),
            metadata: {
                total: apiResults.total_results || 0,
                searchTime: apiResults.search_time || 0,
                confidence: apiResults.average_confidence || 0,
                sources: apiResults.sources_used || []
            }
        };
    }

    formatEnrichmentResults(apiResults) {
        return {
            profile: apiResults.profile,
            enrichment: {
                emails: apiResults.emails || [],
                phones: apiResults.phones || [],
                socialProfiles: apiResults.social_profiles || [],
                additionalInfo: apiResults.additional_info || {},
                confidence: apiResults.confidence || 0
            },
            metadata: {
                enrichmentTime: apiResults.enrichment_time || 0,
                sourcesUsed: apiResults.sources_used || [],
                dataQuality: apiResults.data_quality || 'unknown'
            }
        };
    }

    handleSearchFallback(searchParams, error) {
        console.log('Using fallback search results due to:', error.message);
        
        // Return intelligent fallback based on search params
        return {
            contacts: [{
                name: searchParams.name || 'Unknown',
                title: searchParams.title || 'Unknown',
                company: searchParams.company || 'Unknown',
                location: searchParams.location || 'Unknown',
                emails: [],
                phones: [],
                socialProfiles: [],
                confidence: 0,
                verified: false,
                fallback: true,
                message: 'Server unavailable - limited results'
            }],
            metadata: {
                total: 0,
                fallback: true,
                error: error.message
            }
        };
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Database Health Monitoring
    async checkHealth() {
        try {
            const start = Date.now();
            const result = await this.makeRequest('/health');
            const responseTime = Date.now() - start;
            
            return {
                status: 'healthy',
                responseTime,
                serverVersion: result.version,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

// Export for use in other scripts
window.DemoriDatabase = DemoriDatabase;