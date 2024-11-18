FROM python:3.12.7

WORKDIR /bot

RUN mkdir -p /bot/db
COPY *.py /bot/
COPY requirements.txt /bot/
VOLUME /bot/db

RUN python -m pip install -r requirements.txt

CMD ["python", "bot.py"]