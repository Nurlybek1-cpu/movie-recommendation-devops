FROM python:3.9-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./actual_app/ .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
