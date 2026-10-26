# CRL Battle Image Renderer — Free Github Actions

Render 2400 × 1120 pixel Clash Royale 20-Win challenge graphics with actual Clash Royale API card icons using Pillow, independent of Google Slides. Designed to work with the **existing** `update20WinChallenge` Google Apps Script. It currently offers a **test** bridge only; do not change automated milestones until the images and rate limits are validated.

## Cost and privacy

- GitHub Actions on **public repositories** using standard runners is free; private repositories have monthly free quotas and may require a payment method if billing is blocked. Never commit your Discord webhook, GitHub personal access token, or Clash Royale API token.
- Player names, clans, card lists and counts are sent in the GitHub dispatch event; Actions logs and workflow details have visibility implications, particularly in public repositories. These are public game data, but be mindful of names.
- No Google Slides API or new paid Google Cloud project is required.

## Install

1. Create a **public** GitHub repository named `crl-battle-renderer`.
2. Upload `render.py`, `requirements.txt`, and `.github/workflows/battle-image.yml` to the repository. The workflow **must** be at exactly `.github/workflows/battle-image.yml` on the default branch. If your computer hides `.github`, create the nested path with GitHub's `Add file > Create new file` and paste the YAML.
3. For the first test you don't need a Discord webhook secret. The test runs in `previewOnly` mode and stores a PNG artifact in Actions.
4. In GitHub, go to your profile **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**. Choose only the renderer repository and grant **Contents: Read and write** permission (required for the repository dispatch API). Restrict token expiration appropriately. Never put the token inside repository files or chat messages.
5. In Google Apps Script **Project Settings > Script Properties**, add:
   - `CRL_GITHUB_REPO` = `<your-github-username>/crl-battle-renderer`
   - `CRL_GITHUB_TOKEN` = the fine-grained token
6. Copy code from `apps-script-bridge.js` to the bottom of your existing Apps Script `Code.gs`. **Do not replace your other functions.**
7. Verify that `20_WIN_TEST_BATTLE` exists in Script Properties (previous tests saved Vitor's 17-win battle).
8. Run `previewSaved20WinOnGithub` in Apps Script. This uses saved data, no Clash Royale API request, no Discord post.
9. In GitHub > your repository > **Actions** > **CRL Battle Image** > newest run, download the `crl-preview-...` artifact and inspect the PNG.

## When you're satisfied with the image

1. Go to GitHub repository **Settings > Secrets and variables > Actions > New repository secret** and name it `DISCORD_WEBHOOK` (copy value from your existing Apps Script property; don't paste into GitHub code).
2. Run `postSaved20WinFromGithub` to post **one** image. It is an explicit test and will duplicate Vitor's earlier test message.
3. Only after Discord delivery succeeds, integrate `dispatch20WinToGithub_` with the existing milestone detection, plus retry and durable deduplication. **The bridge does not yet auto-post.** Historical battles only exist in the Clash Royale API's recent battlelog window; backfill cannot recover battles no longer returned.

## Notes

The image renderer uses card icon URLs from battle data, preserves proportions, and creates its PNG at native 2400 × 1120. If Discord returns rate-limit errors (e.g. 429, Cloudflare 1015), do not spam retries. GitHub Action failures show in the Actions page; do not count a job as delivered just because repository dispatch returned HTTP 204.
