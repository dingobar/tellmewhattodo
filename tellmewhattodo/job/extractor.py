from abc import ABC, abstractmethod
import datetime
from os import getenv
from pathlib import Path
import sys
from typing import Any
import requests
import yaml
from tellmewhattodo.models.alert import Alert


class BaseExtractor(ABC):
    @abstractmethod
    def check(self) -> list[Alert]:
        pass


class GitHubReleaseExtractor(BaseExtractor):
    def __init__(self, repository: str) -> None:
        self.REPOSITORY = repository

    def check(self) -> list[Alert]:
        auth_token = getenv("GITHUB_PAT_TOKEN")
        auth = ("token", auth_token) if auth_token else None
        r = requests.get(
            f"https://api.github.com/repos/{self.REPOSITORY}/releases",
            auth=auth,
        )
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            print(e)
            return []

        body: list[dict[str, Any]] = r.json()

        alerts = []
        for release in body:
            if release["prerelease"] or release["draft"]:
                continue
            alerts.append(
                Alert(
                    id=str(release["id"]),
                    name=release["name"],
                    description=f"{self.REPOSITORY} released {release['name']}",
                    datetime=release["created_at"],
                    active=True,
                    url=release["html_url"],
                )
            )

        return alerts


def get_extractors() -> list[BaseExtractor]:
    extractor_config_path = Path.cwd() / "tellme.yml"

    with open(extractor_config_path) as config:
        extractor_config = yaml.safe_load(config)
    
    extractors = []
    for extractor in extractor_config["extractors"]:
        instance = getattr(sys.modules[__name__], extractor["type"])(**extractor["config"])
        extractors.append(instance)

    return extractors
