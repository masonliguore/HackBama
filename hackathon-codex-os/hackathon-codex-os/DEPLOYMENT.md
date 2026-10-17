# Deployment notes

Deployment remains optional. Neither template is published, and no account or secret was connected.

## GitHub repository (not created)

GitHub CLI (`gh`) is not installed, so authentication and repository access could not be checked. After installing it and reviewing the visibility choice, these are the local commands; they create/publish a remote only when you explicitly run them:

```bash
gh auth status
gh repo create hackbama-project --private --source . --remote origin --push
```

Change `--private` only if the event requires a public repository and you have reviewed the source for secrets and disclosure requirements.

## Streamlit Community Cloud

1. Put the Streamlit app and `requirements.txt` at the chosen repository path (the current app is `templates/engineering-dashboard`).
2. Push the project to a GitHub repository you control after reviewing event code-reuse and visibility rules.
3. In Streamlit Community Cloud, create an app from that repository, branch, and `templates/engineering-dashboard/app.py` entrypoint.
4. Deploy, then open the URL in a private window and exercise all three inputs.

No secrets are needed by this sample. Add future credentials through the host's secret manager, never source control. Community Cloud requires a connected account and internet; neither is configured here.

## Vercel (React/Vite)

From `templates/engineering-web`, use framework preset **Vite**, build command `npm run build`, output directory `dist`, and no install-time environment variables. The included `vercel.json` sets the same values. Vercel CLI and authentication were not available/checked, so deployment was not attempted.

```bash
npm ci
npm run build
npx vercel
```

The `npx vercel` command requires network access, a Vercel account, and explicit approval before connecting or publishing. Choose a project and access policy before running it. This static client-side app needs no API server.

## Local configuration checks

JSON configuration parses with Python's standard library. A production build and live deployment must be checked in an environment with Node/npm and the relevant account access.
