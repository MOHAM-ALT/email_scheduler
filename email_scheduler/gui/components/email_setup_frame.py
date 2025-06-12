# gui/components/email_setup_frame.py
"""
Email Setup Frame - Email Configuration Component
Handles email list loading, content creation, and validation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import logging
from pathlib import Path
from ..utils.gui_utils import GuiUtils

logger = logging.getLogger(__name__)

class EmailSetupFrame:
    """Email setup and configuration component"""
    
    def __init__(self, parent, app_manager, config_manager):
        self.parent = parent
        self.app_manager = app_manager
        self.config_manager = config_manager
        
        # Create main frame
        self.frame = tk.Frame(parent, bg='#f5f6fa')
        
        # UI elements
        self.file_path_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.body_text = None
        self.attachment_vars = [tk.StringVar(), tk.StringVar()]
        
        # Create email setup interface
        self._create_interface()
        
        # Load default values
        self._load_defaults()
    
    def _create_interface(self):
        """Create email setup interface"""
        try:
            # File selection section
            file_section = GuiUtils.create_label_frame(self.frame, "📁 Email List File")
            file_section.pack(fill='x', padx=20, pady=10)
            
            file_frame = tk.Frame(file_section, bg='white')
            file_frame.pack(fill='x', padx=20, pady=15)
            
            # File selection
            GuiUtils.create_styled_button(
                file_frame,
                "📂 Select Excel File",
                command=self._select_file,
                style="default"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                file_frame,
                "📋 View Sample Format",
                command=self._show_sample_format,
                style="secondary"
            ).pack(side='left', padx=5)
            
            # File status
            self.file_status_label = tk.Label(
                file_section,
                text="No file selected",
                font=('Segoe UI', 10),
                bg='white',
                fg='#7f8c8d'
            )
            self.file_status_label.pack(pady=10)
            
            # Email content section
            content_section = GuiUtils.create_label_frame(self.frame, "✉️ Email Content")
            content_section.pack(fill='both', expand=True, padx=20, pady=10)
            
            content_frame = tk.Frame(content_section, bg='white')
            content_frame.pack(fill='both', expand=True, padx=20, pady=15)
            
            # Subject
            tk.Label(
                content_frame,
                text="Subject:",
                font=('Segoe UI', 10, 'bold'),
                bg='white'
            ).grid(row=0, column=0, sticky='w', pady=5)
            
            subject_entry = tk.Entry(
                content_frame,
                textvariable=self.subject_var,
                font=('Segoe UI', 10),
                width=80
            )
            subject_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=10)
            
            # Message body
            tk.Label(
                content_frame,
                text="Message:",
                font=('Segoe UI', 10, 'bold'),
                bg='white'
            ).grid(row=1, column=0, sticky='nw', pady=5)
            
            self.body_text = scrolledtext.ScrolledText(
                content_frame,
                font=('Segoe UI', 10),
                width=80,
                height=10,
                wrap='word'
            )
            self.body_text.grid(row=1, column=1, sticky='ew', pady=5, padx=10)
            
            content_frame.columnconfigure(1, weight=1)
            
            # Attachments section
            attachments_section = GuiUtils.create_label_frame(self.frame, "📎 PDF Attachments")
            attachments_section.pack(fill='x', padx=20, pady=10)
            
            for i in range(2):
                att_frame = tk.Frame(attachments_section, bg='white')
                att_frame.pack(fill='x', padx=20, pady=8)
                
                GuiUtils.create_styled_button(
                    att_frame,
                    f"📄 Add PDF File {i+1}",
                    command=lambda idx=i: self._add_attachment(idx),
                    style="danger"
                ).pack(side='left')
                
                att_label = tk.Label(
                    att_frame,
                    textvariable=self.attachment_vars[i],
                    font=('Segoe UI', 10),
                    bg='white',
                    fg='#7f8c8d'
                )
                att_label.pack(side='left', padx=20)
            
            # Actions section
            actions_section = GuiUtils.create_label_frame(self.frame, "🔧 Actions")
            actions_section.pack(fill='x', padx=20, pady=10)
            
            actions_frame = tk.Frame(actions_section, bg='white')
            actions_frame.pack(pady=15)
            
            GuiUtils.create_styled_button(
                actions_frame,
                "🔍 Validate Emails",
                command=self._validate_emails,
                style="default"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                actions_frame,
                "💾 Save Template",
                command=self._save_template,
                style="success"
            ).pack(side='left', padx=5)
            
            GuiUtils.create_styled_button(
                actions_frame,
                "📂 Load Template",
                command=self._load_template,
                style="secondary"
            ).pack(side='left', padx=5)
            
        except Exception as e:
            logger.error(f"Error creating email setup interface: {e}")
    
    def _load_defaults(self):
        """Load default values from configuration"""
        try:
            if self.config_manager:
                email_settings = self.config_manager.get_email_settings()
                self.subject_var.set(email_settings.default_subject)
                if self.body_text:
                    self.body_text.insert('1.0', email_settings.default_body)
                
                # Update attachment labels
                for i in range(2):
                    self.attachment_vars[i].set(f"No PDF {i+1} selected")
                    
        except Exception as e:
            logger.error(f"Error loading defaults: {e}")
    
    def _select_file(self):
        """Select email list file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Email List File",
                filetypes=[
                    ("Excel files", "*.xlsx *.xls"),
                    ("CSV files", "*.csv"),
                    ("Text files", "*.txt"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                self.file_path_var.set(file_path)
                self._load_email_file(file_path)
                
        except Exception as e:
            logger.error(f"Error selecting file: {e}")
            messagebox.showerror("Error", f"Failed to select file: {e}")
    
    def _load_email_file(self, file_path):
        """Load and process email file"""
        try:
            self.file_status_label.config(text="Loading emails...", fg='#f39c12')
            
            # Load emails using email processor
            email_processor = self.app_manager.get_email_processor()
            if email_processor:
                result = email_processor.load_emails_from_file(file_path)
                
                if result.success:
                    filename = Path(file_path).name
                    status_text = f"✅ Loaded: {filename} ({result.valid_emails} valid emails)"
                    self.file_status_label.config(text=status_text, fg='#27ae60')
                    
                    # Show summary dialog
                    summary = f"""Email File Loaded Successfully!

File: {filename}
Total Emails: {result.processed_count}
Valid Emails: {result.valid_emails}
Invalid Emails: {result.invalid_emails}
Duplicates Removed: {result.duplicates_removed}"""
                    
                    messagebox.showinfo("Success", summary)
                    
                else:
                    self.file_status_label.config(text=f"❌ Error: {result.message}", fg='#e74c3c')
                    messagebox.showerror("Error", f"Failed to load emails: {result.message}")
            else:
                self.file_status_label.config(text="❌ Email processor not available", fg='#e74c3c')
                
        except Exception as e:
            logger.error(f"Error loading email file: {e}")
            self.file_status_label.config(text=f"❌ Error loading file", fg='#e74c3c')
            messagebox.showerror("Error", f"Failed to load email file: {e}")
    
    def _show_sample_format(self):
        """Show sample file format dialog"""
        try:
            sample_dialog = tk.Toplevel(self.parent)
            sample_dialog.title("Email File Format Examples")
            sample_dialog.geometry("600x500")
            sample_dialog.transient(self.parent)
            sample_dialog.grab_set()
            
            GuiUtils.center_window(sample_dialog, 600, 500)
            
            # Create notebook for different formats
            notebook = ttk.Notebook(sample_dialog)
            notebook.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Excel format
            excel_frame = tk.Frame(notebook, bg='white')
            notebook.add(excel_frame, text="Excel Format")
            
            excel_text = tk.Text(excel_frame, font=('Consolas', 10), wrap='word')
            excel_text.pack(fill='both', expand=True, padx=15, pady=15)
            
            excel_content = """Excel File Format (.xlsx or .xls):

Column A (Email Addresses):
user1@example.com
user2@company.org
admin@domain.net
contact@business.com
info@organization.org

Requirements:
• Put emails in the first column (Column A)
• One email per row
• No headers required
• Save as .xlsx or .xls format
• Maximum file size: 100MB

The application will automatically:
• Validate all email addresses
• Remove duplicates
• Filter out invalid emails
• Generate detailed statistics"""
            
            excel_text.insert('1.0', excel_content)
            excel_text.config(state='disabled')
            
            # CSV format
            csv_frame = tk.Frame(notebook, bg='white')
            notebook.add(csv_frame, text="CSV Format")
            
            csv_text = tk.Text(csv_frame, font=('Consolas', 10), wrap='word')
            csv_text.pack(fill='both', expand=True, padx=15, pady=15)
            
            csv_content = """CSV File Format (.csv):

File content:
user1@example.com
user2@company.org
admin@domain.net
contact@business.com

Or with comma separation:
user1@example.com,
user2@company.org,
admin@domain.net,

Requirements:
• Emails in first column
• Comma, semicolon, or tab separated
• UTF-8 encoding recommended
• One email per line"""
            
            csv_text.insert('1.0', csv_content)
            csv_text.config(state='disabled')
            
            # Close button
            GuiUtils.create_styled_button(
                sample_dialog,
                "Close",
                command=sample_dialog.destroy,
                style="secondary"
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing sample format: {e}")
    
    def _add_attachment(self, index):
        """Add PDF attachment"""
        try:
            file_path = filedialog.askopenfilename(
                title=f"Select PDF File {index + 1}",
                filetypes=[
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                if not file_path.lower().endswith('.pdf'):
                    messagebox.showwarning("Warning", "Please select a PDF file")
                    return
                
                if not Path(file_path).exists():
                    messagebox.showerror("Error", "Selected file does not exist")
                    return
                
                # Check file size (25MB limit)
                file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
                if file_size > 25:
                    messagebox.showwarning("Warning", f"File size ({file_size:.1f}MB) exceeds 25MB limit")
                    return
                
                filename = Path(file_path).name
                self.attachment_vars[index].set(f"✅ {filename} ({file_size:.1f}MB)")
                
                logger.info(f"Added attachment {index + 1}: {filename}")
                
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            messagebox.showerror("Error", f"Failed to add attachment: {e}")
    
    def _validate_emails(self):
        """Validate loaded email list"""
        try:
            email_processor = self.app_manager.get_email_processor()
            if not email_processor:
                messagebox.showwarning("Warning", "Email processor not available")
                return
            
            stats = email_processor.get_statistics()
            if stats.get('total_emails', 0) == 0:
                messagebox.showwarning("Warning", "No emails loaded. Please select an email file first.")
                return
            
            # Show validation results
            validation_dialog = tk.Toplevel(self.parent)
            validation_dialog.title("Email Validation Results")
            validation_dialog.geometry("500x400")
            validation_dialog.transient(self.parent)
            validation_dialog.grab_set()
            
            GuiUtils.center_window(validation_dialog, 500, 400)
            
            # Create validation summary
            summary_frame = GuiUtils.create_label_frame(validation_dialog, "Validation Summary")
            summary_frame.pack(fill='x', padx=20, pady=10)
            
            summary_text = f"""Total Emails: {stats.get('total_emails', 0)}
Valid Emails: {stats.get('processing_stats', {}).get('valid_emails', 0)}
Invalid Emails: {stats.get('processing_stats', {}).get('invalid_emails', 0)}
Duplicates Removed: {stats.get('processing_stats', {}).get('duplicates_removed', 0)}

Validation Status: {"✅ Complete" if stats.get('total_emails', 0) > 0 else "❌ No data"}"""
            
            tk.Label(
                summary_frame,
                text=summary_text,
                font=('Consolas', 10),
                bg='white',
                justify='left'
            ).pack(padx=20, pady=15)
            
            # Close button
            GuiUtils.create_styled_button(
                validation_dialog,
                "Close",
                command=validation_dialog.destroy,
                style="secondary"
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error validating emails: {e}")
            messagebox.showerror("Error", f"Failed to validate emails: {e}")
    
    def _save_template(self):
        """Save email template"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Email Template",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                template_data = {
                    'subject': self.subject_var.get(),
                    'body': self.body_text.get('1.0', tk.END).strip(),
                    'attachments': [var.get() for var in self.attachment_vars if var.get() and not var.get().startswith("No PDF")],
                    'created_date': datetime.now().isoformat()
                }
                
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", "Email template saved successfully")
                
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            messagebox.showerror("Error", f"Failed to save template: {e}")
    
    def _load_template(self):
        """Load email template"""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Email Template",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                # Load template data
                self.subject_var.set(template_data.get('subject', ''))
                
                if self.body_text:
                    self.body_text.delete('1.0', tk.END)
                    self.body_text.insert('1.0', template_data.get('body', ''))
                
                messagebox.showinfo("Success", "Email template loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            messagebox.showerror("Error", f"Failed to load template: {e}")
    
    def get_email_data(self):
        """Get current email configuration data"""
        try:
            return {
                'file_path': self.file_path_var.get(),
                'subject': self.subject_var.get(),
                'body': self.body_text.get('1.0', tk.END).strip() if self.body_text else '',
                'attachments': [
                    var.get() for var in self.attachment_vars 
                    if var.get() and not var.get().startswith("No PDF") and not var.get().startswith("✅")
                ]
            }
        except Exception as e:
            logger.error(f"Error getting email data: {e}")
            return {}
    
    def validate_emails(self):
        """Public method to validate emails"""
        self._validate_emails()
    
    def refresh(self):
        """Refresh email setup data"""
        try:
            email_processor = self.app_manager.get_email_processor()
            if email_processor:
                stats = email_processor.get_statistics()
                if stats.get('total_emails', 0) > 0:
                    status_text = f"✅ {stats.get('processing_stats', {}).get('valid_emails', 0)} valid emails loaded"
                    self.file_status_label.config(text=status_text, fg='#27ae60')
        except Exception as e:
            logger.error(f"Error refreshing email setup: {e}")
    
    def cleanup(self):
        """Cleanup email setup resources"""
        pass