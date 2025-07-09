from email.mime.text import MIMEText
import logging
import os
import smtplib

logger = logging.getLogger('uvicorn.error')

class MailService:
    def __init__(self):
        if "SMTP_SERVER" in os.environ:
            self.host = os.environ["SMTP_SERVER"]
            logger.info(f"Using SMTP server '{self.host}' from environment variable 'SMTP_SERVER'")
        else:
            self.host = "localhost"
            logger.warning(f"Using SMTP server '{self.host}' since 'SMTP_SERVER' not set")
        
        if "SMTP_PORT" in os.environ:
            self.port = int(os.environ["SMTP_PORT"])
            logger.info(f"Using SMTP port '{self.port}' from environment variable 'SMTP_PORT'")
        else:
            self.port = 587
            logger.warning(f"Using SMTP port '{self.port}' since 'SMTP_PORT' not set")

        if "SMTP_USER" in os.environ:
            self.user = os.environ["SMTP_USER"]
            logger.info(f"Using SMTP user '{self.user}' from environment variable 'SMTP_USER'")
        else:
            logger.error("SMTP_USER environment variable not set, cannot send emails")
            raise ValueError("SMTP_USER environment variable is required for email sending")

        if "SMTP_PASSWORD" in os.environ:
            self.password = os.environ["SMTP_PASSWORD"]
            logger.info("Using SMTP password from environment variable 'SMTP_PASSWORD'")
        else:
            logger.error("SMTP_PASSWORD environment variable not set, cannot send emails")
            raise ValueError("SMTP_PASSWORD environment variable is required for email sending")  

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