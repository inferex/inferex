# Inferex CLI

Deploy and manage your AI projects on Inferex infrastructure.

[Please see our online documentation for a tutorial.](https://docs.inferex.com/)

## Installation

```bash
pip install inferex
```

You can invoke "inferex --help" for a list of commands. Each command may have
subcommands, which can be called with "--help" as well.

Version 0.0.4:

```bash
Usage: inferex [OPTIONS] COMMAND [ARGS]...

  Init, deploy, and manage your projects with Inferex.

Options:
  --version  Display version number.
  --help     Show this message and exit.

Commands:
  delete  🗑️ Delete projects, deployments, and endpoints.
  deploy  🚀 Deploy a project.
  get     🌎 Get information about Inferex resources.
  login   🔑 Fetches your API key from the server.
  logs    🗒️ Get logs from Inferex deployments.
  reset   ❌ Deletes files created at login
```

## CLI - Basic usage

1. Create or navigate to the project folder you wish to deploy. You may copy an
   example project folder from the examples folder ("face_detection",
   "sentiment_analysis", etc). Each example has inferex.yaml, pipeline.py, and
   requirements.txt files.

1. Run the "inferex login" command to log in with your inferex account
   automatically save your token locally.

1. Run "inferex deploy". This will create a tar archive of your project folder
   and send it to the server for processing.

## Troubleshooting

Having issues? Try confirming these variables:

- What is your current working directory?
- What python interpreter is being used (in bash:  'which python')?
- Do you have a token saved locally? Check this folder depending on your OS:

```plaintext
Mac OS X:               ~/Library/Application Support/inferex
Mac OS X (POSIX):       ~/.inferex
Unix:                   ~/.config/inferex
Unix (POSIX):           ~/.inferex
Windows (roaming):      C:\Users\<user>\AppData\Roaming\inferex
Windows (not roaming):  C:\Users\<user>\AppData\Local\inferex
```
