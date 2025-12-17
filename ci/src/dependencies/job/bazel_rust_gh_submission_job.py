import logging
import os

from integration.github.github_api import GithubApi

LOCKFILE = "Cargo.Bazel.toml.lock"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if "GITHUB_PR_DIR" in os.environ:
        basedir = os.environ["GITHUB_PR_DIR"]
    else:
        basedir = os.environ["GITHUB_WORKSPACE"]
    GithubApi.submit_dependencies([(basedir, LOCKFILE)])
