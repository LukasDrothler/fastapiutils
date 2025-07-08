from email.mime.text import MIMEText
import logging
import smtplib
from .config import MailConfig

logger = logging.getLogger('uvicorn.error')


class MailManager:
    def __init__(self, mail_config: MailConfig):
        self.mail_config = mail_config

    def send_email_plain_text(self, content, subject, recipient):
        try:
            msg = MIMEText(content)
            msg['Subject'] = subject
            msg['From'] = self.mail_config.smtp_user
            msg['To'] = recipient
        except Exception as e:
            logger.error(f"Failed to create email message: {e}")
            raise

        try:
            with smtplib.SMTP(host=self.mail_config.smtp_server, port=self.mail_config.smtp_port) as server:
                server.starttls()  # Start TLS encryption
                server.login(self.mail_config.smtp_user, self.mail_config.smtp_password)
                server.sendmail(self.mail_config.smtp_user, [recipient], msg.as_string())
                server.quit()
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            raise