# Use Python base image
FROM python:3.10

# Set environment variables for efficiency
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRUENASdata_DIR=/TrueNASdata \
    PERSISTENT_DIR=/PersistentData \
    EXPERIMENTS_DIR=/experiments

# Set the working directory inside the container
WORKDIR /

# Ensure system packages are updated and install SQLite and Supervisor
RUN apt update && apt install -y sqlite3 supervisor

# Install Nginx
RUN apt install -y nginx

# Copy Nginx config and certs
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/certs/ /etc/nginx/certs/

# Expose HTTPS port
EXPOSE 443

# Ensure required directories exist
RUN mkdir -p ${TRUENASdata_DIR} ${PERSISTENT_DIR} ${EXPERIMENTS_DIR}

# Copy the requirements file
COPY requirements.txt /

# Install dependencies (Ensure gunicorn are installed)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 

# Copy the entire Django project into the container
COPY . .

# Copy the Supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start Supervisor to manage both processes
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]