# Unified Setup Guide

Use **one command** for setup:

```bash
./setup.sh
```

This is a self-serving, repeatable, zero-touch flow (except OpenAI API key if not already exported).

## What `./setup.sh` does

It always runs these three scripts in order:

1. `./scripts/install_dependencies.sh` (installs required system dependencies)
2. `./bootstrap.sh` (generates defaults, secrets, and env files)
3. `./deploy.sh` (builds/starts containers and initializes app data)

## Prompt behavior

- You are only prompted for `OPENAI_API_KEY` if it is not already set in your shell.
- To make setup fully non-interactive, export it first:

```bash
export OPENAI_API_KEY='sk-...'
./setup.sh
```

## Generated reference file

Setup writes a consolidated reference file containing generated defaults and active env values:

- `setup_reference.env`

Keep this file secure.

## Local setup (default)

```bash
./setup.sh
```

## Production setup

```bash
APP_DOMAIN=yourdomain.com ./setup.sh --prod
```

Optional flags:

- `--force` overwrites existing env file
- `--regen-secrets` regenerates `generated_secrets.env`

## Manual advanced flow (optional)

If you want to run steps yourself:

```bash
./scripts/install_dependencies.sh [--prod]
./bootstrap.sh [--prod] [--force] [--regen-secrets]
./deploy.sh [--prod]
```
