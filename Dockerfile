FROM python:3.10

ADD . .

RUN pip install poetry

RUN poetry lock --no-update

RUN poetry install

CMD ["poetry", "run", "python", "./main.py"]