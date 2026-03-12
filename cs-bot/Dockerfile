# Use a lightweight Python base image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (for caching)
COPY requirements.txt .

# Install dependencies without cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot code
COPY . .

# Run the bot
CMD ["python", "bot.py"]
