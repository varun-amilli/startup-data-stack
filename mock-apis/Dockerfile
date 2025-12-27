FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_stripe_api.py .

EXPOSE 5001

CMD ["python", "mock_stripe_api.py"]
