FROM python:3.12.7

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

WORKDIR /bot

RUN mkdir -p /bot/db

COPY requirements.txt /bot/

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY *.py /bot/

CMD ["python", "bot.py"]