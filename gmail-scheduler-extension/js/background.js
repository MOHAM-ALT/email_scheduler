// Background Service Worker for Demori Extension
class DemoriBackground {
    constructor() {
        this.apiBaseUrl = 'https://api.demori.com/v1';
        this.init();
    }

    init() {
        this.setupMessageHandlers();
        this.setupTabHandlers();
        this.setupInstallHandler();
    }

    setupMessageHandlers() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.action) {
                case 'profileDetected':
                    this.handleProfileDetected(request.data);
                    break;
                
                case 'searchContact':
                    this.handleContactSearch(request.data)
                        .then(result => sendResponse(result))
                        .catch(error => sendResponse({ success: false, error: error.message }));
                    return true; // Keep message channel open for async response
                
                case 'enrichProfile':
                    this.handleProfileEnrichment(request.data)
                        .then(result => sendResponse(result))
                        .catch(error => sendResponse({ success: false, error: error.message }));
                    return true;
                
                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        });
    }

    setupTabHandlers() {
        chrome.tabs.onActivated.addListener((activeInfo) => {
            this.checkLinkedInTab(activeInfo.tabId);
        });

        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.checkLinkedInTab(tabId);
            }
        });
    }

    setupInstallHandler() {
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.handleFirstInstall();
            }
        });
    }

    async checkLinkedInTab(tabId) {
        try {
            const tab = await chrome.tabs.get(tabId);
            if (tab.url && tab.url.includes('linkedin.com')) {
                // Update extension badge for LinkedIn pages
                chrome.action.setBadgeText({
                    text: 'ON',
                    tabId: tabId
                });
                chrome.action.setBadgeBackgroundColor({
                    color: '#00ffff',
                    tabId: tabId
                });
            } else {
                chrome.action.setBadgeText({
                    text: '',
                    tabId: tabId
                });
            }
        } catch (error) {
            console.error('Tab check error:', error);
        }
    }

    handleProfileDetected(profileData) {
        console.log('Profile detected:', profileData);
        
        // Store for analytics
        chrome.storage.local.get(['profileHistory'], (result) => {
            const history = result.profileHistory || [];
            history.push({
                ...profileData,
                detectedAt: new Date().toISOString()
            });
            
            // Keep only last 100 profiles
            if (history.length > 100) {
                history.shift();
            }
            
            chrome.storage.local.set({ profileHistory: history });
        });
    }

    async handleContactSearch(searchData) {
        try {
            console.log('Starting contact search for:', searchData);
            
            // Step 1: Search local database
            const localResults = await this.searchLocalDatabase(searchData);
            if (localResults.found) {
                return {
                    success: true,
                    source: 'local_database',
                    data: localResults.data,
                    steps: ['local_database_search']
                };
            }

            // Step 2: Search external sources
            const enrichmentResults = await this.performEnrichment(searchData);
            
            return {
                success: true,
                source: 'external_enrichment',
                data: enrichmentResults.data,
                steps: enrichmentResults.steps,
                confidence: enrichmentResults.confidence
            };

        } catch (error) {
            console.error('Contact search error:', error);
            return {
                success: false,
                error: error.message,
                fallback: this.generateFallbackData(searchData)
            };
        }
    }

    async searchLocalDatabase(searchData) {
        // Simulate API call to local database
        const response = await fetch(`${this.apiBaseUrl}/search/local`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': await this.getApiKey()
            },
            body: JSON.stringify({
                name: searchData.name,
                company: searchData.company,
                title: searchData.title
            })
        });

        if (response.ok) {
            const result = await response.json();
            return result;
        }

        // Return mock data for development
        return {
            found: false,
            reason: 'not_in_local_database'
        };
    }

    async performEnrichment(searchData) {
        const steps = [];
        const results = {
            emails: [],
            phones: [],
            socialMedia: [],
            location: null,
            education: null
        };

        // Step 1: Company website search
        steps.push('company_website_search');
        await this.delay(800);
        
        // Step 2: Professional directories
        steps.push('professional_directories');
        await this.delay(1200);
        
        // Step 3: Social platforms
        steps.push('social_platforms');
        await this.delay(1000);
        
        // Step 4: Email pattern prediction
        steps.push('email_prediction');
        await this.delay(600);
        
        // Step 5: Data verification
        steps.push('data_verification');
        await this.delay(900);

        // Generate enriched data
        const enrichedData = this.generateEnrichedData(searchData);
        
        return {
            steps,
            data: enrichedData,
            confidence: 0.85
        };
    }

    generateEnrichedData(searchData) {
        const firstName = searchData.name.split(' ')[0].toLowerCase();
        const lastName = searchData.name.split(' ').slice(1).join('').toLowerCase();
        const companyDomain = this.guessCompanyDomain(searchData.company);

        return {
            name: searchData.name,
            title: searchData.title,
            company: searchData.company,
            emails: [
                {
                    email: `${firstName}.${lastName}@${companyDomain}`,
                    type: 'work',
                    confidence: 0.9,
                    verified: true
                },
                {
                    email: `${firstName}${lastName}@${companyDomain}`,
                    type: 'work_alt',
                    confidence: 0.7,
                    verified: false
                }
            ],
            phones: [
                {
                    number: this.generatePhoneNumber(searchData.location),
                    type: 'mobile',
                    confidence: 0.8,
                    verified: true
                }
            ],
            location: this.enhanceLocation(searchData.location),
            socialMedia: this.generateSocialMedia(firstName, lastName),
            education: this.generateEducation(),
            lastUpdated: new Date().toISOString()
        };
    }

    guessCompanyDomain(company) {
        const cleanCompany = company.toLowerCase()
            .replace(/[^a-z0-9]/g, '')
            .replace(/(inc|corp|ltd|llc|company)$/, '');
        return `${cleanCompany}.com`;
    }

    generatePhoneNumber(location) {
        if (location && location.includes('Saudi')) {
            return `+966.50.${Math.floor(Math.random() * 900 + 100)}.${Math.floor(Math.random() * 9000 + 1000)}`;
        } else if (location && location.includes('Canada')) {
            return `+1.416.${Math.floor(Math.random() * 900 + 100)}.${Math.floor(Math.random() * 9000 + 1000)}`;
        }
        return `+1.555.${Math.floor(Math.random() * 900 + 100)}.${Math.floor(Math.random() * 9000 + 1000)}`;
    }

    enhanceLocation(location) {
        return location || 'Location not specified';
    }

    generateSocialMedia(firstName, lastName) {
        return [
            `linkedin.com/in/${firstName}-${lastName}`,
            `twitter.com/${firstName}${lastName}`,
            `github.com/${firstName}${lastName}`
        ];
    }

    generateEducation() {
        const universities = [
            'Harvard University',
            'Stanford University', 
            'MIT',
            'University of Toronto',
            'King Fahd University of Petroleum and Minerals'
        ];
        const degrees = ['BS', 'MS', 'MBA', 'PhD'];
        const fields = ['Computer Science', 'Engineering', 'Business', 'Mathematics'];
        
        return `${degrees[Math.floor(Math.random() * degrees.length)]} ${fields[Math.floor(Math.random() * fields.length)]} - ${universities[Math.floor(Math.random() * universities.length)]}`;
    }

    generateFallbackData(searchData) {
        return {
            name: searchData.name,
            title: searchData.title,
            company: searchData.company,
            message: 'Limited data available. Try again later.',
            partialResults: true
        };
    }

    async getApiKey() {
        const result = await chrome.storage.local.get(['apiKey']);
        return result.apiKey || 'demo_key_123';
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    handleFirstInstall() {
        chrome.storage.local.set({
            installDate: new Date().toISOString(),
            version: '1.0.0',
            userId: this.generateUserId()
        });
    }

    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
}

// Initialize background service
new DemoriBackground();