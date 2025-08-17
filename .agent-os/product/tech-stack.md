# Technical Stack

## Backend & Core Application
- **Application Framework:** Python 3.11+ with FastAPI
- **Background Processing:** Celery with Redis broker
- **Database System:** PostgreSQL with SQLAlchemy ORM
- **Google Maps Integration:** Google Maps Platform APIs (Directions API, Places API)

## Mobile Application
- **Mobile Framework:** Kivy or BeeWare for cross-platform Python mobile development
- **Alternative Framework:** React Native with Python backend (if pure Python mobile proves limiting)
- **Push Notifications:** Firebase Cloud Messaging (FCM) for Android
- **Location Services:** Device GPS with Google Maps geocoding

## Infrastructure & Hosting
- **Application Hosting:** Railway or Heroku for Python backend
- **Database Hosting:** PostgreSQL on Railway/Heroku or AWS RDS
- **Background Jobs:** Redis Cloud or self-hosted Redis
- **Mobile Distribution:** Google Play Store (Android)

## Development & Deployment
- **Package Management:** Poetry for Python dependency management
- **Code Repository:** GitHub
- **CI/CD:** GitHub Actions
- **Environment Management:** Docker for containerization
- **Configuration:** Environment variables with python-dotenv

## External Services
- **Maps & Traffic Data:** Google Maps Platform
- **Notifications:** Firebase for push notifications
- **Analytics:** Google Analytics or Mixpanel (optional)
- **Error Tracking:** Sentry for error monitoring

## Development Tools
- **Code Quality:** Black (formatting), Pylint (linting), mypy (type checking)
- **Testing:** pytest with coverage reporting
- **API Documentation:** FastAPI automatic OpenAPI/Swagger docs
- **Database Migrations:** Alembic (SQLAlchemy migrations)