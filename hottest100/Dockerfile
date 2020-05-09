FROM python:3.8-slim
RUN pip install fastapi==0.54.1 uvicorn==0.11.5 httpx==0.12.1
WORKDIR /code
COPY ./engine.py ./app.py ./config.py /code/
CMD uvicorn app:app --workers 4 --port $PORT --host 0.0.0.0
