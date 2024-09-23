FROM ubuntu@sha256:b4b521bfcec90b11d2869e00fe1f2380c21cbfcd799ee35df8bd7ac09e6f63ea
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install -y \
        python3 python3-pip xinetd && \
    pip3 install llvmlite
WORKDIR /
COPY flag.txt /
COPY chall.py /
COPY start.sh /
COPY run.sh /
RUN chmod +x /start.sh
RUN chmod +x /run.sh
ENTRYPOINT ["/start.sh"]