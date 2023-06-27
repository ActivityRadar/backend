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
