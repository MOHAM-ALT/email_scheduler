// DEMORI Contact Finder Pro - OAuth Authentication Handler
class DemoriOAuth {
    constructor() {
        this.apiEndpoint = 'https://your-api-domain.com/api';
        this.currentStep = 1;
        this.authInProgress = false;
        
        this.init();
    }

    init() {
        console.log('🔐 DEMORI OAuth Handler Initialized');
        
        this.updateStep(1);
        this.updateStatus('Preparing authentication...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Start authentication flow
        setTimeout(() => {
            this.startAuthFlow();
        }, 2000); // Give user time to read the interface
    }

    setupEventListeners() {
        // Login button
        document.getElementById('login-btn')?.addEventListener('click', () => {
            this.handleLogin();
        });

        // Register button  
        document.getElementById('register-btn')?.addEventListener('click', () => {
            this.handleRegister();
        });

        // Demo button
        document.getElementById('demo-btn')?.addEventListener('click', () => {
            this.handleDemo();
        });

        // Retry button
        document.getElementById('retry-auth-btn')?.addEventListener('click', () => {
            this.retryAuth();
        });

        // Close auth button
        document.getElementById('close-auth-btn')?.addEventListener('click', () => {
            this.closeAuth();
        });

        // Handle URL parameters (OAuth callback)
        this.handleOAuthCallback();
    }

    updateStep(stepNumber) {
        // Reset all steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        // Mark completed steps
        for (let i = 1; i < stepNumber; i++) {
            const step = document.getElementById(`step${i}`);
            if (step) {
                step.classList.add('completed');
                step.classList.add('step-transition');
            }
        }
        
        // Mark current step as active
        if (stepNumber <= 3) {
            const currentStep = document.getElementById(`step${stepNumber}`);
            if (currentStep) {
                currentStep.classList.add('active');
                currentStep.classList.add('step-transition');
            }
        }
        
        this.currentStep = stepNumber;
    }

    updateStatus(message) {
        const statusElement = document.getElementById('auth-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    async startAuthFlow() {
        try {
            this.updateStep(1);
            this.updateStatus('Checking authentication options...');
            
            // Check if user is already authenticated
            const authData = await this.checkExistingAuth();
            
            if (authData.authenticated) {
                this.updateStep(3);
                this.updateStatus('Already authenticated!');
                setTimeout(() => {
                    this.showSuccess('Welcome back! Your account is already connected.');
                }, 1000);
                return;
            }

            // Show authentication options
            setTimeout(() => {
                this.showAuthOptions();
            }, 1500);
            
        } catch (error) {
            console.error('Auth flow error:', error);
            this.showError('Failed to initialize authentication. Please try again.');
        }
    }

    async checkExistingAuth() {
        try {
            // Check local storage first
            const storage = await chrome.storage.local.get(['apiKey', 'userPlan', 'isAuthenticated']);
            
            if (storage.apiKey && storage.isAuthenticated) {
                // Verify with server
                const response = await fetch(`${this.apiEndpoint}/auth/verify`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${storage.apiKey}`
                    }
                });

                if (response.ok) {
                    const result = await response.json();
                    return { authenticated: true, user: result.user };
                }
            }

            return { authenticated: false };
            
        } catch (error) {
            console.error('Auth check error:', error);
            return { authenticated: false };
        }
    }

    showAuthOptions() {
        this.updateStep(2);
        this.updateStatus('Choose your authentication method');
        
        // Hide loading, show options
        document.querySelector('.auth-loading').style.display = 'none';
        document.getElementById('auth-actions').style.display = 'block';
        document.getElementById('auth-benefits').style.display = 'block';
    }

    async handleLogin() {
        if (this.authInProgress) return;
        this.authInProgress = true;

        try {
            this.showLoading('Redirecting to login...');
            
            // Generate OAuth state for security
            const state = this.generateState();
            await chrome.storage.local.set({ oauthState: state });
            
            // Construct OAuth URL
            const authUrl = this.buildAuthUrl('login', state);
            
            // Open OAuth flow in new tab
            chrome.tabs.create({ url: authUrl });
            
            // Start polling for completion
            this.startAuthPolling();
            
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Failed to start login process. Please try again.');
            this.authInProgress = false;
        }
    }

    async handleRegister() {
        if (this.authInProgress) return;
        this.authInProgress = true;

        try {
            this.showLoading('Redirecting to registration...');
            
            const state = this.generateState();
            await chrome.storage.local.set({ oauthState: state });
            
            const authUrl = this.buildAuthUrl('register', state);
            chrome.tabs.create({ url: authUrl });
            
            this.startAuthPolling();
            
        } catch (error) {
            console.error('Register error:', error);
            this.showError('Failed to start registration process. Please try again.');
            this.authInProgress = false;
        }
    }

    async handleDemo() {
        try {
            this.showLoading('Setting up demo account...');
            
            // Create demo account with limited features
            const demoCredentials = {
                type: 'demo',
                timestamp: new Date().toISOString()
            };

            const response = await fetch(`${this.apiEndpoint}/auth/demo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(demoCredentials)
            });

            if (response.ok) {
                const result = await response.json();
                
                await chrome.storage.local.set({
                    apiKey: result.apiKey,
                    userPlan: 'Demo',
                    userCredits: 5, // Limited demo credits
                    isAuthenticated: true
                });

                this.updateStep(3);
                this.showSuccess('Demo account created! You have 5 free searches to try DEMORI.');
                
            } else {
                throw new Error('Demo account creation failed');
            }
            
        } catch (error) {
            console.error('Demo error:', error);
            this.showError('Failed to create demo account. Please try again.');
        }
    }

    buildAuthUrl(action, state) {
        const baseUrl = 'https://your-website.com/auth';
        const params = new URLSearchParams({
            action: action,
            source: 'chrome_extension',
            state: state,
            redirect_uri: chrome.identity.getRedirectURL()
        });
        
        return `${baseUrl}?${params.toString()}`;
    }

    generateState() {
        // Generate cryptographically secure random state
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    startAuthPolling() {
        // Poll for authentication completion every 2 seconds
        const pollInterval = setInterval(async () => {
            try {
                const authData = await this.checkExistingAuth();
                
                if (authData.authenticated) {
                    clearInterval(pollInterval);
                    this.updateStep(3);
                    this.showSuccess('Authentication successful! Welcome to DEMORI.');
                    this.authInProgress = false;
                }
                
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);

        // Stop polling after 5 minutes
        setTimeout(() => {
            clearInterval(pollInterval);
            if (this.authInProgress) {
                this.showError('Authentication timed out. Please try again.');
                this.authInProgress = false;
            }
        }, 5 * 60 * 1000);
    }

    handleOAuthCallback() {
        // Check if this page was opened as OAuth callback
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');

        if (error) {
            this.showError(`Authentication failed: ${error}`);
            return;
        }

        if (code && state) {
            this.processOAuthCallback(code, state);
        }
    }

    async processOAuthCallback(code, state) {
        try {
            this.showLoading('Completing authentication...');
            
            // Verify state parameter
            const storage = await chrome.storage.local.get(['oauthState']);
            if (storage.oauthState !== state) {
                throw new Error('Invalid state parameter');
            }

            // Exchange code for access token
            const response = await fetch(`${this.apiEndpoint}/auth/callback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    state: state,
                    redirect_uri: chrome.identity.getRedirectURL()
                })
            });

            if (response.ok) {
                const result = await response.json();
                
                // Save authentication data
                await chrome.storage.local.set({
                    apiKey: result.apiKey,
                    userPlan: result.plan,
                    userCredits: result.credits,
                    isAuthenticated: true,
                    userEmail: result.user.email,
                    userName: result.user.name
                });

                // Clean up OAuth state
                await chrome.storage.local.remove(['oauthState']);

                this.updateStep(3);
                this.showSuccess(`Welcome ${result.user.name}! Your account has been connected successfully.`);
                
            } else {
                throw new Error('Failed to exchange authorization code');
            }
            
        } catch (error) {
            console.error('OAuth callback error:', error);
            this.showError('Failed to complete authentication. Please try again.');
        }
    }

    retryAuth() {
        // Reset and restart auth flow
        this.hideError();
        this.hideSuccess();
        this.authInProgress = false;
        this.currentStep = 1;
        
        document.querySelector('.auth-loading').style.display = 'block';
        document.getElementById('auth-actions').style.display = 'none';
        
        setTimeout(() => {
            this.startAuthFlow();
        }, 1000);
    }

    closeAuth() {
        // Close the auth window and return to extension
        window.close();
    }

    showLoading(message) {
        this.updateStatus(message);
        document.querySelector('.auth-loading').style.display = 'block';
        document.getElementById('auth-actions').style.display = 'none';
        document.getElementById('auth-benefits').style.display = 'none';
        this.hideSuccess();
        this.hideError();
    }

    showSuccess(message) {
        document.querySelector('.auth-loading').style.display = 'none';
        document.getElementById('auth-actions').style.display = 'none';
        document.getElementById('auth-benefits').style.display = 'none';
        this.hideError();
        
        const successElement = document.getElementById('auth-success');
        const successMessage = successElement.querySelector('p');
        
        if (successMessage) {
            successMessage.textContent = message;
        }
        
        successElement.style.display = 'block';
        successElement.classList.add('fade-in');
        
        // Notify parent extension of successful auth
        chrome.runtime.sendMessage({
            type: 'auth_success',
            message: message
        });
    }

    showError(message) {
        document.querySelector('.auth-loading').style.display = 'none';
        document.getElementById('auth-actions').style.display = 'none';
        document.getElementById('auth-benefits').style.display = 'none';
        this.hideSuccess();
        
        const errorElement = document.getElementById('auth-error');
        const errorMessage = errorElement.querySelector('#error-message');
        
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        
        errorElement.style.display = 'block';
        errorElement.classList.add('fade-in');
        
        this.authInProgress = false;
    }

    hideSuccess() {
        const successElement = document.getElementById('auth-success');
        successElement.style.display = 'none';
        successElement.classList.remove('fade-in');
    }

    hideError() {
        const errorElement = document.getElementById('auth-error');
        errorElement.style.display = 'none';
        errorElement.classList.remove('fade-in');
    }

    // Utility methods
    async trackAuthEvent(event, properties = {}) {
        try {
            await fetch(`${this.apiEndpoint}/analytics/auth`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    event: event,
                    properties: {
                        ...properties,
                        source: 'chrome_extension',
                        timestamp: new Date().toISOString(),
                        userAgent: navigator.userAgent
                    }
                })
            });
        } catch (error) {
            console.log('Analytics tracking failed:', error);
        }
    }

    async notifyExtension(type, data) {
        try {
            chrome.runtime.sendMessage({
                type: type,
                data: data
            });
        } catch (error) {
            console.log('Extension notification failed:', error);
        }
    }
}

// Add CSS animation classes
const style = document.createElement('style');
style.textContent = `
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Initialize OAuth handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DemoriOAuth();
});