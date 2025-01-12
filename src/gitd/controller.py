import re
import subprocess
from http.client import (BAD_REQUEST, CREATED, INTERNAL_SERVER_ERROR,
                         NO_CONTENT, NOT_FOUND)
from logging import getLogger
from os import makedirs, removedirs
from pathlib import PosixPath
from shutil import rmtree

from flask import Flask, abort, jsonify, request
from sqlalchemy import select
from werkzeug.exceptions import HTTPException

import gitd.logger
from gitd.config import base_dir
from gitd.db import Repo, Session

logger = getLogger(__name__)

app = Flask(__name__)

repo_base = base_dir / 'repos'

path_regex = re.compile('^[0-9a-zA-Z][0-9a-zA-z_./-]{0,64}$')
def valid_path(path):
    if path is None or not isinstance(path, str):
        return False
    if '..' in path or path == '' or path[-1] == '/' or './' in path or '/.' in path:
        return False
    return path_regex.match(path) is not None

def valid_size(size):
    return 0 < size <= 100 * 1048576

commit_regex = re.compile('^[0-9a-fA-F]{40}$')
def valid_commit(commit):
    return isinstance(commit, str) and commit_regex.match(commit) is not None

def spawn(path, args, *, check=False):
    logger.debug(f'spawn {path=} {args=}')
    proc = subprocess.run([ 'timeout', '5' ] + args, cwd=repo_base / path, capture_output=True)
    if check and proc.returncode != 0:
        logger.warn(f'git error {path=} {args=} {proc.stdout=} {proc.stderr=}')
        abort(INTERNAL_SERVER_ERROR, 'Error from git')
    return proc

def check_repo_exists(path):
    with Session.begin() as db:
        repo = db.scalar(select(Repo).where(Repo.path == path))
        if repo is None:
            abort(NOT_FOUND, 'No such repo')

def check_path_not_exist(path: PosixPath):
    while path != repo_base and path.parent != path:
        if path.exists():
            abort(BAD_REQUEST, 'Invalid repo path')
        path = path.parent
    if path != repo_base:
        abort(BAD_REQUEST, 'Invalid repo path')


@app.post('/repo')
def ensure_repo():
    path = request.form['path']
    size = int(request.form['max_size_bytes'])
    serve = request.form.get('serve', 'false') == 'true'
    if not valid_path(path):
        abort(BAD_REQUEST, 'Invalid repo path')
    if not valid_size(size):
        abort(BAD_REQUEST, 'Invalid repo max size')

    logger.info(f'repo:create {path=} {size=} {serve=}')

    with Session.begin() as db:
        repo = db.scalar(select(Repo).where(Repo.path == path))
        if repo is None:
            repo_path = repo_base / path
            check_path_not_exist(repo_path)
            makedirs(repo_path)
            spawn(path, [ 'git', 'init', '--bare' ], check=True)

            repo = Repo(path=path, max_size_bytes=size, serve=serve)
            db.add(repo)
            return '', CREATED
        else:
            repo.max_size_bytes = size
            repo.serve = serve
            return '', NO_CONTENT

@app.delete('/repo')
def delete_repo():
    path = request.form['path']
    with Session.begin() as db:
        repo = db.scalar(select(Repo).where(Repo.path == path))
        if repo is None:
            abort(NOT_FOUND)

        logger.info(f'repo:delete {path=}')
        db.delete(repo)

        repo_path = repo_base / path
        rmtree(repo_path)
        removedirs(repo_path.parent)

        if repo.serve:
            serve_path = base_dir / 'serve' / path
            if serve_path.exists():
                rmtree(serve_path)
                removedirs(serve_path.parent)

    return '', NO_CONTENT

@app.post('/branches')
def get_branches():
    path = request.form['path']
    check_repo_exists(path)
    logger.debug(f'repo:branches {path=}')

    res = spawn(path, [ 'git', 'branch', '--list', '--format', '%(objectname) %(objectname:short=7) %(refname:short)' ], check=True)
    lines = [line.split(' ', maxsplit=2) for line in res.stdout.decode().splitlines()]
    return jsonify([{ 'name': name, 'commit': { 'long': long, 'short': short } } for long, short, name in lines])

@app.post('/tag')
def create_tag():
    path = request.form['path']
    tag = request.form['tag']
    commit = request.form['commit']
    if not valid_path(tag):
        abort(BAD_REQUEST, 'Invalid tag name')
    if not valid_commit(commit):
        abort(BAD_REQUEST, 'Invalid commit id')

    check_repo_exists(path)
    logger.info(f'repo:tag {path=} {tag=} {commit}')

    res = spawn(path, [ 'git', 'tag', '--force', tag, commit ])
    if res.returncode != 0:
        if b'nonexistent object' in res.stderr:
            abort(NOT_FOUND, 'No such commit')
        if b'not a valid tag name' in res.stderr:
            abort(BAD_REQUEST, 'Invalid tag name')
        logger.warn(f'git error repo::tag {path=} {res.stdout=} {res.stderr=}')
        abort(INTERNAL_SERVER_ERROR, 'Error from git')

    return '', CREATED


@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = e.description
    response.content_type = 'text/plain'
    return response
