### Bundle Stage
FROM python:slim-buster AS bundle

ARG USERID=1000
WORKDIR /ipfs-podcasting

RUN apt-get update; \
    apt-get install -y --no-install-recommends wget net-tools procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir requests thread6 bottle beaker \
    && mkdir /ipfs-podcasting/cfg /ipfs-podcasting/ipfs \
    && chown -R ${USERID}:${USERID} /ipfs-podcasting

COPY *.py *.png ./

USER ${USERID}
ENTRYPOINT ["python", "ipfspodcastnode.py"]
EXPOSE 4001/tcp 5001/tcp 8675/tcp
