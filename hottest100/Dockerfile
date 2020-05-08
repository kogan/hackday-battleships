FROM python:3.8-slim
RUN pip install requests flask waitress
WORKDIR /code
COPY ./engine.py ./app.py ./config.py /code/
CMD waitress-serve --listen=*:$PORT --threads=10 --call "app:create_app"
