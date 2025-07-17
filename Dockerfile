FROM alpine:latest

RUN apk add --no-cache python3 py3-pip tini
ENTRYPOINT ["/sbin/tini", "--"]

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip3 install -e .

CMD /app/entrypoint.sh
