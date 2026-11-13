FROM python:3.13-slim

WORKDIR /app

RUN pip install google-genai python-dotenv

COPY main.py test_data_manager.py ./
COPY managers ./managers
COPY models ./models
COPY data ./data

CMD ["python", "main.py"]
