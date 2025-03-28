# Use a lightweight Python 3.10 base image
FROM python:3.10-slim

# Create a working directory in the container
WORKDIR /app

# Copy only requirements first for caching (optional, but good for speed)
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y build-essential
RUN pip install pytest

# Then install your Python dependencies
RUN pip install mathutils
# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your project into the container
COPY . /app/

# Install your package in editable mode
RUN pip install --no-cache-dir -e .

# By default, run pytest
CMD ["sh"]
#CMD ["pytest", "--maxfail=1", "--disable-warnings", "-v"]
