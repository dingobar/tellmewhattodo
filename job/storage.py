from abc import ABC, abstractmethod
from os import getenv
from pathlib import Path
import tempfile
import pandas as pd
import boto3
from botocore.exceptions import ClientError

from models.alert import Alert


class BaseStorage(ABC):
    @abstractmethod
    def write(self, df: pd.DataFrame):
        pass

    @abstractmethod
    def read(self) -> pd.DataFrame:
        pass


class LocalStorage(BaseStorage):
    """Store as local file"""

    def __init__(self) -> None:
        self.PATH = Path.cwd() / ".whattodo" / "whattodo.csv"

    def write(self, df: pd.DataFrame):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.PATH, index=False)

    def read(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.PATH, dtype="str")
        except FileNotFoundError as e:
            print(e)
            return pd.DataFrame(
                columns=[k for k, _ in Alert.schema()["properties"].items()]
            )


class S3Storage(BaseStorage):
    """Store as CSV file"""

    def __init__(self, bucket: str) -> None:
        self.BUCKET = bucket
        self.KEY = "whattodo.csv"
        self.S3_ENDPOINT = getenv("S3_ENDPOINT_URI")

    def write(self, df: pd.DataFrame):
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / self.KEY
            df.to_csv(filename, index=False)
            boto3.client("s3", endpoint_url=self.S3_ENDPOINT).upload_file(
                str(filename), self.BUCKET, self.KEY
            )

    def read(self) -> pd.DataFrame:
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / self.KEY
            try:
                boto3.client("s3", endpoint_url=self.S3_ENDPOINT).download_file(
                    self.BUCKET, self.KEY, str(filename)
                )
                return pd.read_csv(filename)
            except ClientError as e:
                print(e)
                return pd.DataFrame(
                    columns=[k for k, _ in Alert.schema()["properties"].items()]
                )
