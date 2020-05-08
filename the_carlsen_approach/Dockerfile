FROM python:3.8-slim
RUN pip install requests
WORKDIR /code
COPY ./main.py /code
CMD python main.py $PORT
