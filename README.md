# Support Analytics Backend

Python backend service for Support Analytics Dashboard, providing email processing and data analysis capabilities.

## Features

- IMAP email integration for automatic ticket creation
- FastAPI-based REST API
- SQLite database with SQLAlchemy ORM
- Email categorization and sentiment analysis
- CSV file processing
- Real-time metrics calculation

## Setup

1. Clone the repository:
```bash
git clone https://github.com/gRAYESS123/Support-py.git
cd Support-py
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file:
```env
DATABASE_URL=sqlite:///./support_analytics.db
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
Support-py/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic models
│   ├── email_service.py  # Email processing
│   ├── database.py       # Database configuration
│   └── utils.py          # Utility functions
├── alembic/              # Database migrations
├── tests/                # Test files
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License