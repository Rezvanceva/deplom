FROM python:3.11-slim

WORKDIR /opt/

EXPOSE 8000

RUN pip install "poetry==1.3.2"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi --no-root

COPY . .

ENTRYPOINT ["bash", "entrypoint.sh"]

FROM base-image as api-image

CMD ["gunicorn", "todolist.wsgi", "-w", "4", "-b", "0.0.0.0:8000"]

FROM base-image as bot-image

CMD ["python", "manage.py", "runbot"]