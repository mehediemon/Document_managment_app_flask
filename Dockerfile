# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

EXPOSE 5003

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Copy the setup_db.sh script into the container
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser 

# Create the uploads directory with proper permissions and set the SGID bit
RUN mkdir -p /app/app/uploads \
    && chown -R appuser:appuser /app\
    && chown -R appuser:appuser /app/app/uploads\
    && chmod -R 2775 /app/app/uploads

USER appuser


# Use the setup script as the entry point
ENTRYPOINT ["/app/entrypoint.sh"]
