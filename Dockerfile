FROM python:3.6.4-alpine3.7
ADD ./requirements.txt /etc
RUN pip install -r /etc/requirements.txt
WORKDIR /app
ADD . /app
CMD gunicorn -c gunicorn.ini app:app
EXPOSE 5000
