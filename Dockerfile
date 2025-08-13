# Stage 1: Build the React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files and install dependencies to leverage Docker cache
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY Src/ ./src/
COPY public/ ./public/

# Build the static files for production
RUN npm run build

# Stage 2: Build the final Python backend image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Copy Python dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code
COPY . .

# Copy the built frontend from the builder stage into the correct location
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint script as the command to run when the container starts
CMD ["/app/entrypoint.sh"]
