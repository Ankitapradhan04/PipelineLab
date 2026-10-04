# PipelineLab

A small task API, built mostly as an excuse to set up a proper GitLab CI/CD pipeline from scratch.

The app is intentionally boring: you can create, update, list and delete tasks. What I actually wanted to learn was everything around it, meaning how a change goes from a commit to a tested, scanned, containerised service with a published report, and how to make that whole path run on GitLab without any outside services.

**Live report:** `https://<your-username>.gitlab.io/pipelinelab/` (after your first pipeline on `main`)
**Container image:** `registry.gitlab.com/<your-username>/pipelinelab`

## What the pipeline does

Every push goes through five stages, defined in `.gitlab-ci.yml`:

| Stage | What happens |
|---|---|
| lint | `ruff` checks the code and its formatting |
| test | `pytest` runs with a 90% coverage gate. The same tests then run on Python 3.11 and 3.13 in parallel |
| security | GitLab SAST, GitLab secret detection, and `pip-audit` on the pinned dependencies |
| build | Builds the Docker image, starts it, waits for `/health` to answer, and only then pushes it to the GitLab Container Registry |
| deploy | Builds a small report site (test results, coverage, API endpoints) and publishes it with GitLab Pages |

The build and deploy stages only run on the default branch (and tags for the build). Merge requests get lint, tests and scans, which is usually what you want before merging anyway.

## Running it locally

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

make test      # lint is separate: make lint
make run       # API at http://127.0.0.1:8000, interactive docs at /docs
```

Or with Docker:

```bash
make docker
docker run --rm -p 8000:8000 pipelinelab:local
```

A quick try:

```bash
curl -X POST localhost:8000/tasks \
  -H "content-type: application/json" \
  -d '{"title": "read the pipeline logs", "priority": "high"}'

curl localhost:8000/tasks/stats
```

## Getting it running on your own GitLab

1. Create a new project on GitLab and push this folder to it.
2. The pipeline starts by itself. On the free tier, GitLab may ask you to verify your account before it lets shared runners run jobs. That's a one-time thing.
3. Once the pipeline on `main` finishes, your report is at `https://<username>.gitlab.io/pipelinelab/`. The first Pages deploy can take a few minutes to show up.
4. Your image is under **Deploy > Container Registry**.

Nothing needs configuring. The registry login, image name and commit hash all come from GitLab's built-in CI variables.

## Project layout

```
app/                 FastAPI app (models, in-memory store, routes)
tests/               API tests and store tests
scripts/build_site.py  builds the Pages report from the test artifacts
docs/site_template.html  template for that report
Dockerfile           small image, non-root user, health check
.gitlab-ci.yml       the pipeline
```

## Decisions worth explaining

- **In-memory storage.** Tasks disappear when the app restarts. That's fine for a pipeline demo, and it kept the focus where I wanted it. A database would be the first real upgrade.
- **Smoke test before push.** The pipeline starts the built image and calls `/health` before pushing anything. A broken image never reaches the registry.
- **`pip-audit` is allowed to fail.** A new advisory on a pinned package shouldn't block unrelated work, so it shows up as a warning instead of a red pipeline.
- **No Kubernetes or cloud deploy.** The pipeline stops at a published image and a report. I haven't deployed it anywhere, and I'd rather not pretend otherwise.
- **Pinned dependencies.** Versions are pinned so builds are repeatable. The trade-off is that you have to bump them on purpose.

## What I'd add next

- A real database with a migration step in the pipeline
- A deploy job that releases the image to a cloud host
- Merge request previews of the report site

## Honest limits

This is a learning project. It has no real users and no production traffic. I ran the app, tests, and report builder locally, and the pipeline file is checked for valid YAML, but the first run on GitLab itself may need small tweaks, so expect to read a log or two.
