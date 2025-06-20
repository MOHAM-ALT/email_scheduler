// LinkedIn Profile Data Extractor
class LinkedInExtractor {
    constructor() {
        this.profileData = {};
        this.isProfilePage = false;
        this.init();
    }

    init() {
        this.detectProfilePage();
        if (this.isProfilePage) {
            this.extractProfileData();
            this.setupMessageListener();
        }
    }

    detectProfilePage() {
        const currentUrl = window.location.href;
        this.isProfilePage = currentUrl.includes('/in/') || 
                           currentUrl.includes('/profile/view') ||
                           currentUrl.match(/linkedin\.com\/in\/[\w-]+/);
        
        if (this.isProfilePage) {
            console.log('Demori: LinkedIn profile detected');
        }
    }

    extractProfileData() {
        try {
            // Wait for page to load completely
            setTimeout(() => {
                this.profileData = {
                    name: this.extractName(),
                    title: this.extractTitle(),
                    company: this.extractCompany(),
                    location: this.extractLocation(),
                    profileUrl: window.location.href,
                    timestamp: new Date().toISOString(),
                    source: 'linkedin_profile'
                };

                // Store data for popup access
                chrome.storage.local.set({
                    'currentProfile': this.profileData,
                    'profileDetected': true
                });

                // Notify background script
                chrome.runtime.sendMessage({
                    action: 'profileDetected',
                    data: this.profileData
                });

            }, 2000);
        } catch (error) {
            console.error('Demori extraction error:', error);
        }
    }

    extractName() {
        const selectors = [
            'h1.text-heading-xlarge',
            'h1[data-anonymize="person-name"]',
            '.pv-text-details__left-panel h1',
            '.ph5 h1',
            '.pv-top-card-profile-picture + div h1'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                return this.cleanText(element.textContent);
            }
        }
        return 'Unknown';
    }

    extractTitle() {
        const selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '.ph5 .text-body-medium',
            '.pv-top-card-profile-picture + div .text-body-medium',
            '[data-anonymize="job-title"]'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                return this.cleanText(element.textContent);
            }
        }
        return 'Unknown';
    }

    extractCompany() {
        const selectors = [
            '.pv-text-details__right-panel .hoverable-link-text',
            '.experience-item .pv-entity__secondary-title',
            '.pv-top-card-v2-section__info .pv-text-details__right-panel button',
            '.inline-show-more-text button[aria-expanded] span[aria-hidden="true"]'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                const companyText = this.cleanText(element.textContent);
                if (!companyText.includes('Connect') && !companyText.includes('Message')) {
                    return companyText;
                }
            }
        }
        return 'Unknown';
    }

    extractLocation() {
        const selectors = [
            '.pv-text-details__left-panel .text-body-small.inline.t-black--light',
            '.ph5 .text-body-small.inline.t-black--light',
            '.pv-top-card-profile-picture + div .text-body-small.inline'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                return this.cleanText(element.textContent);
            }
        }
        return 'Unknown';
    }

    cleanText(text) {
        return text.replace(/\s+/g, ' ').trim();
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'getProfileData') {
                sendResponse({
                    success: true,
                    data: this.profileData,
                    isProfilePage: this.isProfilePage
                });
            }
            return true;
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new LinkedInExtractor();
    });
} else {
    new LinkedInExtractor();
}

// Handle navigation changes (SPA)
let lastUrl = location.href;
new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
        lastUrl = url;
        setTimeout(() => {
            new LinkedInExtractor();
        }, 1000);
    }
}).observe(document, { subtree: true, childList: true });