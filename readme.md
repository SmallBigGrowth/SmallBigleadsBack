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
DATABASE_NAME=your_database_name
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432


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

Kill a process if needed (replace `<PID>` with the actual process ID):

```bash
kill <PID>
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
git checkout main
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
- Verify `.env` variables are correctly loaded in `settings/base.py`.