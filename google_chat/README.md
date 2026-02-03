# google_chat/README.md
# 💬 Google Chat Notification Module

## Overview

Scalable notification system using Google Chat API to replace Twilio SMS for T4Alerts error notifications. Supports Direct Messages (DM), Group Chats, and Spaces with thread organization.

## Architecture

- **Strategy Pattern**: Different notification targets (DM, Group, Space)
- **Singleton Pattern**: Client instance management
- **Factory Pattern**: Strategy creation based on configuration
- **Template Method**: Common message formatting
- **Error Boundary Decorator**: Graceful error handling

## Directory Structure

```
google_chat/
├── __init__.py                 # Public API
├── core/
│   ├── auth.py                # Service Account authentication
│   ├── config.py              # Environment configuration
│   └── logger.py              # Colored logging
├── client/
│   └── gchat_client.py        # Google Chat API wrapper
├── strategies/
│   ├── base_strategy.py       # Abstract strategy
│   ├── dm_strategy.py         # Direct Message
│   └── space_strategy.py      # Space with threads
├── notifier/
│   └── gchat_notifier.py      # Main orchestrator
├── errors/
│   └── exceptions.py          # Custom exceptions
└── README.md                  # This file
```

## Configuration

### Environment Variables

```bash
# Enable/disable
GCHAT_ENABLED=1                # 1=enabled, 0=disabled

# Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Notification mode
GCHAT_MODE=dm                  # 'dm', 'group', or 'space'

# For DM mode
GCHAT_TARGET_EMAIL=devops@your-domain.com

# For Space mode
# GCHAT_SPACE_NAME=spaces/AAAAxxxxxxxx
# GCHAT_THREAD_KEY=t4-alerts   # Optional
```

### Required Credentials

1. **Service Account Key** (`service-account-key.json`)
   - Download from Google Cloud Console
   - Never commit to git (add to `.gitignore`)
   - Set path in `GOOGLE_APPLICATION_CREDENTIALS`

2. **Target Email or Space ID**
   - For DM: User's email address
   - For Space: Space ID from Google Chat

## Usage

### Basic Usage

```python
from google_chat import enviar_gchat_errores_no_controlados

resultado = {
    'app_name': 'DriveApp',
    'app_key': 'driverapp_goto',
    'fecha_str': '2026-02-02',
    'no_controlados_nuevos': [
        'SQLSTATE error...',
        'Database timeout...'
    ]
}

success = enviar_gchat_errores_no_controlados(resultado)
```

### Generic Messages

```python
from google_chat import enviar_aviso_gchat

success = enviar_aviso_gchat("🧪 Test message from T4Alerts")
```

## Integration with main.py

Already integrated in `app/notifier.py`:

```python
from google_chat import enviar_gchat_errores_no_controlados

def notificar_app(resultado):
    # Email
    enviar_resumen_por_correo(...)
    
    # Google Chat (NEW)
    gchat_enviado = enviar_gchat_errores_no_controlados(resultado)
    if gchat_enviado:
        print(f"✓ Google Chat enviado para {app_name}")
    
    # SMS (legacy)
    # Slack
    ...
```

## Error Handling

- **Graceful degradation**: Errors don't crash main app
- **Detailed logging**: All errors logged with timestamps
- **Auto-retry**: Exponential backoff for transient errors
- **Rate limiting**: Respects Google Chat API limits (60 req/min)

## Testing

See `implementation_plan.md` for detailed testing procedures.

Quick test:
```bash
python -c "from google_chat import enviar_aviso_gchat; enviar_aviso_gchat('Test')"
```

## Design Patterns Used

1. **Strategy**: `DMStrategy`, `SpaceStrategy` implement `NotificationStrategy`
2. **Singleton**: Single `GoogleChatNotifier` instance
3. **Factory**: `_create_strategy()` creates appropriate strategy
4. **Template Method**: `format_message()` in base strategy
5. **Decorator**: `@gchat_error_boundary` for error handling

## Future Enhancements

- [ ] Group Chat support
- [ ] Rich cards with buttons
- [ ] File attachments
- [ ] Two-way bot interactions
- [ ] Metrics and analytics
