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
            
        # Template system initialization
        self.templates_dir = os.getenv("EMAIL_TEMPLATES_DIR", None)
        if self.templates_dir:
            logger.info(f"Using email templates directory '{self.templates_dir}' from environment variable 'EMAIL_TEMPLATES_DIR'")
            if not os.path.exists(self.templates_dir):
                logger.warning(f"Email templates directory does not exist: {self.templates_dir}")  
        else:
            logger.info("Environment variable 'EMAIL_TEMPLATES_DIR' not set, using plain text emails only")

        # Load logo URL from environment variable
        self.logo_url = os.getenv("LOGO_URL", None)
        if self.logo_url:
            logger.info(f"Using logo URL '{self.logo_url}' from environment variable 'LOGO_URL'")
        else:
            logger.warning("Environment variable 'LOGO_URL' not set, logo will not be included in emails")

        # Color configuration initialization
        if "EMAIL_COLOR_CONFIG_DIR" in os.environ:
            self.config_dir_path = os.environ["EMAIL_COLOR_CONFIG_DIR"]
            logger.info(f"Using color config directory '{self.config_dir_path}' from environment variable 'EMAIL_COLOR_CONFIG_DIR'")
        else:
            self.config_dir_path = os.path.join(os.path.dirname(__file__), "config")
            logger.info(f"Using default color config directory '{self.config_dir_path}' since 'EMAIL_COLOR_CONFIG_DIR' not set")

        if "EMAIL_COLOR_CONFIG_FILE" in os.environ:
            self.colors_file_name = os.environ["EMAIL_COLOR_CONFIG_FILE"]
            logger.info(f"Using color config file '{self.colors_file_name}' from environment variable 'EMAIL_COLOR_CONFIG_FILE'")
        else:
            self.colors_file_name = "colors.json"
            logger.info(f"Using default color config file '{self.colors_file_name}' since 'EMAIL_COLOR_CONFIG_FILE' not set")

        self.colors_file_path = os.path.join(self.config_dir_path, self.colors_file_name)
        if not os.path.exists(self.colors_file_path):
            logger.warning(f"Color configuration file does not exist: {self.colors_file_path}")
        else:
            logger.info(f"Color configuration file found: {self.colors_file_path}")
        


    def _load_color_config(self) -> Dict[str, Any]:
        """Load color configuration from separate JSON file"""

        try:
            with open(self.colors_file_path, 'r', encoding='utf-8') as f:
                color_config = json.load(f)
            return color_config
        except FileNotFoundError:
            logger.warning(f"Color configuration file not found: {self.colors_file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse color configuration: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load color configuration: {e}")
            return {}

    def _load_template(self, template_name: str, locale: str = "en") -> Optional[str]:
        """Load an HTML template file with locale support"""
        if not self.templates_dir:
            return None
        
        # Try localized template first, then fall back to default
        template_path = os.path.join(self.templates_dir, f"{template_name}.html")
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


    def _load_css_template(self, css_filename: str = "email_styles.css") -> Optional[str]:
        """Load CSS template file"""
        if not self.templates_dir:
            return None
        
        css_path = os.path.join(self.templates_dir, css_filename)
        if not os.path.exists(css_path):
            logger.warning(f"CSS template not found: {css_path}")
            return None

        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            logger.info(f"Loaded CSS template: {css_path}")
            return css_content
        except Exception as e:
            logger.error(f"Failed to load CSS template {css_path}: {e}")
            return None


    def _render_css_template(self, css_content: str, variables: Dict[str, Any]) -> str:
        """Render CSS template with variables - DEPRECATED: Now using inline styles"""
        # This method is kept for backward compatibility but not used
        rendered_css = css_content
        
        # Replace all variables in the CSS template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_css = rendered_css.replace(placeholder, str(value))
        
        return rendered_css


    def _get_template_text_variables(self, i18n_service: I18nService, template_name: str, locale: str) -> Dict[str, str]:
        """Get all text variables for a template from i18n service"""
        try:
            # Get the translations for the locale
            translations = i18n_service._translations.get(locale, {})
            
            # Get email_templates section
            email_templates = translations.get("email_templates", {})
            
            # Get shared content
            shared_content = email_templates.get("shared_content", {})
            
            # Get template-specific content
            template_content = email_templates.get("templates", {}).get(template_name, {}).get("content", {})
            
            # Merge shared content with template-specific content (template-specific takes precedence)
            all_texts = {**shared_content, **template_content}
            
            return all_texts
            
        except Exception as e:
            logger.error(f"Failed to get template text variables from i18n for '{template_name}': {e}")
            return {}

    def _load_template_config(self, template_name: str, i18n_service: I18nService, locale: str = "en") -> Dict[str, Any]:
        """Load template configuration from i18n service and separate color config"""
        try:
            # Get the translations for the locale
            translations = i18n_service._translations.get(locale, {})
            
            # Get email_templates section
            email_templates = translations.get("email_templates", {})
            
            # Get app config
            app_config = email_templates.get("app_config", {})
            
            # Load colors from separate configuration file
            color_config = self._load_color_config()
            colors = color_config.get("colors", {})
            status_colors = color_config.get("status_colors", {})
            template_colors = color_config.get("template_colors", {}).get(template_name, {})
            
            # Create defaults with flattened color structure for template compatibility
            defaults = app_config.copy()
            
            # Add flattened colors from color configuration
            defaults.update({
                "primary_color": colors.get("primary", "#4f46e5"),
                "secondary_color": colors.get("secondary", "#6366f1"),
                "background_color": colors.get("background", "#f8fafc"),
                "container_background": colors.get("container_background", "#ffffff"),
                "text_color": colors.get("text_primary", "#1e293b"),
                "text_secondary_color": colors.get("text_secondary", "#64748b"),
                "border_color": colors.get("border", "#e2e8f0"),
                "code_text_color": colors.get("code_text", "#ffffff"),
                "button_text_color": colors.get("button_text", "#ffffff"),
                "button_hover_color": colors.get("button_hover", "#3730a3"),
                "footer_text_color": colors.get("footer_text", "#64748b"),
                "footer_border_color": colors.get("footer_border", "#e2e8f0"),
                "footer_link_color": colors.get("footer_link", "#4f46e5"),
            })
            
            # Add status colors
            for status, status_config in status_colors.items():
                if isinstance(status_config, dict):
                    defaults.update({
                        f"{status}_background": status_config.get("background", ""),
                        f"{status}_text_color": status_config.get("text", ""),
                        f"{status}_border_color": status_config.get("border", ""),
                        f"{status}_title_color": status_config.get("title", ""),
                    })
            
            # Add template-specific colors (these override defaults)
            defaults.update(template_colors)
            
            # Get template-specific config from locale (for non-color config)
            template_config = email_templates.get("templates", {}).get(template_name, {}).get("config", {})
            
            # Merge defaults with template-specific config (template config takes precedence)
            defaults.update(template_config)
            
            return {"defaults": defaults}
            
        except Exception as e:
            logger.error(f"Failed to get template config from i18n for '{template_name}': {e}")
            return {}
            

    def _process_asset_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Add logo URL to variables"""
        processed_vars = variables.copy()
        
        # Add logo URL if available
        if self.logo_url:
            processed_vars["logo_url"] = self.logo_url
        
        return processed_vars

    def _render_template(self, template_content: str, variables: Dict[str, Any], 
                        config: Dict[str, Any] = {}, i18n_service=None, 
                        template_name: str = None, locale: str = "en") -> str:
        """Render template with variables and configuration"""
        # Process asset file paths to data URIs
        processed_variables = self._process_asset_variables(variables)
        
        # Get template text variables from i18n service
        text_variables = {}
        if i18n_service and template_name:
            text_variables = self._get_template_text_variables(i18n_service, template_name, locale)
        
        # First, process nested variables in text_variables using processed_variables
        processed_text_variables = {}
        for key, value in text_variables.items():
            processed_text = str(value)
            # Replace placeholders like {username}, {app_name} in the text
            for var_key, var_value in processed_variables.items():
                placeholder = f"{{{var_key}}}"
                processed_text = processed_text.replace(placeholder, str(var_value))
            processed_text_variables[key] = processed_text
        
        # Merge all variables: config defaults + processed text variables + processed variables
        # Order matters: processed_variables should override processed_text_variables and config defaults
        all_variables = {
            **config.get("defaults", {}),
            **processed_text_variables,
            **processed_variables
        }
        
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
                       locale: str = "en",
                       fallback_content: str = None,
                       i18n_service=None) -> None:
        """Send HTML email using template system"""
        
        # Load template and config
        template_content = self._load_template(
            template_name = template_name,
            locale = locale
            )
        config = self._load_template_config(
            template_name= template_name,
            i18n_service=i18n_service,
            locale=locale
            )
        
        if template_content:
            # Render HTML template
            html_content = self._render_template(template_content, variables, config, 
                                               i18n_service, template_name, locale)
            
            # Create multipart message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = recipient
            
            # Add plain text fallback if provided
            if fallback_content:
                text_part = MIMEText(fallback_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            self._send_message(
                msg=msg,
                recipient=recipient,
                i18n_service=i18n_service,
                locale=locale
            )
            
        else:
            # Fall back to plain text if no template found
            if fallback_content:
                self.send_email_plain_text(
                    content=fallback_content,
                    subject=subject,
                    recipient=recipient,
                    i18n_service=i18n_service,
                    locale=locale
                )
            else:
                logger.error(f"No template found for '{template_name}' and no fallback provided")
                raise ValueError(f"Email template '{template_name}' not found and no fallback provided")

    def send_email_with_template(self,
                               template_name: str,
                               variables: Dict[str, Any],
                               subject: str,
                               recipient: str,
                               locale: str = "en",
                               plain_text_content: str = None,
                               i18n_service=None) -> None:
        """Send email using template system with automatic fallback to plain text"""
        
        # Try HTML template first
        template_content = self._load_template(template_name, locale)
        
        if template_content:
            config = self._load_template_config(template_name, i18n_service, locale)
            html_content = self._render_template(template_content, variables, config, 
                                               i18n_service, template_name, locale)
            
            # Create multipart message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = recipient
            
            # Add plain text version if provided
            if plain_text_content:
                text_part = MIMEText(plain_text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            self._send_message(
                msg=msg,
                recipient=recipient,
                i18n_service=i18n_service,
                locale=locale
            )
            
        else:
            # Fall back to plain text
            if plain_text_content:
                self.send_email_plain_text(
                    content=plain_text_content,
                    subject=subject,
                    recipient=recipient,
                    i18n_service=i18n_service,
                    locale=locale
                )
            else:
                logger.error(f"No template or plain text content provided for '{template_name}'")
                raise ValueError(f"No template or plain text content provided for '{template_name}'")

    def _send_message(
            self,
            msg, 
            recipient: str,
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
            self,
            content,
            subject,
            recipient,
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
        
        # Get company name from locale configuration
        config = self._load_template_config("email_verification", i18n_service, locale)
        app_name = config.get("defaults", {}).get("app_name", "YourApp")
        contact_email = config.get("defaults", {}).get("contact_email", "support@yourapp.com")
        
        # Generate new verification code
        self.send_email_with_template(
            template_name="email_verification",
            variables={
                "username": username,
                "verification_code": verification_code,
                "app_name": app_name,
                "contact_email": contact_email
            },
            subject=i18n_service.t("email.subjects.email_verification", locale),
            recipient=recipient,
            locale=locale,
            plain_text_content=i18n_service.t("email.fallback_content.email_verification", locale, 
                                            username=username, 
                                            verification_code=verification_code),
            i18n_service=i18n_service
        )
            