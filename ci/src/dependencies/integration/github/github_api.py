import logging
import os
import typing
from parser.bazel_toml_parser import parse_bazel_toml_to_gh_manifest

import requests

from integration.github.github_dependency_submission import GHSubDetector, GHSubJob, GHSubRequest

# Github dataclass has len(token) > 0 assertion, so we set a placeholder
# value and validate against it.
TOKEN_NOT_SET = "token-not-set"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", TOKEN_NOT_SET)
if GITHUB_TOKEN == TOKEN_NOT_SET:
    logging.warning("GITHUB_TOKEN is not set, can not send comments and dependencies to Github")

GITHUB_REPOSITORY = os.environ.get("CI_PROJECT_PATH", "dfinity/ic")
DELTA_HEADER = "*Vulnerable dependency information*"


class GithubApi:

    @staticmethod
    def submit_dependencies(toml_lock_filenames: typing.List[typing.Tuple[str, str]]) -> None:
        def get_sha():
            if "GITHUB_PR_SHA" in os.environ:
                return os.environ["GITHUB_PR_SHA"]
            return os.environ["GITHUB_SHA"]

        if toml_lock_filenames is None or len(toml_lock_filenames) == 0:
            raise RuntimeError("No toml lock files provided")

        if GITHUB_TOKEN == TOKEN_NOT_SET:
            raise RuntimeError("Dependency submission not possible because GITHUB_TOKEN not set")

        detector = GHSubDetector("bazel-rust-detector", "0.0.1", "https://github.com/dfinity/ic")
        job = GHSubJob(os.environ["GITHUB_RUN_ID"], f'{os.environ['GITHUB_WORKFLOW']} / {os.environ['GITHUB_JOB']}')

        manifests = []
        for basedir, filepath in toml_lock_filenames:
            manifests.append(parse_bazel_toml_to_gh_manifest(basedir, filepath))

        req = GHSubRequest(0, job, get_sha(), os.environ["GITHUB_REF"], detector, manifests)

        # https://docs.github.com/en/rest/dependency-graph/dependency-submission?apiVersion=2022-11-28#create-a-snapshot-of-dependencies-for-a-repository
        url = f'https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/dependency-graph/snapshots'
        logging.debug(f"Submitting request to {url} with payload: {req.to_json()}")
        resp = requests.post(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}, json=req.to_json())
        if resp.status_code != 201:
            raise RuntimeError(f"Dependency submission failed with status code {resp.status_code}")
