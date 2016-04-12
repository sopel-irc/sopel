FROM python:alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN adduser -S sopel

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

USER sopel

# OS X users will crash with permission errors if they use a
#     volume over /home/sopel/.sopel - nothing we can do about it.
# Workaround: Don't use OS X
# https://github.com/boot2docker/boot2docker/issues/581
# https://github.com/docker/kitematic/issues/351
VOLUME [ "/home/sopel/.sopel" ]

CMD [ "python", "./sopel.py" ]
