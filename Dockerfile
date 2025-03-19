# Use Python base image
FROM python:3.10

# Set environment variables for efficiency
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_DIR=/app \
    CONFIG_DIR=/config/data \
    EXPERIMENTS_DIR=/experiments

# Set the working directory inside the container
WORKDIR ${APP_DIR}

# Ensure required directories exist
RUN mkdir -p ${CONFIG_DIR} ${EXPERIMENTS_DIR}

# Copy the requirements file
COPY requirements.txt ${APP_DIR}/

# Install dependencies (Ensure gunicorn is installed)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy the entire Django project into the container
COPY . ${APP_DIR}/

# Expose the port
EXPOSE 8000

# Start the Django application using Python command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]