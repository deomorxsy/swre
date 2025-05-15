#!/bin/sh

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
) > /app/shared/rp.py


docker compose up -d swre

#docker cp ./examples/rp.py swre:/app/rp.py
docker exec --entrypoint=/bin/sh -c "/entrypoint.sh /app/shared/rp.py && cp ./dummy.parquet /app/shared/dummy.parquet" swre

docker compose up -d minio
#docker cp swre:/dummy.parquet minio:/app/dummy.parquet

docker run --rm \
    --network container:minio \
    -v shared_data:/data \
    minio/mc -sh -c '
    mc alias set localminio "http://localhost:9000" swre_user swre_passd && \
    mc mb localminio/swre_bucket && \
    mc cp /data/shared/dummy.parquet localminio/swre_bucket/
    '



