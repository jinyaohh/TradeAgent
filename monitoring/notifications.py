"""
Notification System

Handles all notifications for the trading system including:
- Trade execution alerts
- Risk limit breaches
- System errors
- Daily performance summaries
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import os

from monitoring.logger import get_logger

logger = get_logger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"


class NotificationChannel(Enum):
    """Available notification channels"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    CONSOLE = "console"
    WEBHOOK = "webhook"


class Notification:
    """Represents a notification message"""

    def __init__(self,
                 title: str,
                 message: str,
                 level: NotificationLevel = NotificationLevel.INFO,
                 data: Optional[Dict] = None):
        self.timestamp = datetime.now()
        self.title = title
        self.message = message
        self.level = level
        self.data = data or {}

    def __str__(self):
        emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨",
            NotificationLevel.SUCCESS: "✅"
        }
        emoji = emoji_map.get(self.level, "")
        return f"{emoji} {self.title}\n{self.message}"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'message': self.message,
            'level': self.level.value,
            'data': self.data
        }


class BaseNotifier(ABC):
    """Base class for all notifiers"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """Send a notification"""
        pass

    def is_enabled(self) -> bool:
        """Check if notifier is enabled"""
        return self.enabled


class ConsoleNotifier(BaseNotifier):
    """Console/terminal notifier - prints to stdout"""

    def send(self, notification: Notification) -> bool:
        """Print notification to console"""
        if not self.enabled:
            return False

        try:
            print("\n" + "="*60)
            print(f"[{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"{notification.level.value.upper()}")
            print(f"{notification.title}")
            print("-"*60)
            print(notification.message)

            if notification.data:
                print("\nAdditional Data:")
                for key, value in notification.data.items():
                    print(f"  {key}: {value}")

            print("="*60 + "\n")
            return True
        except Exception as e:
            logger.error(f"Console notification failed: {e}")
            return False


class TelegramNotifier(BaseNotifier):
    """Telegram bot notifier"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None,
                 enabled: bool = True):
        super().__init__(enabled)

        # Get from environment if not provided
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        # Only enable if credentials are provided
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not provided - Telegram notifications disabled")
            self.enabled = False
        else:
            logger.info("Telegram notifier initialized")

    def send(self, notification: Notification) -> bool:
        """Send notification via Telegram"""
        if not self.enabled:
            return False

        try:
            import requests

            # Format message with Markdown
            emoji_map = {
                NotificationLevel.INFO: "ℹ️",
                NotificationLevel.WARNING: "⚠️",
                NotificationLevel.ERROR: "❌",
                NotificationLevel.CRITICAL: "🚨",
                NotificationLevel.SUCCESS: "✅"
            }
            emoji = emoji_map.get(notification.level, "")

            text = f"{emoji} *{notification.title}*\n\n{notification.message}"

            # Add data if present
            if notification.data:
                text += "\n\n*Details:*"
                for key, value in notification.data.items():
                    text += f"\n• {key}: {value}"

            # Add timestamp
            text += f"\n\n_{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_"

            # Send via Telegram API
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.debug(f"Telegram notification sent: {notification.title}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False

        except ImportError:
            logger.error("requests library not installed - cannot send Telegram notifications")
            self.enabled = False
            return False
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False


class EmailNotifier(BaseNotifier):
    """Email notifier (optional)"""

    def __init__(self, smtp_host: Optional[str] = None, smtp_port: int = 587,
                 smtp_user: Optional[str] = None, smtp_password: Optional[str] = None,
                 to_email: Optional[str] = None, enabled: bool = False):
        super().__init__(enabled)

        self.smtp_host = smtp_host or os.getenv('SMTP_HOST')
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.to_email = to_email or os.getenv('EMAIL_TO')

        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.to_email]):
            logger.warning("Email credentials not complete - Email notifications disabled")
            self.enabled = False

    def send(self, notification: Notification) -> bool:
        """Send notification via email"""
        if not self.enabled:
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{notification.level.value.upper()}] {notification.title}"
            msg['From'] = self.smtp_user
            msg['To'] = self.to_email

            # Create HTML body
            html_body = f"""
            <html>
              <body>
                <h2>{notification.title}</h2>
                <p><strong>Level:</strong> {notification.level.value.upper()}</p>
                <p><strong>Time:</strong> {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{notification.message.replace(chr(10), '<br>')}</p>
            """

            if notification.data:
                html_body += "<h3>Details:</h3><ul>"
                for key, value in notification.data.items():
                    html_body += f"<li><strong>{key}:</strong> {value}</li>"
                html_body += "</ul>"

            html_body += "</body></html>"

            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.debug(f"Email notification sent: {notification.title}")
            return True

        except ImportError:
            logger.error("Email libraries not available - Email notifications disabled")
            self.enabled = False
            return False
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False


