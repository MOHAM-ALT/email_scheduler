// DEMORI Gmail Scheduler Pro - Main Popup Script
class DemoriScheduler {
    constructor() {
        this.currentSection = 'scheduler';
        this.isAuthenticated = false;
        this.recipients = [];
        this.campaigns = [];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.setupHeaderAnimation();
        await this.checkAuthentication();
        this.loadSavedData();
        this.updatePreview();
        setInterval(() => this.updatePreview(), 1000);
    }

    setupEventListeners() {
        // Authentication
        document.getElementById('auth-btn').addEventListener('click', () => this.authenticateGmail());
        
        // Form inputs
        document.getElementById('recipients').addEventListener('input', () => this.updateRecipientCount());
        document.getElementById('subject').addEventListener('input', () => this.updateCharCount('subject', 100));
        document.getElementById('message').addEventListener('input', () => this.updateCharCount('message'));
        document.getElementById('distribution-mode').addEventListener('change', () => this.toggleCustomRate());
        
        // Buttons
        document.getElementById('preview-btn').addEventListener('click', () => this.previewCampaign());
        document.getElementById('schedule-btn').addEventListener('click', () => this.scheduleCampaign());
        document.getElementById('reset-settings').addEventListener('click', () => this.resetSettings());
        
        // Set default date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById('start-date').value = tomorrow.toISOString().split('T')[0];
    }

    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });
    }

    setupHeaderAnimation() {
        const content = document.querySelector('.content-wrapper');
        const header = document.getElementById('header');
        
        content.addEventListener('scroll', () => {
            if (content.scrollTop > 20) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    async checkAuthentication() {
        try {
            const result = await chrome.storage.local.get(['gmailAuth']);
            this.isAuthenticated = result.gmailAuth?.accessToken ? true : false;
            
            if (this.isAuthenticated) {
                this.showSchedulerInterface();
                this.updateConnectionStatus(true);
            } else {
                this.showAuthInterface();
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showAuthInterface();
        }
    }

    async authenticateGmail() {
        this.showLoading('Connecting to Gmail...');
        
        try {
            // Chrome Identity API for OAuth
            const authUrl = `https://accounts.google.com/oauth/authorize?` +
                `client_id=${chrome.runtime.getManifest().oauth2.client_id}&` +
                `response_type=token&` +
                `scope=${encodeURIComponent(chrome.runtime.getManifest().oauth2.scopes.join(' '))}&` +
                `redirect_uri=${encodeURIComponent(chrome.identity.getRedirectURL())}`;

            const result = await chrome.identity.launchWebAuthFlow({
                url: authUrl,
                interactive: true
            });

            const urlParams = new URLSearchParams(result.split('#')[1]);
            const accessToken = urlParams.get('access_token');

            if (accessToken) {
                await chrome.storage.local.set({
                    gmailAuth: {
                        accessToken: accessToken,
                        timestamp: Date.now()
                    }
                });

                this.isAuthenticated = true;
                this.showSchedulerInterface();
                this.updateConnectionStatus(true);
                this.showSuccess('Gmail connected successfully!');
            }
        } catch (error) {
            console.error('Authentication failed:', error);
            this.showError('Authentication failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    showAuthInterface() {
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('scheduler-section').classList.add('hidden');
    }

    showSchedulerInterface() {
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('scheduler-section').classList.remove('hidden');
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (connected) {
            statusEl.textContent = '🟢 Connected';
            statusEl.className = 'status-connected';
        } else {
            statusEl.textContent = '🔴 Disconnected';
            statusEl.className = 'status-disconnected';
        }
    }

    updateRecipientCount() {
        const recipients = document.getElementById('recipients').value.trim();
        const lines = recipients ? recipients.split('\n').filter(line => line.trim()) : [];
        
        this.recipients = lines.map(line => {
            const parts = line.split(',');
            return {
                email: parts[0]?.trim(),
                name: parts[1]?.trim() || ''
            };
        }).filter(r => r.email && r.email.includes('@'));

        document.getElementById('recipient-count').textContent = `${this.recipients.length} recipients`;
        document.getElementById('email-count').textContent = `${this.recipients.length} emails`;
        this.updatePreview();
    }

    updateCharCount(fieldId, maxLength = null) {
        const field = document.getElementById(fieldId);
        const counter = document.getElementById(`${fieldId}-count`);
        const length = field.value.length;
        
        if (maxLength) {
            counter.textContent = length;
            counter.style.color = length > maxLength * 0.9 ? '#e74c3c' : '#999';
        } else {
            counter.textContent = length;
        }
    }

    toggleCustomRate() {
        const mode = document.getElementById('distribution-mode').value;
        const customGroup = document.getElementById('custom-rate-group');
        
        if (mode === 'aggressive') {
            customGroup.style.display = 'block';
        } else {
            customGroup.style.display = 'none';
        }
        this.updatePreview();
    }

    updatePreview() {
        const recipientCount = this.recipients.length;
        const mode = document.getElementById('distribution-mode').value;
        
        let dailyRate;
        switch(mode) {
            case 'recommended':
                dailyRate = 499;
                break;
            case 'conservative':
                dailyRate = 50;
                break;
            case 'aggressive':
                dailyRate = parseInt(document.getElementById('custom-rate').value) || 100;
                break;
        }

        const duration = Math.ceil(recipientCount / dailyRate);
        const startDate = new Date(document.getElementById('start-date').value);
        const completionDate = new Date(startDate);
        completionDate.setDate(completionDate.getDate() + duration - 1);

        document.getElementById('preview-recipients').textContent = recipientCount.toLocaleString();
        document.getElementById('preview-daily').textContent = `${Math.min(dailyRate, recipientCount)}/day`;
        document.getElementById('preview-duration').textContent = `${duration} days`;
        document.getElementById('preview-completion').textContent = completionDate.toLocaleDateString();
    }

    async previewCampaign() {
        if (!this.validateForm()) return;

        const subject = document.getElementById('subject').value;
        const message = document.getElementById('message').value;
        const sampleRecipient = this.recipients[0];

        if (sampleRecipient) {
            const personalizedMessage = message.replace(/\{\{name\}\}/g, sampleRecipient.name || 'there');
            
            const previewWindow = window.open('', '_blank', 'width=600,height=400');
            previewWindow.document.write(`
                <html>
                <head>
                    <title>DEMORI - Email Preview</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { background: #667eea; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; border: 1px solid #ddd; }
                        .subject { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
                        .message { line-height: 1.6; white-space: pre-wrap; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>📧 Email Preview - DEMORI</h2>
                        <p>Preview for: ${sampleRecipient.email}</p>
                    </div>
                    <div class="content">
                        <div class="subject">Subject: ${subject}</div>
                        <div class="message">${personalizedMessage}</div>
                    </div>
                </body>
                </html>
            `);
        }
    }

    async scheduleCampaign() {
        if (!this.validateForm()) return;
        if (!this.isAuthenticated) {
            this.showError('Please connect your Gmail account first');
            return;
        }

        this.showLoading('Scheduling your campaign...');

        try {
            const campaignData = this.getCampaignData();
            const scheduledEmails = this.generateEmailSchedule(campaignData);
            
            // Save campaign
            const campaign = {
                id: Date.now(),
                ...campaignData,
                emails: scheduledEmails,
                status: 'scheduled',
                createdAt: new Date().toISOString()
            };

            this.campaigns.push(campaign);
            await chrome.storage.local.set({ campaigns: this.campaigns });

            // Send to background script for processing
            await chrome.runtime.sendMessage({
                action: 'scheduleCampaign',
                campaign: campaign
            });

            this.showSuccess(`🚀 Campaign scheduled successfully! ${scheduledEmails.length} emails will be sent over ${Math.ceil(scheduledEmails.length / campaignData.dailyRate)} days.`);
            
            // Clear form
            this.clearForm();
            
            // Switch to campaigns view
            setTimeout(() => {
                this.showSection('campaigns');
                this.loadCampaigns();
            }, 2000);

        } catch (error) {
            console.error('Campaign scheduling failed:', error);
            this.showError('Failed to schedule campaign. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    getCampaignData() {
        const mode = document.getElementById('distribution-mode').value;
        let dailyRate;
        
        switch(mode) {
            case 'recommended': dailyRate = 499; break;
            case 'conservative': dailyRate = 50; break;
            case 'aggressive': dailyRate = parseInt(document.getElementById('custom-rate').value) || 100; break;
        }

        return {
            name: `Campaign ${new Date().toLocaleDateString()}`,
            subject: document.getElementById('subject').value,
            message: document.getElementById('message').value,
            recipients: this.recipients,
            emailType: document.getElementById('email-type').value,
            dailyRate: Math.min(dailyRate, this.recipients.length),
            batchSize: parseInt(document.getElementById('batch-size').value),
            batchDelay: parseInt(document.getElementById('batch-delay').value),
            startDate: document.getElementById('start-date').value,
            startTime: document.getElementById('start-time').value,
            settings: {
                randomizeTiming: document.getElementById('randomize-timing').checked,
                avoidWeekends: document.getElementById('avoid-weekends').checked,
                personalization: document.getElementById('personalization').checked,
                trackOpens: document.getElementById('track-opens').checked,
                trackClicks: document.getElementById('track-clicks').checked
            }
        };
    }

    generateEmailSchedule(campaignData) {
        const emails = [];
        const startDateTime = new Date(`${campaignData.startDate}T${campaignData.startTime}`);
        let currentDate = new Date(startDateTime);
        let recipientIndex = 0;

        while (recipientIndex < campaignData.recipients.length) {
            // Skip weekends if enabled
            if (campaignData.settings.avoidWeekends && (currentDate.getDay() === 0 || currentDate.getDay() === 6)) {
                currentDate.setDate(currentDate.getDate() + 1);
                currentDate.setHours(parseInt(campaignData.startTime.split(':')[0]), parseInt(campaignData.startTime.split(':')[1]));
                continue;
            }

            let dailyCount = 0;
            let currentTime = new Date(currentDate);

            // Schedule emails for current day
            while (dailyCount < campaignData.dailyRate && recipientIndex < campaignData.recipients.length) {
                const batch = [];
                
                // Create batch
                for (let i = 0; i < campaignData.batchSize && recipientIndex < campaignData.recipients.length && dailyCount < campaignData.dailyRate; i++) {
                    batch.push(campaignData.recipients[recipientIndex]);
                    recipientIndex++;
                    dailyCount++;
                }

                if (batch.length > 0) {
                    // Add randomization if enabled
                    if (campaignData.settings.randomizeTiming) {
                        const randomMinutes = Math.floor(Math.random() * 10) - 5; // ±5 minutes
                        currentTime.setMinutes(currentTime.getMinutes() + randomMinutes);
                    }

                    emails.push({
                        id: `email_${Date.now()}_${emails.length}`,
                        scheduledTime: new Date(currentTime).toISOString(),
                        recipients: batch,
                        subject: campaignData.subject,
                        message: campaignData.message,
                        emailType: campaignData.emailType,
                        status: 'pending'
                    });

                    // Add delay between batches
                    currentTime.setMinutes(currentTime.getMinutes() + campaignData.batchDelay);
                }
            }

            // Move to next day
            currentDate.setDate(currentDate.getDate() + 1);
            currentDate.setHours(parseInt(campaignData.startTime.split(':')[0]), parseInt(campaignData.startTime.split(':')[1]));
        }

        return emails;
    }

    validateForm() {
        const recipients = document.getElementById('recipients').value.trim();
        const subject = document.getElementById('subject').value.trim();
        const message = document.getElementById('message').value.trim();

        if (!recipients) {
            this.showError('Please add recipients');
            return false;
        }

        if (!subject) {
            this.showError('Please add email subject');
            return false;
        }

        if (!message) {
            this.showError('Please add email message');
            return false;
        }

        if (this.recipients.length === 0) {
            this.showError('No valid email addresses found in recipients list');
            return false;
        }

        return true;
    }

    clearForm() {
        document.getElementById('recipients').value = '';
        document.getElementById('subject').value = '';
        document.getElementById('message').value = '';
        this.updateRecipientCount();
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        document.getElementById(`${sectionName}-section`).classList.remove('hidden');

        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        this.currentSection = sectionName;

        // Load section-specific data
        if (sectionName === 'campaigns') {
            this.loadCampaigns();
        }
    }

    async loadCampaigns() {
        try {
            const result = await chrome.storage.local.get(['campaigns']);
            this.campaigns = result.campaigns || [];
            this.renderCampaigns();
        } catch (error) {
            console.error('Failed to load campaigns:', error);
        }
    }

    renderCampaigns() {
        const container = document.getElementById('campaigns-list');
        
        if (this.campaigns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No campaigns yet</p>
                    <small>Create your first campaign in the Scheduler tab</small>
                </div>
            `;
            return;
        }

        container.innerHTML = this.campaigns.map(campaign => `
            <div class="campaign-card">
                <div class="campaign-header">
                    <h4>${campaign.name}</h4>
                    <span class="campaign-status status-${campaign.status}">${campaign.status}</span>
                </div>
                <div class="campaign-stats">
                    <div class="stat">
                        <span class="stat-label">Recipients:</span>
                        <span class="stat-value">${campaign.recipients.length}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Daily Rate:</span>
                        <span class="stat-value">${campaign.dailyRate}/day</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Progress:</span>
                        <span class="stat-value">${this.getCampaignProgress(campaign)}%</span>
                    </div>
                </div>
                <div class="campaign-actions">
                    <button onclick="scheduler.pauseCampaign('${campaign.id}')" class="btn-small btn-secondary">⏸️ Pause</button>
                    <button onclick="scheduler.deleteCampaign('${campaign.id}')" class="btn-small btn-danger">🗑️ Delete</button>
                </div>
            </div>
        `).join('');
    }

    getCampaignProgress(campaign) {
        const sentEmails = campaign.emails.filter(email => email.status === 'sent').length;
        return Math.round((sentEmails / campaign.emails.length) * 100);
    }

    resetSettings() {
        if (confirm('Reset all settings to default values?')) {
            document.getElementById('distribution-mode').value = 'recommended';
            document.getElementById('batch-size').value = '10';
            document.getElementById('batch-delay').value = '2';
            document.getElementById('randomize-timing').checked = true;
            document.getElementById('avoid-weekends').checked = true;
            document.getElementById('personalization').checked = true;
            document.getElementById('track-opens').checked = false;
            document.getElementById('track-clicks').checked = false;
            
            this.showSuccess('Settings reset to defaults');
        }
    }

    loadSavedData() {
        chrome.storage.local.get(['formData'], (result) => {
            if (result.formData) {
                const data = result.formData;
                if (data.recipients) document.getElementById('recipients').value = data.recipients;
                if (data.subject) document.getElementById('subject').value = data.subject;
                if (data.message) document.getElementById('message').value = data.message;
                
                this.updateRecipientCount();
            }
        });

        // Auto-save form data
        setInterval(() => {
            const formData = {
                recipients: document.getElementById('recipients').value,
                subject: document.getElementById('subject').value,
                message: document.getElementById('message').value
            };
            chrome.storage.local.set({ formData });
        }, 5000);
    }

    showLoading(text) {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.scheduler = new DemoriScheduler();
});

// Add notification animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .campaign-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .campaign-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .campaign-header h4 {
        margin: 0;
        color: #333;
    }
    
    .campaign-status {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-scheduled {
        background: #e3f2fd;
        color: #1976d2;
    }
    
    .status-running {
        background: #e8f5e8;
        color: #2e7d32;
    }
    
    .status-paused {
        background: #fff3e0;
        color: #f57c00;
    }
    
    .status-completed {
        background: #f3e5f5;
        color: #7b1fa2;
    }
    
    .campaign-stats {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
        font-size: 12px;
    }
    
    .stat {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    
    .stat-label {
        color: #666;
        font-weight: 500;
    }
    
    .stat-value {
        color: #333;
        font-weight: 600;
    }
    
    .campaign-actions {
        display: flex;
        gap: 8px;
    }
    
    .btn-small {
        padding: 6px 12px;
        font-size: 11px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-weight: 500;
    }
`;
document.head.appendChild(style);