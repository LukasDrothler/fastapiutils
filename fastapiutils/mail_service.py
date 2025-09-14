from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging
import os
import smtplib
import json

from fastapi import HTTPException, status

from .i18n_service import I18nService

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

        self._init_colors()


    def _init_colors(self):
        """Initialize default color cofiguration and override with custom config if provided"""
        _default_colors_file = os.path.join(os.path.dirname(__file__), "config", "colors.json")
        _default_color_config = self._json_to_dict(file_path=_default_colors_file)

        if "COLOR_CONFIG_FILE" in os.environ:
            _colors_file = os.environ["COLOR_CONFIG_FILE"]
            logger.info(f"Using color config file '{_colors_file}' from environment variable 'COLOR_CONFIG_FILE'")
            if os.path.exists(_colors_file):
                _custom_config = self._json_to_dict(file_path=_colors_file)
                self.colors = self._deep_merge_dicts(_default_color_config, _custom_config)
                return None
            else: logger.warning(f"Color configuration file does not exist: {_colors_file}")

        self.colors = _default_color_config
        return None

    
    def _deep_merge_dicts(self, default_dict: Dict[str, Any], custom_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with custom_dict values taking precedence"""
        result = default_dict.copy()
        
        for key, value in custom_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                # Override or add new key-value pair
                result[key] = value
        
        return result

    
    def _deep_merge_multiple_dicts(self, *dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge multiple dictionaries, with later dictionaries taking precedence"""
        result = {}
        for dict_item in dicts:
            if dict_item:  # Skip None or empty dictionaries
                result = self._deep_merge_dicts(result, dict_item)
        return result

    
    def _process_variable_references(self, variables: Dict[str, Any], max_iterations: int = 3) -> Dict[str, Any]:
        """Process variable references within variables (e.g., {app_name} in text)"""
        processed_variables = variables.copy()
        
        for iteration in range(max_iterations):
            changes_made = False
            
            for key, value in processed_variables.items():
                if isinstance(value, str):
                    original_value = value
                    
                    # Replace all variable references in this string
                    for var_key, var_value in processed_variables.items():
                        if var_key != key:  # Don't replace self-references
                            placeholder = f"{{{var_key}}}"
                            if placeholder in value:
                                value = value.replace(placeholder, str(var_value))
                    
                    if value != original_value:
                        processed_variables[key] = value
                        changes_made = True
                elif isinstance(value, dict):
                    # Recursively process nested dictionaries
                    processed_nested = self._process_variable_references(value, max_iterations=1)
                    if processed_nested != value:
                        processed_variables[key] = processed_nested
                        changes_made = True
            
            # If no changes were made in this iteration, we're done
            if not changes_made:
                break
        
        return processed_variables


    def _json_to_dict(self, file_path) -> Dict[str, Any]:
        """Load dict from separate JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
            return file_content
        except FileNotFoundError:
            logger.warning(f"JSON file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SON file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load SON file: {e}")
            return {}


    def _load_template(self, template_name: str, locale: str = "en") -> Optional[str]:
        """Load an HTML template file with locale support"""
        if "EMAIL_TEMPLATES_DIR" in os.environ:
            _templates_dir = os.environ["EMAIL_TEMPLATES_DIR"]
            logger.info(f"Using email templates directory '{_templates_dir}' from environment variable 'EMAIL_TEMPLATES_DIR'")
        else:
            _templates_dir = os.path.join(os.path.dirname(__file__), "templates")
            logger.info(f"Using default email templates directory since 'EMAIL_TEMPLATES_DIR' not set")
        
        # Try localized template first, then fall back to default
        template_path = os.path.join(_templates_dir, f"{template_name}.html")
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_name} (locale: {locale})")
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            logger.info(f"Loaded email template: {template_path}")
            return template_content
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return None


    def _render_template(
            self, template_content: str, variables: Dict[str, Any], 
            i18n_service: I18nService, template_name: str = None, locale: str = "en"
            ) -> str:
        """Render template with variables and configuration"""
        email_templates = i18n_service._translations[locale]["email"]
        app_config = i18n_service._translations[locale]["app_config"]

        # Add flattened colors from color configuration (new nested format)
        _config = {
            "app_name": app_config["app_name"],
            "app_owner": app_config["app_owner"],
            "contact_email": app_config["contact_email"],
            "logo_url": app_config["logo_url"],
            "primary_color": self.colors["primary"],
            "primary_shade_color": self.colors["primary-shade"],
            "primary_foreground_color": self.colors["primary-foreground"],
            "background_color": self.colors["background"],
            "card": self.colors["card"],
            "foreground_color": self.colors["foreground"],
            "muted_color": self.colors["muted"],
            "primary_foreground_color": self.colors["muted-foreground"],
            "border_color": self.colors["border"],
            "warning_background": self.colors["warning"]["background"],
            "warning_foreground_color": self.colors["warning"]["text"],
            "warning_border_color": self.colors["warning"]["border"],
            "warning_title_color": self.colors["warning"]["title"],
            "info_background": self.colors["info"]["background"],
            "info_foreground_color": self.colors["info"]["text"],
            "info_border_color": self.colors["info"]["border"],
        }
    
        # Get template text variables from i18n service
        text_variables = {}
        if template_name:
            template_config = email_templates[template_name]
            # Merge defaults with template-specific config (template config takes precedence)
            _config.update(template_config)
            # Merge shared content with template-specific content (template-specific takes precedence)
            # text_variables = {**email_templates["shared_content"], **email_templates[template_name]["content"]}
            text_variables = self._deep_merge_dicts(
                email_templates["shared_content"],
                email_templates[template_name]["content"]
            )
        
        # Merge all variables first: config defaults + text variables + user variables
        # Order matters: user variables should override text variables and config defaults
        all_variables = self._deep_merge_multiple_dicts(_config, text_variables, variables)
        
        # Process variable references within the merged variables (multiple passes if needed)
        all_variables = self._process_variable_references(all_variables)
        
        # Replace all variables in the template
        for key, value in all_variables.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))
        
        return template_content


    def send_email_html(self,
                        template_name: str,
                        variables: Dict[str, Any],
                        subject: str,
                        recipient: str,
                        i18n_service: I18nService,
                        locale: str = "en"
                        ) -> None:
        """Send email using template system with automatic fallback to plain text"""
        
        # Try HTML template first
        template_content = self._load_template(template_name, locale)
        if not template_content:
            raise ValueError(f"Template '{template_name}' not found for locale '{locale}'")

        html_content = self._render_template(
            template_content=template_content,
            variables=variables,
            i18n_service=i18n_service,
            template_name=template_name,
            locale=locale
        )
        
        # Create multipart message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = recipient
        
        # Add HTML version
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        self._send_message(
            msg=msg,
            recipient=recipient,
            i18n_service=i18n_service,
            locale=locale
            )
        return None

    def _send_message(
            self, msg, recipient: str,
            i18n_service: I18nService,
            locale: str = "en"
            ) -> None:
        """Send prepared email message"""
        try:
            # Create SMTP connection
            server = smtplib.SMTP(host=self.host, port=self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, [recipient], msg.as_string())
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            logger.error(f"Parameters: host={self.host}, port={self.port}, user={self.user}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=i18n_service.t("api.email.email_sending_failed", locale, error=str(e))
            )

    def send_email_plain_text(
            self, content, subject, recipient: str,
            i18n_service: I18nService,
            locale: str = "en"
            ):
        """Send plain text email (backward compatibility)"""
        try:
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = recipient
            
            self._send_message(
                msg=msg,
                recipient=recipient,
                i18n_service=i18n_service,
                locale=locale
            )
            
        except Exception as e:
            logger.error(f"Failed to create or send plain text email: {e}")
            raise

    def send_email_verification_mail(
            self,
            username: str,
            recipient: str,
            verification_code: str,
            i18n_service: I18nService,
            locale: str = "en"
            ):

        # Generate new verification code
        self.send_email_html(
            template_name="email_verification",
            variables={
                "username": username,
                "verification_code": verification_code
            },
            subject=i18n_service.t(
                key="email.shared_content.verification_code_subject", 
                locale=locale,
                verification_code=verification_code
                ),
            recipient=recipient,
            locale=locale,
            i18n_service=i18n_service
        )