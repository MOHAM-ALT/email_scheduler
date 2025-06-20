// DEMORI Contact Finder Pro - LinkedIn Content Script
class DemoriLinkedInIntegration {
    constructor() {
        this.apiEndpoint = 'https://your-api-domain.com/api';
        this.isProcessing = false;
        this.lastProfileData = null;
        
        this.init();
    }

    init() {
        console.log('🚀 DEMORI Contact Finder Pro - Active on LinkedIn');
        
        // Wait for page to load completely
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startMonitoring());
        } else {
            this.startMonitoring();
        }
    }

    startMonitoring() {
        // Monitor for profile pages
        this.checkForProfile();
        
        // Monitor for URL changes (SPA navigation)
        let lastUrl = location.href;
        new MutationObserver(() => {
            const currentUrl = location.href;
            if (currentUrl !== lastUrl) {
                lastUrl = currentUrl;
                setTimeout(() => this.checkForProfile(), 1000);
            }
        }).observe(document, { subtree: true, childList: true });
    }

    checkForProfile() {
        // Check if we're on a LinkedIn profile page
        if (this.isProfilePage()) {
            setTimeout(() => {
                this.extractProfileData();
            }, 2000); // Wait for page elements to load
        }
    }

    isProfilePage() {
        return window.location.pathname.includes('/in/') || 
               window.location.pathname.includes('/profile/');
    }

    extractProfileData() {
        if (this.isProcessing) return;
        
        try {
            const profileData = this.parseLinkedInProfile();
            
            if (profileData && this.isValidProfile(profileData)) {
                // Check if this is a new profile (avoid duplicates)
                if (!this.isSameProfile(profileData)) {
                    this.lastProfileData = profileData;
                    this.searchInDatabase(profileData);
                }
            }
        } catch (error) {
            console.error('Profile extraction error:', error);
        }
    }

    parseLinkedInProfile() {
        const profileData = {};
        
        // Extract name (multiple selectors for different LinkedIn layouts)
        const nameSelectors = [
            'h1[class*="text-heading-xlarge"]',
            '.pv-text-details__left-panel h1',
            '.ph5 h1',
            'h1.break-words'
        ];
        
        for (const selector of nameSelectors) {
            const nameElement = document.querySelector(selector);
            if (nameElement && nameElement.textContent.trim()) {
                profileData.name = nameElement.textContent.trim();
                break;
            }
        }

        // Extract current position/title
        const titleSelectors = [
            '[class*="text-body-medium break-words"]',
            '.pv-text-details__left-panel .text-body-medium',
            '.ph5 .text-body-medium'
        ];
        
        for (const selector of titleSelectors) {
            const titleElement = document.querySelector(selector);
            if (titleElement && titleElement.textContent.trim()) {
                profileData.title = titleElement.textContent.trim();
                break;
            }
        }

        // Extract company from experience section
        const companySelectors = [
            '[data-field="experience_company_logo"] img[alt]',
            '.pv-entity__secondary-title',
            '[class*="experience-item"] [class*="company-name"]'
        ];
        
        for (const selector of companySelectors) {
            const companyElement = document.querySelector(selector);
            if (companyElement) {
                if (companyElement.tagName === 'IMG') {
                    profileData.company = companyElement.alt;
                } else {
                    profileData.company = companyElement.textContent.trim();
                }
                if (profileData.company) break;
            }
        }

        // Extract location
        const locationSelectors = [
            '[class*="text-body-small inline t-black--light break-words"]',
            '.pv-text-details__left-panel .text-body-small',
            '.ph5 .text-body-small'
        ];
        
        for (const selector of locationSelectors) {
            const locationElement = document.querySelector(selector);
            if (locationElement && locationElement.textContent.includes(',')) {
                profileData.location = locationElement.textContent.trim();
                break;
            }
        }

        // Extract profile URL
        profileData.linkedinUrl = window.location.href.split('?')[0];
        
        // Extract profile image URL
        const imageElement = document.querySelector('img[class*="pv-top-card-profile-picture__image"]');
        if (imageElement) {
            profileData.imageUrl = imageElement.src;
        }

        return profileData;
    }

    isValidProfile(profileData) {
        return profileData.name && 
               profileData.name.length > 2 && 
               profileData.name !== 'LinkedIn Member';
    }

    isSameProfile(newProfileData) {
        return this.lastProfileData && 
               this.lastProfileData.name === newProfileData.name &&
               this.lastProfileData.company === newProfileData.company;
    }

    async searchInDatabase(profileData) {
        this.isProcessing = true;
        
        try {
            // Show loading indicator
            this.showLoadingWidget(profileData);
            
            // Search in our database first
            const searchQuery = {
                name: profileData.name,
                company: profileData.company,
                title: profileData.title,
                location: profileData.location,
                source: 'linkedin_profile_view',
                timestamp: new Date().toISOString()
            };

            const response = await fetch(`${this.apiEndpoint}/search-contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Extension-Version': '1.0.0'
                },
                body: JSON.stringify(searchQuery)
            });

            if (response.ok) {
                const result = await response.json();
                this.displayContactInfo(result, profileData);
            } else {
                this.showErrorWidget();
            }
            
        } catch (error) {
            console.error('Database search error:', error);
            this.showErrorWidget();
        } finally {
            this.isProcessing = false;
        }
    }

    showLoadingWidget(profileData) {
        this.removeExistingWidget();
        
        const widget = document.createElement('div');
        widget.id = 'demori-contact-widget';
        widget.innerHTML = `
            <div class="demori-widget-container">
                <div class="demori-header">
                    <img src="${chrome.runtime.getURL('images/demori-logo.png')}" alt="DEMORI" class="demori-logo">
                    <span class="demori-title">Contact Finder Pro</span>
                </div>
                <div class="demori-content">
                    <div class="demori-loading">
                        <div class="demori-spinner"></div>
                        <p>Searching in our comprehensive database...</p>
                        <small>Checking 50M+ verified business contacts</small>
                    </div>
                </div>
            </div>
        `;
        
        this.insertWidget(widget);
    }

    displayContactInfo(result, profileData) {
        this.removeExistingWidget();
        
        const widget = document.createElement('div');
        widget.id = 'demori-contact-widget';
        
        if (result.found && result.contacts && result.contacts.length > 0) {
            const contact = result.contacts[0];
            
            widget.innerHTML = `
                <div class="demori-widget-container success">
                    <div class="demori-header">
                        <img src="${chrome.runtime.getURL('images/demori-logo.png')}" alt="DEMORI" class="demori-logo">
                        <span class="demori-title">Contact Found!</span>
                        <span class="demori-confidence">Confidence: ${contact.confidence || 95}%</span>
                    </div>
                    <div class="demori-content">
                        <div class="demori-contact-info">
                            ${contact.email ? `
                                <div class="demori-contact-item">
                                    <span class="demori-icon">📧</span>
                                    <span class="demori-label">Email:</span>
                                    <span class="demori-value">${contact.email}</span>
                                    <button class="demori-copy-btn" onclick="navigator.clipboard.writeText('${contact.email}')">Copy</button>
                                </div>
                            ` : ''}
                            
                            ${contact.phone ? `
                                <div class="demori-contact-item">
                                    <span class="demori-icon">📞</span>
                                    <span class="demori-label">Phone:</span>
                                    <span class="demori-value">${contact.phone}</span>
                                    <button class="demori-copy-btn" onclick="navigator.clipboard.writeText('${contact.phone}')">Copy</button>
                                </div>
                            ` : ''}
                            
                            ${contact.socialLinks ? `
                                <div class="demori-contact-item">
                                    <span class="demori-icon">🔗</span>
                                    <span class="demori-label">Social:</span>
                                    <div class="demori-social-links">
                                        ${contact.socialLinks.map(link => `
                                            <a href="${link.url}" target="_blank" class="demori-social-link">${link.platform}</a>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        
                        <div class="demori-actions">
                            <button class="demori-btn primary" onclick="this.closest('.demori-widget-container').querySelector('.demori-save-form').style.display='block'">
                                Save to CRM
                            </button>
                            <button class="demori-btn secondary" onclick="window.open('https://your-website.com/contact/${contact.id}', '_blank')">
                                View Details
                            </button>
                        </div>
                        
                        <div class="demori-save-form" style="display: none;">
                            <input type="text" placeholder="Add notes..." class="demori-notes">
                            <button class="demori-btn small">Save</button>
                        </div>
                        
                        <div class="demori-footer">
                            <small>Source: Professional Database | Verified: ${contact.lastVerified || 'Recently'}</small>
                        </div>
                    </div>
                </div>
            `;
        } else {
            widget.innerHTML = `
                <div class="demori-widget-container not-found">
                    <div class="demori-header">
                        <img src="${chrome.runtime.getURL('images/demori-logo.png')}" alt="DEMORI" class="demori-logo">
                        <span class="demori-title">Contact Not Found</span>
                    </div>
                    <div class="demori-content">
                        <div class="demori-not-found">
                            <p>Contact not found in our current database</p>
                            <small>We're constantly expanding our 50M+ contact database</small>
                            
                            <div class="demori-actions">
                                <button class="demori-btn primary" onclick="this.requestContact('${profileData.name}', '${profileData.company}')">
                                    Request Contact Info
                                </button>
                                <button class="demori-btn secondary" onclick="window.open('https://your-website.com/suggest-contact', '_blank')">
                                    Suggest Addition
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.insertWidget(widget);
        
        // Track usage
        this.trackUsage(profileData, result.found);
    }

    showErrorWidget() {
        this.removeExistingWidget();
        
        const widget = document.createElement('div');
        widget.id = 'demori-contact-widget';
        widget.innerHTML = `
            <div class="demori-widget-container error">
                <div class="demori-header">
                    <img src="${chrome.runtime.getURL('images/demori-logo.png')}" alt="DEMORI" class="demori-logo">
                    <span class="demori-title">Connection Error</span>
                </div>
                <div class="demori-content">
                    <p>Unable to search database at the moment</p>
                    <button class="demori-btn primary" onclick="location.reload()">Retry</button>
                </div>
            </div>
        `;
        
        this.insertWidget(widget);
    }

    insertWidget(widget) {
        // Find the best location to insert widget on LinkedIn
        const insertionPoints = [
            '.pv-text-details__left-panel',
            '.ph5 .mt2',
            '.artdeco-card .pv-text-details__left-panel',
            'main .scaffold-layout__main'
        ];
        
        for (const selector of insertionPoints) {
            const container = document.querySelector(selector);
            if (container) {
                container.appendChild(widget);
                break;
            }
        }
    }

    removeExistingWidget() {
        const existing = document.getElementById('demori-contact-widget');
        if (existing) {
            existing.remove();
        }
    }

    async trackUsage(profileData, found) {
        try {
            await fetch(`${this.apiEndpoint}/track-usage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'profile_search',
                    found: found,
                    profileName: profileData.name,
                    company: profileData.company,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.log('Tracking failed:', error);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new DemoriLinkedInIntegration());
} else {
    new DemoriLinkedInIntegration();
}