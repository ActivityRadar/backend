# backend

Backend for the ActivityRadar platform.

## Setup

Run `pip install -r requirements.txt` in the project root after cloning and
setting up a virtual environment.

## Environment

There are a couple of environment variables needed to run the backend.
They can be found in the `.env.example`. Rename that file to `.env` and fill in
the right values for each variable.

### Variables

**Do not share any of these variables!**

`MONGODB_CONNECTION_STRING` should be the normal connection string used by mongoDB.
For a local setup, this might simply be `mongodb://localhost:27017`, if you don't
have a login set up.

`JWT_SECRET` is used for creating the auth tokens. It must be a randomly generated
32-character hex string. You can generate one of those with `openssl rand -hex 32`.

## Run

Run `uvicorn backend.main:app --reload` to start the server. Any saved changes
will make `uvicorn` reload the source files.

## Docs

See `127.0.0.1:8000/docs` for automatic and interactive API documentation.

## For development

Run `pip install -r ./requirements-dev.txt` in your environment to install extra
development tools.
We are using [`pre-commit`](https://pre-commit.com/) for automatic code formatting.

Run `pre-commit install` to set up the hooks as pre-commit hooks.

Try it out by running `pre-commit run --all-files` from the project root.

### Environment variables

For the `ggshield` pre-commit hook, you need to have a `GitGuardian` account and
generate an API-key. That key has to be put into the `.env` file in order to let
`ggshield` work and protect you from sharing secrets.

## Deployment

For deploying the backend, we are using `docker-compose`. For https support, we use
`traefik` with `Let's Encrypt`.

We currently have a test and a production setup. Either way, you'll have to do the
following:

1. Install `docker` and `docker-compose`.
2. Set the variables in the `.env` file:
   - `LETSENCRYPT_EMAIL`: To the email you are using for `Let's Encrypt`.
   - `DOMAIN_NAME`: To the domain that redirects to your server instance.
3. Set the email sending specific variables in the `.env` file
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_FROM`, `MAIL_PASSWORD`

### Test setup

1. Run `docker-compose up` to start the container stack without traefik.

### Production setup

1. Run `docker network create traefik-public` to create the docker network that
   `traefik` uses to communicate with `fastapi`.
2. Run `docker-compose -f docker-compose.traefik.yaml up` to start `traefik`.
3. Run `docker-compose -f docker-compose.yaml up` to start the rest of the containers.
