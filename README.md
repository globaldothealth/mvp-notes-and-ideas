# mvp-notes-and-ideas
Repository for the output of initial discussions regarding an MVP

## Useful resources

- `google.com`
- Johns Hopkins `https://systems.jhu.edu/research/public-health/ncov/` 

## Configuring Python

Instructions here assume Linux or macOS, please [see the Python documentation](https://docs.python.org/3/tutorial/venv.html) for Windows instructions.

1. Make sure you have python 3.6 or later.
2. Create an environment:

```console
    $ python3 -m venv /path/to/ocd-env
```

This command creates the folder `ocd-env` if it doesn't exist. You don't need to create it within this repository, it can live anywhere.

3. Activate that environment:

```console
    $ . /path/to/ocd-env/bin/activate
```

4. Install the dependencies:

```console
    $ pip install -r ./requirements.txt
```

5. Work on your Python! When you're done, deactivate the environment:

```console
    $ deactivate
```
