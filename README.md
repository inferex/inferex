# Inferex CLI

Inferex CLI - Init, deploy and manage your projects on Inferex infrastructure

[Please see our online documentation](https://docs.inferex.com/)

## Installation

### 0. Setup

Download the most recent version. The inferex CLI can be installed so that it
can be invoked from the command line anywhere

```shell
python setup.py install
inferex [command]
```

This may leave behind some installation artifacts in the CLI folder.

Alternatively you can add the CLI directory to your system path. On Linux this
means adding this line to ~/.profile:

```shell
export PYTHONPATH=$PYTHONPATH:/full/path/to/cli/folder
```

It is recommended to use a virtual environment. Install requirements from
requirements.txt with pip, or from pyproject.toml using poetry (poetry install).
These are located in (at the time of writing) /platform/inferex/cli.

```shell
pip install -r requirements.txt
```

or

```shell
poetry install
```

You can invoke "inferex" and it should output help text.

### 1. Project folder structure

Create or navigate to the project folder you wish to deploy. You may copy an
example project folder from the examples folder ("sentiment_analysis", etc).
Each example has inferex.yaml, pipeline.py, and requirements.txt files.

### 2. Initialization

From within this project folder, or by passing in the absolute path while using
"python -m", run the command "inferex init". You will be prompted to enter
information that will be saved locally.

### 3. Login

Run the "inferex login" command to log in and receive your API key. For local
CLI development, see "development notes" at the bottom when creating your user
on the backend for the first time.

### 4. Deploy

Run "inferex deploy". This will create a tar archive of your project folder and
send it to the server for processing.

### Troubleshooting

Having issues? Try confirming these variables:

- What is your current working directory?
- What python interpreter is being used?
- Do the credentials you saved via the browser form match those in
  credentials.json? This file is located one of these directories depending on
  your OS:

```plaintext
Mac OS X:               ~/Library/Application Support/inferex
Mac OS X (POSIX):       ~/.inferex
Unix:                   ~/.config/inferex
Unix (POSIX):           ~/.inferex
Windows (roaming):      C:\Users\<user>\AppData\Roaming\inferex
Windows (not roaming):  C:\Users\<user>\AppData\Local\inferex
```
