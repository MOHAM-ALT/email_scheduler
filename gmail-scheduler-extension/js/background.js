// DEMORI Gmail Scheduler Pro - Background Service Worker
class DemoriBackgroundService {
    constructor() {
        this.campaigns = [];
        this.isProcessing = false;
        this.init();
    }

    init() {
        chrome.runtime.onInstalled.addListener(() => {
            console.log('DEMORI Gmail Scheduler Pro installed');
            this.setupAlarms();
        });

        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async response
        });

        chrome.alarms.onAlarm.addListener((alarm) => {
            this.handleAlarm(alarm);
        });

        // Load campaigns on startup
        this.loadCampaigns();
    }

    setupAlarms() {
        // Check for emails to send every minute
        chrome.alarms.create('emailCheck', { 
            periodInMinutes: 1 
        });
        
        // Daily cleanup
        chrome.alarms.create('dailyCleanup', { 
            periodInMinutes: 1440 // 24 hours
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'scheduleCampaign':
                    await this.scheduleCampaign(request.campaign);
                    sendResponse({ success: true });
                    break;
                    
                case 'pauseCampaign':
                    await this.pauseCampaign(request.campaignId);
                    sendResponse({ success: true });
                    break;
                    
                case 'deleteCampaign':
                    await this.deleteCampaign(request.campaignId);
                    sendResponse({ success: true });
                    break;
                    
                case 'getCampaigns':
                    const campaigns = await this.getCampaigns();
                    sendResponse({ campaigns });
                    break;
                    
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background message error:', error);
            sendResponse({ error: error.message });
        }
    }

    async handleAlarm(alarm) {
        switch (alarm.name) {
            case 'emailCheck':
                await this.processScheduledEmails();
                break;
                
            case 'dailyCleanup':
                await this.cleanupOldCampaigns();
                break;
        }
    }

    async scheduleCampaign(campaign) {
        try {
            // Save campaign to storage
            await this.loadCampaigns();
            this.campaigns.push(campaign);
            await chrome.storage.local.set({ campaigns: this.campaigns });
            
            console.log(`Campaign scheduled: ${campaign.name} with ${campaign.emails.length} emails`);
            
            // Schedule individual email alarms
            campaign.emails.forEach((email, index) => {
                const alarmName = `email_${campaign.id}_${email.id}`;
                const scheduledTime = new Date(email.scheduledTime);
                
                chrome.alarms.create(alarmName, {
                    when: scheduledTime.getTime()
                });
            });
            
        } catch (error) {
            console.error('Failed to schedule campaign:', error);
            throw error;
        }
    }

    async processScheduledEmails() {
        if (this.isProcessing) return;
        this.isProcessing = true;

        try {
            await this.loadCampaigns();
            const now = new Date();
            
            for (const campaign of this.campaigns) {
                if (campaign.status !== 'scheduled' && campaign.status !== 'running') continue;
                
                const pendingEmails = campaign.emails.filter(email => 
                    email.status === 'pending' && 
                    new Date(email.scheduledTime) <= now
                );
                
                for (const email of pendingEmails) {
                    await this.sendScheduledEmail(campaign, email);
                    
                    // Small delay between emails to avoid rate limiting
                    await this.sleep(1000);
                }
                
                // Update campaign status
                this.updateCampaignStatus(campaign);
            }
            
            // Save updated campaigns
            await chrome.storage.local.set({ campaigns: this.campaigns });
            
        } catch (error) {
            console.error('Email processing error:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    async sendScheduledEmail(campaign, email) {
        try {
            // Get Gmail auth token
            const authData = await chrome.storage.local.get(['gmailAuth']);
            if (!authData.gmailAuth?.accessToken) {
                throw new Error('Gmail not authenticated');
            }

            // Prepare email data
            const emailData = this.prepareEmailData(campaign, email);
            
            // Send email via Gmail API
            const response = await this.sendGmailMessage(authData.gmailAuth.accessToken, emailData);
            
            if (response.ok) {
                email.status = 'sent';
                email.sentTime = new Date().toISOString();
                email.gmailId = (await response.json()).id;
                
                console.log(`Email sent successfully: ${email.id}`);
            } else {
                throw new Error(`Gmail API error: ${response.status}`);
            }
            
        } catch (error) {
            email.status = 'failed';
            email.error = error.message;
            console.error(`Failed to send email ${email.id}:`, error);
        }
    }

    prepareEmailData(campaign, email) {
        let message = campaign.message;
        
        // Personalization
        if (campaign.settings.personalization) {
            email.recipients.forEach(recipient => {
                if (recipient.name) {
                    message = message.replace(/\{\{name\}\}/g, recipient.name);
                }
            });
        }
        
        // Prepare recipients based on email type
        let to = '';
        let cc = '';
        let bcc = '';
        
        const recipientEmails = email.recipients.map(r => r.email).join(',');
        
        switch (campaign.emailType) {
            case 'to':
                to = recipientEmails;
                break;
            case 'cc':
                cc = recipientEmails;
                break;
            case 'bcc':
            default:
                bcc = recipientEmails;
                break;
        }
        
        // Create email message
        const emailContent = [
            `To: ${to}`,
            cc ? `Cc: ${cc}` : '',
            bcc ? `Bcc: ${bcc}` : '',
            `Subject: ${campaign.subject}`,
            '',
            message
        ].filter(line => line !== '').join('\r\n');
        
        return {
            raw: btoa(unescape(encodeURIComponent(emailContent)))
        };
    }

    async sendGmailMessage(accessToken, emailData) {
        return fetch('https://www.googleapis.com/gmail/v1/users/me/messages/send', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(emailData)
        });
    }

    updateCampaignStatus(campaign) {
        const totalEmails = campaign.emails.length;
        const sentEmails = campaign.emails.filter(e => e.status === 'sent').length;
        const failedEmails = campaign.emails.filter(e => e.status === 'failed').length;
        const pendingEmails = campaign.emails.filter(e => e.status === 'pending').length;
        
        if (sentEmails + failedEmails === totalEmails) {
            campaign.status = 'completed';
        } else if (sentEmails > 0) {
            campaign.status = 'running';
        }
        
        campaign.progress = {
            total: totalEmails,
            sent: sentEmails,
            failed: failedEmails,
            pending: pendingEmails,
            percentage: Math.round((sentEmails / totalEmails) * 100)
        };
    }

    async loadCampaigns() {
        const result = await chrome.storage.local.get(['campaigns']);
        this.campaigns = result.campaigns || [];
    }

    async getCampaigns() {
        await this.loadCampaigns();
        return this.campaigns;
    }

    async pauseCampaign(campaignId) {
        await this.loadCampaigns();
        const campaign = this.campaigns.find(c => c.id == campaignId);
        if (campaign) {
            campaign.status = 'paused';
            await chrome.storage.local.set({ campaigns: this.campaigns });
        }
    }

    async deleteCampaign(campaignId) {
        await this.loadCampaigns();
        this.campaigns = this.campaigns.filter(c => c.id != campaignId);
        await chrome.storage.local.set({ campaigns: this.campaigns });
        
        // Clear related alarms
        const alarms = await chrome.alarms.getAll();
        alarms.forEach(alarm => {
            if (alarm.name.includes(`_${campaignId}_`)) {
                chrome.alarms.clear(alarm.name);
            }
        });
    }

    async cleanupOldCampaigns() {
        await this.loadCampaigns();
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        
        this.campaigns = this.campaigns.filter(campaign => {
            const campaignDate = new Date(campaign.createdAt);
            return campaignDate > thirtyDaysAgo || campaign.status !== 'completed';
        });
        
        await chrome.storage.local.set({ campaigns: this.campaigns });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize background service
new DemoriBackgroundService();