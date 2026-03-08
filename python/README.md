# pi-tk-flow-ui

Standalone Textual TUI for browsing pi-tk-flow tickets and plans.

## Install globally with uv

From a git source:

```bash
uv tool install --from 'git+https://github.com/legout/pi-tk-flow[ui]' tf-ui
```

From a local checkout:

```bash
uv tool install --from '.[ui]' tf-ui
```

## Run without installing

From a local checkout:

```bash
uvx --from '.[ui]' tf-ui
```

From git directly:

```bash
uvx --from 'git+https://github.com/legout/pi-tk-flow[ui]' tf-ui
```

## Local development install

```bash
pip install -e '.[ui]'
tf-ui
```

## Usage

```bash
tf-ui
tf-ui --web
```
