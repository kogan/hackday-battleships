FROM python:3.8-slim
RUN pip install fastapi==0.54.1 uvicorn==0.11.5 aiohttp==3.6.2
WORKDIR /code
COPY ./main.py /code
CMD uvicorn main:app --workers 2 --port $PORT --host 0.0.0.0
