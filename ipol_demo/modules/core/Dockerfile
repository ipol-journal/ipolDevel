FROM python:3.9

WORKDIR /app

RUN pip install pip --upgrade

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install .
