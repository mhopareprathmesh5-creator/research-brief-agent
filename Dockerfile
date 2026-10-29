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

# Render assigns a port at run time through the PORT variable, so the
# port cannot be hardcoded. 7860 is the local default when PORT is unset.
EXPOSE 7860

ENV PORT=7860 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# No API key anywhere in this file or in the image (Task 4).
# It is supplied at run time with -e GOOGLE_API_KEY=... locally, or from
# the platform's environment settings when deployed.
#
# Shell form is required so that ${PORT} is expanded at container start.
# The exec form would pass the literal string "${PORT}" to Streamlit.
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-7860} --server.address=0.0.0.0"]