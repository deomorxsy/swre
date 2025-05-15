FROM alpine:3.20 as builder
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt



RUN <<EOF

apk upgrade && apk update && \
    apk add musl-dev python3 py3-pip \
        python3-dev py3-numpy graphviz \
        gcc g++ make cmake linux-headers

(
cat <<EOL
http://dl-cdn.alpinelinux.org/alpine/edge/main
http://dl-cdn.alpinelinux.org/alpine/edge/community
http://dl-cdn.alpinelinux.org/alpine/edge/testing
EOL
) | tee /etc/apk/repositories

# for the build with edge
apk add apache-arrow apache-arrow-dev krb5-dev

# krb5-dev is for the krb5 package,
# needed by gssapi and leveraged by sparkmagic with livy

USER=spark

addgroup -g 1000 -S "${USER}" && \
adduser -s /bin/sh -u 1000 -G "${USER}" -h "/home/${USER}" -D "${USER}" && \
su "${USER}"

mkdir -p "/home/spark/app/dags/" && \
cd "/home/spark/app" || return

# copy the repo to inside the container

pip3 install --user --upgrade pip virtualenv --break-system-packages && \
export PATH=$HOME/.local/bin/:$PATH && \
virtualenv venv && source ./venv/bin/activate && \
python3 -m ensurepip --default-pip

# from the host: podman cp ./requirements.txt 1176c3955ac2:/home/spark/app/requirements.txt
cp /app/requirements.txt /home/spark/app/requirements.txt
pip3 install --no-cache-dir -r /home/spark/app/requirements.txt


pip3 list

deactivate

# python -m ensurepip --default-pip && \
#     pip3 install --upgrade pip && \
#     pip3 install --user virtualenv && \
#     python3 -m virtualenv --python=python3.12 && \
#     pip install -r requirements.txt

EOF


# Setup the entrypoint script for simple tests
RUN <<EOF
(
cat <<EOL
#!/bin/sh

if [ -f /home/spark/app/venv/bin/activate]; then
source /home/spark/app/venv/bin/activate
exec python "$@" 2>&1 >> /tests/output.txt && echo "done!!"

else
    printf "\n|> venv activate script not found! Exiting now...\n\n"
fi

EOL
) | tee /entrypoint.sh

chmod +x /entrypoint.sh


EOF


ENTRYPOINT ["/entrypoint.sh"]
CMD ["/app/examples/parquet-reader.py"]




