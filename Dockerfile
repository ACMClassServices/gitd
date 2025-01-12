FROM alpine:3.21.2

RUN apk add --no-cache openrc nginx git git-daemon cgit python3 py3-pip bash fcgiwrap spawn-fcgi sqlite
RUN sed -i '/getty/d' /etc/inittab
RUN ln -s spawn-fcgi /etc/init.d/spawn-fcgi.wrap
RUN rc-update add nginx default && rc-update add spawn-fcgi.wrap default

COPY src/requirements.txt /opt/gitd/requirements.txt 
RUN pip3 install --break-system-packages -r /opt/gitd/requirements.txt

RUN mkdir -p /srv/gitd/repos /srv/gitd/log/git /srv/gitd/log/api /srv/gitd/serve

COPY etc /etc
RUN rc-update add gunicorn default

COPY src /opt/gitd

WORKDIR /opt/gitd
RUN alembic upgrade head && chown -R nginx:www-data /srv/gitd

VOLUME /srv/gitd /sys/fs/cgroup

CMD ["/sbin/init"]
