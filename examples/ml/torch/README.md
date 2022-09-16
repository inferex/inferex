# MNIST Torch example

This example is slightly more complex than our other examples because it contains code to train models also. It is designed to be a slightly less "isolated" use case of our system

## Usage

1) Setup virtual environment

    ```python
    python3 -m venv env3
    pip install -r requirements.txt
    source env3/bin/activate
    ```

2) Train a new model by running:

   `python pipeline.py`

    This will download the MNIST data if it doesn't exist already in './data' and then train a simple model for 2 epochs

3) Delete the sample data and deploy the model:

    ```bash
    rm -rf ./data
    inferex deploy
    ```

