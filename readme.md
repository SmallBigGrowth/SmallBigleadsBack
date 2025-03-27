# Project Setup Guide

This repository contains a Django project setup with a virtual environment, PostgreSQL integration, Celery for background tasks, and a branching strategy for development. Follow the steps below to set up and run the project locally.

---

## Prerequisites

- Python 3.x
- PostgreSQL installed and running
- Git for version control
- Virtualenv (`pip install virtualenv`)
- Celery dependencies (e.g., Redis or RabbitMQ as a message broker)

---

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/SmallBigGrowth/SmallBigleadsBack.git
cd SmallBigleadsBack
```

### Step 2: Set Up a Virtual Environment

Create a virtual environment:

```bash
virtualenv myenv
```

Activate it (choose based on your OS):

**Unix/Linux/macOS:**

```bash
. myenv/bin/activate
```

**Alternative path:**

```bash
. myenv/local/bin/activate
```

---

### Step 3: Install Dependencies

Install required packages from `requirements.txt`:

```bash
pip3 install -r requirements.txt
```

Example dependency:

```
Django==5.1.3
```

Verify Django version:

```bash
python -m django --version
```

---

### Step 4: Configure PostgreSQL

Update `settings/base.py` to use PostgreSQL:

```python
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
    }
}
```

Create a `.env` file in the project root:

```
# .env (no trailing spaces)
DATABASE_NAME=database name
DATABASE_USER=database user
DATABASE_PASSWORD=databsse password
DATABASE_HOST=database host
DATABASE_PORT=database port
DEBUG=False
GOOGLE_CLIENT_ID=google client id
BETTERSTACK_LOGGER_KEY=betterstack logger key
GOOGLE_SEC_ID=GOCSPX-google secret
EMAIL_BACKEND=email backend
EMAIL_HOST=email host
EMAIL_PORT=email port
EMAIL_USE_TLS=email tls
EMAIL_HOST_USER=email host user
EMAIL_HOST_PASSWORD=email host password

```

Install `python-decouple`:

```bash
pip install python-decouple
```

---

### Step 5: Apply Migrations

Generate migration files:

```bash
python3 manage.py makemigrations
```

Apply migrations:

```bash
python3 manage.py migrate
```

Create a superuser:

```bash
python3 manage.py createsuperuser
```

---

### Step 6: Run the Application

Start the Django server, Celery worker, and Celery beat:

```bash
python manage.py runserver 
```

Check for running processes (e.g., on port 8000):

```bash
lsof -i :8000
```


---

## Branching Strategy

- **Development Branch**: Base branch for ongoing work.
- **Feature Branches**: Create from development for new features.

```bash
git checkout development
git branch feature/your-feature-name
git checkout feature/your-feature-name
```

Merge feature into development:

```bash
git checkout development
git merge feature/your-feature-name
```

Merge development into production for deployment:

```bash
git checkout Production
git merge development
```

---

## Configuration Notes

- Replace `.env` placeholders with your actual values.
- Use an App Password for `EMAIL_HOST_PASSWORD` if using Gmail with 2FA.
- Ensure PostgreSQL, Redis (or another broker), and other services are running.

---

## Troubleshooting

- If the server doesn’t start, check port availability or kill conflicting processes.