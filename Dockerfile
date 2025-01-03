# Use a Python base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy application files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure temporary directories are created
RUN mkdir -p /content/plots

# Expose the Streamlit default port (8501)
EXPOSE 8501

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "doxplor.py", "--server.port=8501", "--server.address=0.0.0.0"]
