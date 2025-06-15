// DEMORI Gmail Scheduler Pro - OAuth Authentication Handler
class DemoriOAuth {
    constructor() {
        this.init();
    }

    init() {
        this.updateStep(1);
        this.updateStatus('Preparing authentication...');
        
        // Start OAuth flow
        setTimeout(() => {
            this.startOAuthFlow();
        }, 1500);
    }

    updateStep(stepNumber) {
        // Reset all steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        // Mark completed steps
        for (let i = 1; i < stepNumber; i++) {
            document.getElementById(`step${i}`).classList.add('completed');
        }
        
        // Mark current step as active
        if (stepNumber <= 3) {
            document.getElementById(`step${stepNumber}`).classList.add('active');
        }
    }

    updateStatus(message) {
        document.getElementById('auth-status').textContent = message;
    }

    async startOAuthFlow() {
        try {
            this.updateStep(1);
            this.updateStatus('Redirecting to Google...');
            
            // Get OAuth URL from extension
            const response = await chrome.runtime.sendMessage({
                action: 'getOAuthUrl'
            });
            
            if (response.authUrl) {
                this.updateStep(2);
                this.updateStatus('Please grant permissions in the popup window...');
                
                // Redirect to Google OAuth
                window.location.href = response.authUrl;
            } else {
                throw new Error('Failed to get OAuth URL');
            }
            
        } catch (error) {
            console.error('OAuth flow error:', error);
            this.updateStatus('Authentication failed. Please try again.');
        }
    }

    // Handle OAuth callback
    handleCallback() {
        try {
            const urlParams = new URLSearchParams(window.location.hash.substring(1));
            const accessToken = urlParams.get('access_token');
            const error = urlParams.get('error');
            
            if (error) {
                throw new Error(`OAuth error: ${error}`);
            }
            
            if (accessToken) {
                this.updateStep(3);
                this.updateStatus('Authentication successful! Completing setup...');
                
                // Send token to extension
                chrome.runtime.sendMessage({
                    action: 'saveAuthToken',
                    token: accessToken
                }, (response) => {
                    if (response.success) {
                        this.updateStatus('Setup complete! You can now close this window.');
                        
                        // Close window after delay
                        setTimeout(() => {
                            window.close();
                        }, 2000);
                    }
                });
            }
            
        } catch (error) {
            console.error('Callback handling error:', error);
            this.updateStatus('Authentication failed. Please try again.');
        }
    }
}

// Initialize OAuth handler
document.addEventListener('DOMContentLoaded', () => {
    const oauth = new DemoriOAuth();
    
    // Check if this is a callback
    if (window.location.hash.includes('access_token')) {
        oauth.handleCallback();
    }
});