#%%
import sys; sys.path.append("../")
from spark_wrapper.spark_wrapper import SparkWrapper
from dotenv import load_dotenv; load_dotenv()
import os

ak = os.getenv("S3_ACCESS_KEY")
sk = os.getenv("S3_SECRET_KEY")
ep = os.getenv("S3_ENDPOINT_URL")

pg_user = os.getenv("PG_USER")
pg_pwd = os.getenv("PG_PWD")
pg_host = os.getenv("PG_HOST")
pg_port = os.getenv("PG_PORT")
pg_db = os.getenv("PG_DB")

#%%
sw = SparkWrapper(num_cors=1, memory_gb=2) \
    .set_s3_conf(ak, sk, ep) \
    .set_pg_conf(pg_user, pg_pwd, pg_host, pg_port, pg_db)

spark = sw.create_session()
#%%

df = spark.read.parquet('s3a://swre_bucket/dummy.parquet')
df.show()
#%%
#Postgres
schema_table = "redes_sociais.linkedins_crawleados"
df = sw.read_pg(schema_table=schema_table)
df.show()
