# ticker-scrap server

A FastAPI-based server for real-time financial market data collection and distribution.

## Features

- Real-time market data collection for various financial instruments
- Cryptocurrency market indicators (BTC Dominance, TOTAL3)
- Fear & Greed Index tracking
- Redis-based pub/sub system for real-time data distribution
- Background tasks for continuous data updates

## Tech Stack

- Python 3.11
- FastAPI
- Redis
- Docker
- Jenkins (CI/CD)

## CI/CD

The project uses Docker and Jenkins for automated deployment:

- Automated builds on git push
- Automatic container management
- Health check verification after deployment

## Project Structure

```
ticker-scrap/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── constants/           # Application constants and configurations
│   ├── core/               # Core functionality and connections
│   ├── models/             # Data models and schemas
│   ├── services/           # Business logic and external services
│   └── workers/            # Background task workers
├── Dockerfile              # Docker configuration
├── Jenkinsfile            # CI/CD pipeline configuration
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## License

This project is proprietary software owned by takealook97.
