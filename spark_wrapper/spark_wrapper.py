#!/usr/bin/python3

# ===========================================
# script based on the work from
# @luisteod at
# https://github.com/luisteod/spark_wrapper/wrapper/spark-wrapper.py
# + overall cleaning
# + ci and other utils such as papermill remote connection
# ===========================================

from pyspark import SparkConf
from pyspark.sql import SparkSession
import logging
# Configure the logging system
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
        )


class SparkWrapper:
    """
    Wrapper class to simplify the configuration of pyspark by using an
    S3 data-lake with postgres support

    The URI connector comes from hadoop, in 's3a://'

    PySpark Driver
    |
    ├──> SparkContext
    |      |
    |      └──> Hadoop FileSystem APIs (S3A connector)
    |               |
    |               └──> S3 connector (hadoop-aws + aws-java-sdk)
    |                       |
    |                       └──> S3 Object Store (e.g. AWS S3, minio)
    |
    └──> SparkSession.read.jdbc(...)
          |
          └──> Java JDBC Driver (via JVM bridge)
                 |
                 └──> PostgreSQL server
    """
    session: SparkSession = None

    def __init__(
        self,
        num_cores: int = 2,
        memory_gb: int = 4,
    ):
        self.driver_cores = num_cores
        self.driver_memory_gb = str(memory_gb) + "g"

    def create_session(self) -> SparkSession:
        """
        Create spark session

        Parameters
        ----------------

        """

        conf = SparkConf() \
                .setAppName("App") \
                .setMaster(f"local[{self.driver_cores}]")

        # conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")

        conf.set(
                "spark.hadoop.fs.s3a.impl",
                "org.apache.hadoop.fs.s3a.S3AFileSystem")
        conf.set(
            "spark.jars.packages",
            ("org.apache.hadoop:hadoop-aws:3.2.2,org.postgresql"
             ":postgresql:42.7.3"),
        )
        conf.set(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )

        # conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")
        # conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")
        # conf.set("spark.sql.adaptive.enabled", "true")
        # conf.set("spark.sql.parquet.filterPushdown", "true")
        # conf.set("spark.sql.shuffle.partitions", "1000")

        conf.set("spark.driver.cores", self.driver_cores)

        conf.set("spark.driver.memory", self.driver_memory_gb)
        conf.set("spark.memory.offHeap.enabled", "true")
        conf.set("spark.memory.offHeap.size", self.driver_memory_gb)

        try:
            conf.set("spark.hadoop.fs.s3a.access.key",
                     self.s3_conf["access_key"])
            conf.set("spark.hadoop.fs.s3a.secret.key",
                     self.s3_conf["secret_key"])
            conf.set("spark.hadoop.fs.s3a.endpoint",
                     self.s3_conf["endpoint_url"])
        except Exception as e:
            logging.info(f"Error: {e} - AWS S3 configuration not set")

        try:
            assert self.pg_conf is not None
        except Exception as e:
            logging.info(f"Error: {e} - Postgres configuration not set")

        spark = SparkSession.builder.config(conf=conf).getOrCreate()

        self.session = spark
        return spark

    # set postgres configuration
    def set_pg_conf(self, user, pwd, host, port, db):

        self.pg_conf = {
            "user": user,
            "pwd": pwd,
            "host": host,
            "port": port,
            "db": db,
        }

        return self

    # set aws s3 configuration
    def set_s3_conf(self, access_key, secret_key, endpoint_url):

        self.s3_conf = {
            "access_key": access_key,
            "secret_key": secret_key,
            "endpoint_url": endpoint_url,
        }

        return self

    def send_pg(self, df, schema_table, mode):

        if self.pg_conf is None:
            raise Exception("Postgres connection is not set")

        jdbc_url = (
            "jdbc:postgresql://"
            + self.pg_conf["host"]
            + ":"
            + str(self.pg_conf["port"])
            + "/"
            + self.pg_conf["db"]
        )

        df.write.format("jdbc").option("url", jdbc_url).option(
            "dbtable", schema_table
        ).option("user", self.pg_conf["user"]).option(
            "password", self.pg_conf["pwd"]
        ).option(
            "driver", "org.postgresql.Driver"
        ).mode(
            mode
        ).save()

        return True

    def read_pg(self, schema_table):

        if self.pg_conf is None:
            raise Exception("Postgres connection is not set")

        jdbc_url = (
            "jdbc:postgresql://"
            + self.pg_conf["host"]
            + ":"
            + str(self.pg_conf["port"])
            + "/"
            + self.pg_conf["db"]
        )

        df = self.session.read.format("jdbc").option("url", jdbc_url).option(
            "dbtable", schema_table
        ).option("user", self.pg_conf["user"]).option(
            "password", self.pg_conf["pwd"]
        ).option(
            "driver", "org.postgresql.Driver"
        ).load()

        return df


if __name__ == "__main__":
    pass
