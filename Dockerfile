# it's offical so i'm using it + alpine so damn small
FROM python:3.8.1-alpine3.11

# set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# install requirements
COPY requirements.txt /autoscaler/requirements.txt
RUN pip install -r /autoscaler/requirements.txt

# copy the codebase
COPY . /autoscaler
RUN chmod +x /autoscaler/autoscaler_runner.py

# configure the default location of the config folder
ENV CONFIG_DIR=/autoscaler/config

# and running it
CMD ["python" ,"/autoscaler/autoscaler_runner.py"]
