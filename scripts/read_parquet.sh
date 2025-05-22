#!/bin/sh

runner() {

mkdir -p ./shared_data/
(
cat <<EOF
#!/bin/python3

pip install pandas pyarrow

import pandas as pd

df = pd.DataFrame({
"name": ["Alice", "Bob", "Charlie"],
"age": [25, 30, 35]
})

df.to_parquet("./dummy.parquet", engine="pyarrow")

EOF
) > ./shared_data/rp.py


docker compose up -d swre

DYNCONT=$(docker compose ps | grep swre | awk '{print $1}')

docker exec "$DYNCONT" /bin/sh -c "/entrypoint.sh /app/shared/rp.py && cp ./dummy.parquet /app/shared/dummy.parquet & tail -f /dev/null"

docker compose up -d postgres
docker compose up -d minio

#docker cp swre:/dummy.parquet minio:/app/dummy.parquet

MINIOCONT=$(docker compose ps -a | grep minio | awk '{print $1}') && \


printf "\n|> miniocont is: %s" "$MINIOCONT"

docker run --rm \
--network container:"$MINIOCONT" \
-v shared_data:/data \
minio/mc -sh -c '
mc alias set localminio "http://localhost:9000" swre_user swre_passd && \
mc mb localminio/swre_bucket && \
mc cp /data/shared/dummy.parquet localminio/swre_bucket/
'


docker exec "$DYNCONT" /bin/sh -c 'mkdir -p /extract && tar -czf /extract/results.tar.gz /tests/*'
# docker run -it --name swre -d --entrypoint="/bin/sh" localhost:5000/swre:latest -c 'mkdir -p /extract; tar -czf /extract/results.tar.gz /tests/*'
mkdir -pv ./artifacts/
docker cp "$DYNCONT":/extract/results.tar.gz ./artifacts/

docker stop "$DYNCONT" && docker rm "$DYNCONT"
docker compose ps
echo done!!
}


if [ "$GITHUB_ACTIONS" = "true" ]; then
    runner
else

    runner
fi