class NotificationManager:
    """
    Central notification manager

    Handles routing notifications to multiple channels
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize notification manager

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        # Initialize notifiers
        self.notifiers: Dict[NotificationChannel, BaseNotifier] = {}

        # Console notifier (always enabled)
        self.notifiers[NotificationChannel.CONSOLE] = ConsoleNotifier(
            enabled=config.get('console_enabled', True)
        )

        # Telegram notifier
        self.notifiers[NotificationChannel.TELEGRAM] = TelegramNotifier(
            bot_token=config.get('telegram_bot_token'),
            chat_id=config.get('telegram_chat_id'),
            enabled=config.get('telegram_enabled', False)
        )

        # Email notifier
        self.notifiers[NotificationChannel.EMAIL] = EmailNotifier(
            smtp_host=config.get('smtp_host'),
            smtp_port=config.get('smtp_port', 587),
            smtp_user=config.get('smtp_user'),
            smtp_password=config.get('smtp_password'),
            to_email=config.get('email_to'),
            enabled=config.get('email_enabled', False)
        )

        # Notification history
        self.history: List[Notification] = []
        self.max_history = config.get('max_history', 100)

        # Count active notifiers
        active = sum(1 for n in self.notifiers.values() if n.is_enabled())
        logger.info(f"Notification Manager initialized with {active} active channel(s)")

    def notify(self, title: str, message: str,
               level: NotificationLevel = NotificationLevel.INFO,
               channels: Optional[List[NotificationChannel]] = None,
               data: Optional[Dict] = None) -> bool:
        """
        Send a notification

        Args:
            title: Notification title
            message: Notification message
            level: Severity level
            channels: Specific channels to use (None = all enabled)
            data: Additional data dictionary

        Returns:
            True if at least one notification succeeded
        """
        notification = Notification(title, message, level, data)

        # Add to history
        self.history.append(notification)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Determine which channels to use
        if channels is None:
            channels = list(self.notifiers.keys())

        # Send to each channel
        success = False
        for channel in channels:
            if channel in self.notifiers:
                if self.notifiers[channel].send(notification):
                    success = True

        # Log the notification
        log_method = {
            NotificationLevel.INFO: logger.info,
            NotificationLevel.WARNING: logger.warning,
            NotificationLevel.ERROR: logger.error,
            NotificationLevel.CRITICAL: logger.critical,
            NotificationLevel.SUCCESS: logger.info
        }.get(level, logger.info)

        log_method(f"Notification: {title} - {message}")

        return success

    # Convenience methods for different notification types

    def trade_executed(self, symbol: str, side: str, quantity: float,
                      price: float, strategy: str):
        """Notify about trade execution"""
        self.notify(
            title=f"Trade Executed: {symbol}",
            message=f"{side.upper()} {quantity:.4f} {symbol} @ ${price:,.2f}\nStrategy: {strategy}",
            level=NotificationLevel.SUCCESS,
            data={
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'strategy': strategy
            }
        )

    def position_closed(self, symbol: str, pnl: float, pnl_pct: float,
                       reason: str):
        """Notify about position closure"""
        level = NotificationLevel.SUCCESS if pnl > 0 else NotificationLevel.WARNING

        self.notify(
            title=f"Position Closed: {symbol}",
            message=f"P&L: ${pnl:,.2f} ({pnl_pct:.2%})\nReason: {reason}",
            level=level,
            data={
                'symbol': symbol,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason
            }
        )

    def risk_limit_breach(self, limit_type: str, current_value: float,
                         threshold: float):
        """Notify about risk limit breach"""
        self.notify(
            title=f"Risk Limit Breach: {limit_type}",
            message=f"Current: {current_value:.2%}\nThreshold: {threshold:.2%}",
            level=NotificationLevel.CRITICAL,
            data={
                'limit_type': limit_type,
                'current_value': current_value,
                'threshold': threshold
            }
        )

    def system_error(self, error_type: str, error_message: str):
        """Notify about system errors"""
        self.notify(
            title=f"System Error: {error_type}",
            message=error_message,
            level=NotificationLevel.ERROR,
            data={'error_type': error_type}
        )

    def daily_summary(self, total_value: float, daily_pnl: float,
                     daily_pnl_pct: float, num_trades: int,
                     open_positions: int):
        """Send daily performance summary"""
        self.notify(
            title="Daily Performance Summary",
            message=f"Portfolio Value: ${total_value:,.2f}\n"
                   f"Daily P&L: ${daily_pnl:,.2f} ({daily_pnl_pct:.2%})\n"
                   f"Trades Today: {num_trades}\n"
                   f"Open Positions: {open_positions}",
            level=NotificationLevel.INFO,
            data={
                'total_value': total_value,
                'daily_pnl': daily_pnl,
                'daily_pnl_pct': daily_pnl_pct,
                'num_trades': num_trades,
                'open_positions': open_positions
            }
        )

    def emergency_stop(self, reason: str):
        """Notify about emergency stop"""
        self.notify(
            title="🚨 EMERGENCY STOP ACTIVATED",
            message=f"Trading has been halted!\nReason: {reason}",
            level=NotificationLevel.CRITICAL,
            channels=[NotificationChannel.TELEGRAM, NotificationChannel.CONSOLE],
            data={'reason': reason}
        )

    def get_recent_notifications(self, count: int = 10) -> List[Notification]:
        """Get recent notifications"""
        return self.history[-count:]


if __name__ == "__main__":
    # Test notification system
    print("="*60)
    print("Testing Notification System")
    print("="*60)

    # Create manager (console only for testing)
    manager = NotificationManager({
        'console_enabled': True,
        'telegram_enabled': False,
        'email_enabled': False
    })

    # Test different notification types
    print("\n1. Trade Execution:")
    manager.trade_executed('BTC/USDT', 'buy', 0.1, 50000.0, 'RSI Strategy')

    print("\n2. Position Closed (Profit):")
    manager.position_closed('ETH/USDT', 150.50, 0.05, 'take_profit')

    print("\n3. Position Closed (Loss):")
    manager.position_closed('AAPL', -45.20, -0.03, 'stop_loss')

    print("\n4. Risk Limit Breach:")
    manager.risk_limit_breach('daily_loss', 0.06, 0.05)

    print("\n5. System Error:")
    manager.system_error('API Connection', 'Failed to connect to exchange')

    print("\n6. Daily Summary:")
    manager.daily_summary(10500.0, 250.0, 0.025, 5, 3)

    print("\n7. Emergency Stop:")
    manager.emergency_stop('Circuit breaker triggered - daily loss limit')

    print("\n" + "="*60)
    print("✓ Notification system test complete!")
    print(f"Total notifications in history: {len(manager.history)}")
    print("="*60)
