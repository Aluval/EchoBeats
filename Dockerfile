FROM python:3.10
WORKDIR /app
COPY . /app/
# Install mediainfo
RUN apt-get update && \
    apt-get install -y mediainfo  
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
# Credits 🌟 - @Sunrises_24
