FROM python:3.12.7

WORKDIR /bot

RUN mkdir -p /bot/db

COPY requirements.txt /bot/

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY *.py /bot/

CMD ["python", "bot.py"]