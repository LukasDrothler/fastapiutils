from email.mime.text import MIMEText
import logging
import smtplib
from .config import MailConfig

logger = logging.getLogger('uvicorn.error')


class MailManager:
    def __init__(self, mail_config: MailConfig):
        self.host = mail_config.smtp_server
        self.port = mail_config.smtp_port
        self.user = mail_config.smtp_user
        self.password = mail_config.smtp_password

        try:
            server = smtplib.SMTP(host=self.host, port=self.port)
            server.login(self.user, self.password)
            server.quit()
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise ValueError("Invalid SMTP configuration. Please check your settings.") from e

            

    def send_email_plain_text(self, content, subject, recipient):
        try:
            msg = MIMEText(content)
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = recipient
        except Exception as e:
            logger.error(f"Failed to create email message: {e}")
            raise
            
        try:
            # Create SMTP connection
            server = smtplib.SMTP(host=self.host, port=self.port)

            # Enable security
            server.starttls()
            
            # Login to server
            server.login(self.user, self.password)
            
            # Send email
            server.sendmail(self.user, [recipient], msg.as_string())
            
            # Close connection
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            logger.error(f"Parameters: host={self.host}, port={self.port}, user={self.user}, recipient={recipient}")
            raise