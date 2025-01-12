from os import getenv
from pathlib import PosixPath

from sqlalchemy import select

import gitd.logger
from gitd.config import base_dir
from gitd.db import Repo, Session

gitdir = PosixPath(getenv('GIT_DIR')).absolute()
repo_base = base_dir / 'repos'
try:
    path = gitdir.relative_to(repo_base)
except ValueError:
    print('Error: Invalid GIT_DIR')
    exit(1)

db = Session()
repo = db.scalar(select(Repo).where(Repo.path == str(path)))
if repo is None:
    print('Error: No such repository')
    exit(1)
