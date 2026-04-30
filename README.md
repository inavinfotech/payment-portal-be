# Payment Portal Backend

This is the backend service for the Payment Portal application, built with **FastAPI**. It manages authentication, payments (Razorpay), and data persistence using **SQLAlchemy** and **SQLite**. Database migrations are handled by **Alembic**.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (via SQLAlchemy)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose, passlib)
- **Payments**: Razorpay

## Prerequisites

- Python 3.8+
- pip

## Setup & Installation

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Create a `.env` file in the `backend/` directory with the following variables:

    ```env
    RAZORPAY_KEY_ID=your_razorpay_key_id
    RAZORPAY_KEY_SECRET=your_razorpay_key_secret
    DATABASE_URL=sqlite:///./db/payment.db
    SECRET_KEY=your_secret_key
    ADMIN_SECRET_KEY=your_admin_secret_key
    ```

5.  **Initialize the Database:**
    Run migrations to create the database tables:
    ```bash
    alembic upgrade head
    ```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
API Documentation (Swagger UI) is available at `http://localhost:8000/docs`.

## Database Migrations

This project uses **Alembic** for schema migrations.

- **Create a new migration** (after modifying models):

  ```bash
  alembic revision --autogenerate -m "Description of changes"
  ```

- **Apply migrations**:
  ```bash
  alembic upgrade head
  ```

## Project Structure

- `app/`: Main application code.
  - `models.py`: Database models.
  - `schemas.py`: Pydantic schemas.
  - `routes/`: API route handlers.
  - `database.py`: Database connection setup.
- `alembic/`: Migration scripts.
- `db/`: SQLIte database files.
