import json
import argparse
from glob import glob
from loguru import logger
from lean_dojo import LeanGitRepo, trace, is_available_in_cache


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, default="data")
    args = parser.parse_args()
    logger.info(args)
    print(f"{args.data_path}/*/*/*.json")
    url_commits = set()
    for path in glob(f"{args.data_path}/*/*/*.json"):
        data = json.load(open(path))
        for ex in data:
            url_commits.add((ex["url"], ex["commit"]))

    url_commits = {('https://github.com/yangky11/miniF2F-lean4', 'eddb5ca1fa7dea7268d3feabd7e6fd451b5ef3dd')}
    repos = set()
    for url, commit in url_commits:
        repo = LeanGitRepo(url, commit)
        if not is_available_in_cache(repo) and not repo.is_lean4:
            repos.add(repo)

    logger.info(f"Repos to trace: {repos}")

    for repo in repos:
        trace(repo)


if __name__ == "__main__":
    main()