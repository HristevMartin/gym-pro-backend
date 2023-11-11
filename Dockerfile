FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Install a WSGI server, like gunicorn
RUN pip install gunicorn

# Start the application using a WSGI server
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
