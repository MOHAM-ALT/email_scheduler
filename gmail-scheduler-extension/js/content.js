// DEMORI Gmail Scheduler Pro - Content Script for Gmail Integration
class DemoriGmailIntegration {
    constructor() {
        this.init();
    }

    init() {
        console.log('DEMORI Gmail Scheduler Pro loaded in Gmail');
        this.injectSchedulerButton();
        this.observeGmailChanges();
    }

    injectSchedulerButton() {
        // Wait for Gmail to load
        this.waitForElement('[role="button"][aria-label*="Send"]', (sendButton) => {
            if (sendButton && !document.getElementById('demori-scheduler-btn')) {
                this.addSchedulerButton(sendButton);
            }
        });
    }

    addSchedulerButton(sendButton) {
        const schedulerBtn = document.createElement('button');
        schedulerBtn.id = 'demori-scheduler-btn';
        schedulerBtn.type = 'button';
        schedulerBtn.innerHTML = `
            <span style="margin-right: 5px;">⏰</span>
            Schedule with DEMORI
        `;
        
        schedulerBtn.style.cssText = `
            margin-left: 10px;
            padding: 8px 16px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        `;
        
        schedulerBtn.addEventListener('mouseenter', () => {
            schedulerBtn.style.transform = 'translateY(-2px)';
            schedulerBtn.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
        });
        
        schedulerBtn.addEventListener('mouseleave', () => {
            schedulerBtn.style.transform = 'translateY(0)';
            schedulerBtn.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
        });
        
        schedulerBtn.addEventListener('click', () => {
            this.openSchedulerFromCompose();
        });
        
        // Insert button next to send button
        sendButton.parentNode.insertBefore(schedulerBtn, sendButton.nextSibling);
    }

    openSchedulerFromCompose() {
        // Extract email content from Gmail compose
        const emailData = this.extractComposeData();
        
        // Open extension popup with pre-filled data
        chrome.runtime.sendMessage({
            action: 'openScheduler',
            data: emailData
        });
    }

    extractComposeData() {
        const subject = document.querySelector('[name="subjectbox"]')?.value || '';
        const recipients = this.extractRecipients();
        const body = this.extractEmailBody();
        
        return {
            subject,
            recipients,
            body
        };
    }

    extractRecipients() {
        const recipients = [];
        
        // Extract TO recipients
        const toFields = document.querySelectorAll('[email]');
        toFields.forEach(field => {
            const email = field.getAttribute('email');
            const name = field.getAttribute('name') || '';
            if (email) {
                recipients.push({ email, name, type: 'to' });
            }
        });
        
        return recipients;
    }

    extractEmailBody() {
        const bodyElement = document.querySelector('[role="textbox"][aria-label*="Message Body"]');
        return bodyElement ? bodyElement.innerText : '';
    }

    observeGmailChanges() {
        // Watch for Gmail interface changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    // Re-inject button if compose window opens
                    setTimeout(() => this.injectSchedulerButton(), 1000);
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    waitForElement(selector, callback, timeout = 10000) {
        const startTime = Date.now();
        
        const checkElement = () => {
            const element = document.querySelector(selector);
            if (element) {
                callback(element);
            } else if (Date.now() - startTime < timeout) {
                setTimeout(checkElement, 500);
            }
        };
        
        checkElement();
    }
}

// Initialize when Gmail loads
if (window.location.hostname === 'mail.google.com') {
    new DemoriGmailIntegration();
}