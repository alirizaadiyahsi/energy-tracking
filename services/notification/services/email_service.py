from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl
from typing import Optional, Dict, Any, List
from core.config import settings
import logging
import jinja2
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL
        
        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent / "templates"
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def send_email(
        self,
        recipient: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = recipient
            msg["Subject"] = subject

            # If template is specified, render it
            if template_name and template_data:
                try:
                    template = self.template_env.get_template(f"{template_name}.html")
                    html_message = template.render(**template_data)
                    
                    # Try to get text version
                    try:
                        text_template = self.template_env.get_template(f"{template_name}.txt")
                        message = text_template.render(**template_data)
                    except jinja2.TemplateNotFound:
                        # Use HTML stripped of tags as fallback
                        import re
                        message = re.sub(r'<[^>]+>', '', html_message)
                        
                except jinja2.TemplateNotFound:
                    logger.warning(f"Template {template_name} not found, using plain message")

            # Add text part
            text_part = MIMEText(message, "plain")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, "html")
                msg.attach(html_part)

            # Add attachments if any
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)

            # Send email
            context = ssl.create_default_context()
            
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient}")
            return True

        except Exception as exc:
            logger.error(f"Failed to send email to {recipient}: {exc}")
            return False

    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """
        Add attachment to email message
        """
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            
            filename = Path(file_path).name
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )

            msg.attach(part)
            
        except Exception as exc:
            logger.error(f"Failed to add attachment {file_path}: {exc}")

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        html_message: Optional[str] = None,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Send email to multiple recipients
        """
        results = {}
        
        for recipient in recipients:
            success = self.send_email(
                recipient=recipient,
                subject=subject,
                message=message,
                html_message=html_message,
                template_name=template_name,
                template_data=template_data
            )
            results[recipient] = success
            
        return results

    def test_connection(self) -> bool:
        """
        Test SMTP connection
        """
        try:
            context = ssl.create_default_context()
            
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.username, self.password)
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
                    
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as exc:
            logger.error(f"SMTP connection test failed: {exc}")
            return False
