# Inferex CLI

Deploy and manage your AI projects on Inferex infrastructure.

[See our online documentation for a tutorial.](https://docs.inferex.com/)

## Installation

```bash
pip install inferex
```

You can invoke "inferex --help" for a list of commands. Each command may have
subcommands, which can be called with "--help" as well.

Version 0.0.7:

```bash
Usage: inferex [OPTIONS] COMMAND [ARGS]...

  Inferex CLI is a tool that enables AI companies to rapidly deploy pipelines.
  Init, deploy, and manage your projects with Inferex. Invoke "inferex --help"
  for a list of commands.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  deploy      🚀 Deploy a project.
  deployment  🌎 Manage Inferex deployments.
  pipelines   📞 List pipelines for a deployment.
  init        ✨ Initializes a new project.
  login       🔑 Fetch api key via username & password authentication.
  logs        📃 Get logs from Inferex deployments.
  projects    📁 Manage Inferex projects.
  reset       ❌ Deletes the token.json file created at login.
```

## CLI - Basic usage

1. Create or navigate to the project folder you wish to deploy. You may copy an
   example project folder from the examples folder ("face_detection",
   "sentiment_analysis", etc). Each example has inferex.yaml, pipeline.py, and
   requirements.txt files.

1. Run the "inferex login" command to log in with your inferex account
   and save your token locally.

1. Run "inferex deploy". This will create a tar archive of your project folder
   and send it to the server for processing.

That's it! `inferex deployments` will list your deployed projects and their URLs.
