# Lunia WhatsApp Agent

🤖 AI-powered WhatsApp agent for Lunia Soluciones built with LangGraph, LlamaIndex, and OpenAI.

## Features

- **WhatsApp Integration**: Seamless messaging via Evolution API
- **AI-Powered Responses**: LlamaIndex knowledge base with OpenAI
- **Audio Support**: Automatic transcription using Whisper
- **Session Management**: Conversation history and context
- **Rate Limiting**: Built-in protection against spam
- **RESTful API**: FastAPI backend with full documentation
- **Scalable Architecture**: Modular, production-ready design

## Architecture

```
src/
├── api/           # FastAPI application
├── agents/        # LangGraph agent implementation
├── core/          # Configuration and logging
├── models/        # Data models and schemas
├── services/      # Business logic services
└── utils/         # Helper utilities

tests/             # Comprehensive test suite
scripts/           # Development and deployment scripts
data/              # Knowledge base content
storage/           # Vector store and cache
config/            # Configuration files
```

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry
- OpenAI API key
- Evolution API access

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Lunia-Whatsapp-Agent
   ```

2. **Run setup script**
   ```bash
   python scripts/setup.py
   ```

3. **Configure environment**
   ```bash
   # Edit .env file with your credentials
   cp .env.example .env
   # Update with your actual API keys and configuration
   ```

4. **Install dependencies**
   ```bash
   poetry install
   ```

5. **Start the application**
   ```bash
   poetry run python scripts/run_server.py
   ```

### Configuration

Update `.env` file with your configuration:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
EVOLUTION_API_URL=https://your-evolution-api-domain.com
EVOLUTION_API_KEY=your_evolution_api_key_here
EVOLUTION_INSTANCE_NAME=your_instance_name

# Application Settings
DEBUG=false
APP_PORT=8000
APP_HOST=0.0.0.0
```

## Usage

### API Endpoints

- **Health Check**: `GET /health`
- **WhatsApp Webhook**: `POST /webhook/whatsapp`
- **Send Message**: `POST /api/send-message`
- **Query Knowledge Base**: `POST /api/knowledge-base/query`
- **Session Management**: `GET/DELETE /api/sessions/{user_id}`

### API Documentation

Access interactive API docs at: `http://localhost:8000/docs`

### Testing

```bash
# Run unit tests
poetry run pytest tests/unit/

# Run integration tests
poetry run pytest tests/integration/

# Run all tests
poetry run pytest

# Test simulation
poetry run python scripts/test_simulation.py
```

## Development

### Project Structure

- **Modular Design**: Clean separation of concerns
- **Type Safety**: Full type annotations with mypy
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging with rotation
- **Testing**: Unit, integration, and E2E tests

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/
```

### Adding New Features

1. Create models in `src/models/`
2. Implement services in `src/services/`
3. Add API endpoints in `src/api/`
4. Write tests in `tests/`
5. Update documentation

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry install --no-dev

EXPOSE 8000
CMD ["poetry", "run", "python", "-m", "src.api.main"]
```

### Production Considerations

- Use PostgreSQL for session storage
- Implement Redis for caching
- Set up proper monitoring
- Configure rate limiting
- Use HTTPS/SSL
- Set up load balancing

## Security

- API key validation
- Rate limiting per user
- Input sanitization
- CORS configuration
- Session timeout
- Error message sanitization

## Integraciones Adicionales

Se han agregado servicios para correo electrónico (Gmail SMTP), Google Calendar y base de datos Supabase. A continuación se detallan configuraciones y ejemplos de uso:

### Variables de entorno

```env
# SMTP (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_password_o_app_password

# Google Calendar
GOOGLE_SERVICE_ACCOUNT_FILE=path/al/archivo/service-account.json

# Supabase
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_KEY=tu_supabase_anon_key_o_service_role_key
```

### Uso de EmailService

```python
from src.services.email_service import EmailService

email_svc = EmailService()
sent = email_svc.send_email(
    to="cliente@ejemplo.com",
    subject="Asunto de prueba",
    body="Hola, este es un correo de prueba desde Lunia-Whatsapp-Agent."
)
if sent:
    print("Correo enviado correctamente!")
```

### Uso de CalendarService

```python
from src.services.calendar_service import CalendarService

cal_svc = CalendarService()
event = {
    'summary': 'Reunión con cliente',
    'start': {'dateTime': '2025-06-10T10:00:00-05:00'},
    'end':   {'dateTime': '2025-06-10T11:00:00-05:00'},
    'attendees': [{'email': 'cliente@ejemplo.com'}]
}
resultado = cal_svc.create_event('primary', event)
print(f"Evento creado en Google Calendar: {resultado.get('htmlLink')}")
```

### Uso de SupabaseService

```python
from src.services.supabase_service import SupabaseService

supabase_svc = SupabaseService()
# Insertar un registro en tabla `clientes`
registro = {'nombre': 'Juan Pérez', 'email': 'juan@ejemplo.com'}
resp = supabase_svc.insert('clientes', registro)
print(f"Insert successful: {resp.data}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is proprietary to Lunia Soluciones.

## Support

For support, contact: support@luniasoluciones.com

---

Built with ❤️ by Lunia Soluciones