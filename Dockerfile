# --- Stage 1: Build the React frontend ---
FROM node:18-alpine AS frontend-builder

# Set the working directory
WORKDIR /app/frontend

# Copy package.json and package-lock.json (if available) to leverage Docker cache
COPY package.json ./
# If you have a package-lock.json, copy it too
# COPY package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY Src/ ./src/
COPY Public/ ./public/

# Build the static files for production
RUN npm run build


# --- Stage 2: Build the Python backend ---
# Use the same Python version as in your CI pipeline
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY . .

# Copy the built frontend from the first stage
COPY --from=frontend-builder /app/frontend/build ./build

# Run collectstatic to gather all static files (Django admin + React)
RUN python manage.py collectstatic --noinput

# Expose the port Gunicorn will run on
EXPOSE 8000

# Run the application using Gunicorn
CMD ["gunicorn", "event_management.wsgi:application", "--bind", "0.0.0.0:8000"]