# Oráculo de Concursos - Discord Bot

## Overview

The Oráculo de Concursos is a specialized Discord bot designed to help users prepare for Brazilian public service examinations (concursos públicos). The bot leverages Google Gemini 2.5 AI to provide accurate, contextualized responses about Brazilian administrative law, constitutional law, and public service regulations while implementing robust anti-hallucination strategies.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Python architecture with clear separation of concerns:

### Core Components
- **Discord Bot Interface** (`bot/discord_bot.py`): Main entry point handling Discord interactions
- **Gemini AI Client** (`bot/gemini_client.py`): Integration with Google Gemini 2.5 API
- **Database Layer** (`database/`): SQLite-based data persistence
- **Anti-Hallucination System** (`utils/anti_alucinacao.py`): Confidence validation and response verification
- **Configuration Management** (`utils/config.py`): Environment-based configuration system
- **Logging System** (`utils/logger.py`): Centralized logging with rotation and custom formatting

### Architecture Decisions
1. **SQLite Database**: Chosen for simplicity and self-containment, suitable for single-instance deployment
2. **Discord.py**: Official Discord library for Python providing comprehensive API coverage
3. **Google Gemini 2.5**: Selected for advanced AI capabilities with focus on accuracy
4. **Async/Await Pattern**: Used throughout for efficient handling of concurrent Discord interactions

## Key Components

### Discord Bot (`OraculoBot`)
- Responds only when mentioned (@bot) to avoid spam
- Maintains conversation context for each user
- Implements streaming responses for better user experience
- Tracks usage statistics and performance metrics

### Gemini Client (`GeminiClient`)
- Specialized system prompt focused on Brazilian public service law
- Temperature set to 0.1 for more precise, factual responses
- Implements timeout and error handling for API calls
- Custom prompt engineering for legal accuracy

### Anti-Hallucination System (`ValidadorConfianca`)
- Pattern matching for high-confidence legal references (laws, decrees, articles)
- Detection of uncertainty indicators in responses
- Confidence scoring system with configurable thresholds
- Source verification for legal citations

### Database Models
- **Usuario**: User profile and interaction history
- **Interacao**: Individual bot interactions with metadata
- **EstatisticaUso**: Usage analytics and performance tracking

## Data Flow

1. **User Interaction**: User mentions bot in Discord channel
2. **Context Loading**: Bot retrieves conversation history from SQLite
3. **Query Processing**: Message sent to Gemini with specialized prompt
4. **Response Validation**: Anti-hallucination system validates response confidence
5. **Response Delivery**: Streaming response sent to Discord with typing indicators
6. **Data Persistence**: Interaction logged to database for context and analytics

## External Dependencies

### Required APIs
- **Discord API**: Bot user management and message handling
- **Google Gemini API**: AI-powered response generation

### Key Python Libraries
- `discord.py`: Discord bot framework
- `google.genai`: Google Gemini API client
- `aiosqlite`: Async SQLite database operations
- `asyncio`: Asynchronous programming support

### Environment Variables
- `DISCORD_TOKEN`: Discord bot authentication token
- `GEMINI_API_KEY`: Google Gemini API key
- `DATABASE_PATH`: SQLite database file location
- Various configuration options for performance tuning

## Deployment Strategy

### Current Setup
- Single-instance Python application
- SQLite database for data persistence
- Environment variable configuration
- File-based logging with rotation

### Scalability Considerations
- Database can be upgraded to PostgreSQL for multi-instance deployment
- Stateless design allows for horizontal scaling
- Configuration system supports different deployment environments
- Logging system prepared for centralized log aggregation

### Security Measures
- Token-based authentication for external APIs
- Input validation and sanitization
- Confidence-based response filtering
- Rate limiting considerations in bot design

The architecture prioritizes reliability, accuracy, and user experience while maintaining simplicity for deployment and maintenance. The anti-hallucination system is a key differentiator, ensuring high-quality responses for legal and regulatory questions.