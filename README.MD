# Fintech Platform - Core API Service

This is the  core implementation of our secure fintech platform. It provides user identity and profile management using Auth0 for authentication.

## Prerequisites

- Docker
- Docker Compose
- An Auth0 Account and Tenant

## Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <https://github.com/Sharon-Njunge/E-commerce-User-Service.git>
    cd E-commerce-User-Service
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file and update the values with your specific details.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file:
    ```ini
    # Database
    DB_URL=postgresql+asyncpg://postgres:postgres@db:5432/fintech_db

    AUTH0_DOMAIN=your-tenant.us.auth0.com
    AUTH0_CLIENT_ID=your_client_id_here
    AUTH0_CLIENT_SECRET=your_client_secret_here
    AUTH0_AUDIENCE=your_api_identifier_here 
    AUTH0_ISSUER=https://your-tenant.us.auth0.com/
    AUTH0_ALGORITHMS=RS256

    # App
    ENVIRONMENT=development
    ```

3.  **Start the Services:**
    This command will build the API image and start both the API and PostgreSQL database.
    ```bash
    docker-compose up --build
    ```
    The API will be available at `http://localhost:8000`.

4.  **Run Database Migrations (in a new terminal):**
    Apply the database schema to your running PostgreSQL container.
    ```bash
    docker-compose exec api alembic upgrade head
    ```

5.  **(Optional) Seed the Database:**
    Populate the database with sample test users.
    ```bash
    docker-compose exec api python -m scripts.seed_db
    ```

## Running Tests

To execute the test suite with coverage, run:
```bash
docker-compose exec api pytest --cov=src --cov-report=term-missing