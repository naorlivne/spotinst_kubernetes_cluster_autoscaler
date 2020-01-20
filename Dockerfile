# it's offical so i'm using it + alpine so damn small
FROM python:3.8.1-alpine3.10

# exposing the port
EXPOSE 80

# set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# install requirements
COPY requirements.txt /www/requirements.txt
RUN pip install -r /www/requirements.txt

# copy the codebase
COPY . /www
RUN chmod +x /www/autoscaler_runner.py

# and running it
CMD ["python" ,"autoscaler_runner.py"]
