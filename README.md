# Publicly Available Data

Publicly available data from Logos Circle Ruse.

## Pipelines

Github Actions workflow [`data-extraction.yml`](./.github/workflows/data-extraction.yml) runs the data pipelines.

### `circles.py`

Extract data from publicly available [Institute of Free Technology](https://free.technology/) [REST API](https://hasura.bi.status.im/api/rest/circle/events). Data can be found on [**About us** page](https://logos-circle-ruse.github.io/about.html).

### `winnable_issues.py`

Extract the winnable issues from Logos Circle Ruse and show overall statistics on our website.