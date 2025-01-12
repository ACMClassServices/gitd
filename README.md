# gitd

gitd is a Git daemon for ACM class purposes.

## Requirements

- git push/pull via http(s) (not ssh, since inbound ssh connections are blocked outside SJTU campus network)
- create and delete repo via API
- per-repo disk quota
- for OJ web interface:
  - embeddable lightweight web browsing of repos
  - get a list of branches via API
  - make tags via API
  - limit creation of certain tags
- for userpage: serving selected repos via http

## Architecture

```plain
+--------------+
|        port  |
|       +----+ |   git files                           /srv/git/repos
|       |    +-+--------------------> git-http-backend (via fcgiwrap)
|       | 80 | |                                                |
|       |    +-+--------------------> cgit (via fcgiwrap)       | call
|       +----+ |   non-git files                                v
| nginx        |                                            git hooks
|       +----+ |                         update on push         |
|       | 81 +-+----> /srv/gitd/serve <-------------------------+
|       +----+ |                                                |
|              |                                                v
|       +----+ |                                        repo database
|       | 82 +-+----> API server (via gunicorn) --> /srv/gitd/gitd.db
|       +----+ |      /opt/gitd
+--------------+
```

## Deploy

```sh
echo 'username:{PLAIN}randomlygeneratedapikey' > htpasswd
docker-compose build
docker-compose up -d
```

## API

Please reverse-engineer [src/gitd/controller.py](src/gitd/controller.py).
