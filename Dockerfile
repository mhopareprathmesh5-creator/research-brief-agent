# Python 3.11 slim keeps the image small while still having wheels
# available for every dependency.
FROM python:3.11-slim

# Hugging Face Spaces runs containers as a non-root user with UID 1000.
# Creating that user here avoids permission errors on the writable paths.
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements first so that Docker caches the install layer.
# Rebuilds after a code change then skip re-downloading every package.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

# Spaces expects the app on 7860. Streamlit defaults to 8501, so it is
# set explicitly here.
EXPOSE 7860

ENV STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# No API key anywhere in this file or in the image (Task 4).
# It is supplied at run time with -e GOOGLE_API_KEY=... locally, or from
# the platform's secrets settings when deployed.
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
