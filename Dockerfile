FROM python:3.12.7

WORKDIR /bot

COPY *.py /bot/
COPY mysqlite.db /bot/
COPY requirements.txt /bot/

RUN python -m pip install -r requirements.txt

CMD ["python", "bot.py"]