"""
Sistema de notificaciones para agentes de IA.
Desacopla la comunicación de eventos de la lógica principal.
"""
import asyncio
import json
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class NotificationLevel(Enum):
    """Niveles de severidad para notificaciones"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Notification:
    """Estructura de una notificación"""
    level: NotificationLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class NotificationChannel(ABC):
    """Interfaz base para canales de notificación"""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Enviar notificación por este canal"""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Verificar si el canal está habilitado"""
        pass

class ConsoleNotifier(NotificationChannel):
    """Notificador a consola con formato estructurado"""
    
    def __init__(self, colored: bool = True):
        self.colored = colored
        self.colors = {
            NotificationLevel.DEBUG: "\033[36m",    # Cyan
            NotificationLevel.INFO: "\033[32m",     # Green
            NotificationLevel.WARNING: "\033[33m",  # Yellow
            NotificationLevel.ERROR: "\033[31m",    # Red
            NotificationLevel.CRITICAL: "\033[35m", # Magenta
        }
        self.reset = "\033[0m" if colored else ""
    
    async def send(self, notification: Notification) -> bool:
        """Imprimir notificación en consola"""
        try:
            color = self.colors.get(notification.level, "") if self.colored else ""
            timestamp = notification.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{color}[{timestamp}] {notification.level.value.upper()} "
                  f"[{notification.source}] {notification.title}{self.reset}")
            print(f"{color}  {notification.message}{self.reset}")
            
            if notification.metadata:
                print(f"{color}  Metadata: {json.dumps(notification.metadata, indent=2)}{self.reset}")
            
            print()  # Línea en blanco
            return True
            
        except Exception as e:
            print(f"Error sending console notification: {e}")
            return False
    
    def is_enabled(self) -> bool:
        return True

class FileNotifier(NotificationChannel):
    """Notificador a archivo con rotación"""
    
    def __init__(self, file_path: str, max_size_mb: int = 10, backup_count: int = 5):
        self.file_path = file_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
    
    async def send(self, notification: Notification) -> bool:
        """Escribir notificación a archivo"""
        try:
            # Verificar rotación
            await self._rotate_if_needed()
            
            # Escribir notificación
            log_entry = {
                "timestamp": notification.timestamp.isoformat(),
                "level": notification.level.value,
                "source": notification.source,
                "title": notification.title,
                "message": notification.message,
                "metadata": notification.metadata
            }
            
            async with asyncio.aiofiles.open(self.file_path, 'a') as f:
                await f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Error sending file notification: {e}")
            return False
    
    async def _rotate_if_needed(self):
        """Rotar archivo si excede tamaño máximo"""
        try:
            import os
            if os.path.exists(self.file_path):
                if os.path.getsize(self.file_path) >= self.max_size_bytes:
                    # Rotar archivos existentes
                    for i in range(self.backup_count - 1, 0, -1):
                        old_file = f"{self.file_path}.{i}"
                        new_file = f"{self.file_path}.{i + 1}"
                        if os.path.exists(old_file):
                            os.rename(old_file, new_file)
                    
                    # Mover archivo actual
                    os.rename(self.file_path, f"{self.file_path}.1")
                    
        except Exception as e:
            print(f"Error rotating log file: {e}")
    
    def is_enabled(self) -> bool:
        return True

class WebhookNotifier(NotificationChannel):
    """Notificador vía webhook HTTP"""
    
    def __init__(self, webhook_url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.headers = headers or {"Content-Type": "application/json"}
    
    async def send(self, notification: Notification) -> bool:
        """Enviar notificación vía HTTP POST"""
        try:
            import aiohttp
            
            payload = {
                "timestamp": notification.timestamp.isoformat(),
                "level": notification.level.value,
                "source": notification.source,
                "title": notification.title,
                "message": notification.message,
                "metadata": notification.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status < 400
                    
        except Exception as e:
            print(f"Error sending webhook notification: {e}")
            return False
    
    def is_enabled(self) -> bool:
        return bool(self.webhook_url)

class EmailNotifier(NotificationChannel):
    """Notificador vía email SMTP"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def send(self, notification: Notification) -> bool:
        """Enviar notificación por email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{notification.level.value.upper()}] {notification.title}"
            
            body = f"""
Notificación de {notification.source}

Nivel: {notification.level.value}
Fecha: {notification.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

Mensaje:
{notification.message}

Metadatos:
{json.dumps(notification.metadata, indent=2, ensure_ascii=False)}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Enviar en thread separado para no bloquear
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_sync, msg)
            
            return True
            
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False
    
    def _send_sync(self, msg):
        """Envío síncrono de email"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
    
    def is_enabled(self) -> bool:
        return all([self.smtp_server, self.username, self.password, self.to_emails])

class NotificationManager:
    """Gestor central de notificaciones con múltiples canales"""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.filters: List[Callable[[Notification], bool]] = []
        self.min_level = NotificationLevel.INFO
    
    def add_channel(self, channel: NotificationChannel):
        """Agregar canal de notificación"""
        self.channels.append(channel)
    
    def remove_channel(self, channel: NotificationChannel):
        """Remover canal de notificación"""
        if channel in self.channels:
            self.channels.remove(channel)
    
    def set_min_level(self, level: NotificationLevel):
        """Establecer nivel mínimo de notificación"""
        self.min_level = level
    
    def add_filter(self, filter_func: Callable[[Notification], bool]):
        """Agregar filtro de notificaciones"""
        self.filters.append(filter_func)
    
    async def notify(self, level: NotificationLevel, title: str, message: str, 
                    source: str, metadata: Optional[Dict[str, Any]] = None):
        """Enviar notificación a todos los canales habilitados"""
        
        # Verificar nivel mínimo
        if self._should_skip_level(level):
            return
        
        notification = Notification(
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Aplicar filtros
        if not all(filter_func(notification) for filter_func in self.filters):
            return
        
        # Enviar a todos los canales
        tasks = []
        for channel in self.channels:
            if channel.is_enabled():
                tasks.append(channel.send(notification))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _should_skip_level(self, level: NotificationLevel) -> bool:
        """Verificar si se debe omitir por nivel"""
        levels = [NotificationLevel.DEBUG, NotificationLevel.INFO, 
                 NotificationLevel.WARNING, NotificationLevel.ERROR, 
                 NotificationLevel.CRITICAL]
        
        current_idx = levels.index(level)
        min_idx = levels.index(self.min_level)
        
        return current_idx < min_idx

# Instancia global para fácil acceso
notification_manager = NotificationManager()

# Funciones de conveniencia
async def notify_debug(title: str, message: str, source: str, metadata: Optional[Dict[str, Any]] = None):
    await notification_manager.notify(NotificationLevel.DEBUG, title, message, source, metadata)

async def notify_info(title: str, message: str, source: str, metadata: Optional[Dict[str, Any]] = None):
    await notification_manager.notify(NotificationLevel.INFO, title, message, source, metadata)

async def notify_warning(title: str, message: str, source: str, metadata: Optional[Dict[str, Any]] = None):
    await notification_manager.notify(NotificationLevel.WARNING, title, message, source, metadata)

async def notify_error(title: str, message: str, source: str, metadata: Optional[Dict[str, Any]] = None):
    await notification_manager.notify(NotificationLevel.ERROR, title, message, source, metadata)

async def notify_critical(title: str, message: str, source: str, metadata: Optional[Dict[str, Any]] = None):
    await notification_manager.notify(NotificationLevel.CRITICAL, title, message, source, metadata)
