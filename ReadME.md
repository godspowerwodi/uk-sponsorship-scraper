# UK Sponsorship Job Scraper

A lightweight Python script that checks selected companies for UK data-engineering roles and keeps only roles that appear to come from licensed UK sponsors. Newly discovered jobs can be written to a Markdown report and sent to Discord.

## What It Does

On each run, `daily_job_scraper.py`:

1. Downloads the UK Home Office Register of Licensed Sponsors for Workers and Temporary Workers.
2. Falls back to the GOV.UK publication page when the configured direct CSV URL is unavailable.
3. Queries the public job-board APIs for Greenhouse, Lever, and Ashby for every company in the configured list.
4. Filters roles whose title contains one of:
	- `data engineer`
	- `data engineering`
	- `analytics engineer`
5. Filters roles whose location contains one of:
	- `london`
	- `uk`
	- `united kingdom`
	- `remote - uk`
	- `hybrid`
6. Checks whether the company matches a licensed sponsor. Exact matches are preferred, with a longer partial-name match used as a fallback.
7. Removes jobs already recorded in `history.json`, using the job URL as the unique key.
8. Sends each new job to Discord when a webhook is configured.
9. Appends each new job to `daily_jobs.md`.

If no new jobs are found, the script prints a status message and does not create or update the report.

## Requirements

- Python 3.9 or newer
- Network access to GOV.UK, Greenhouse, Lever, Ashby, and optionally Discord

Install the Python dependencies with:

```powershell
python -m pip install -r requirements.txt
```

The dependencies are:

- `requests` for HTTP requests
- `beautifulsoup4` for locating the latest sponsor-register CSV on GOV.UK

## Configuration

The optional Discord integration is configured through the `DISCORD_WEBHOOK_URL` environment variable.

PowerShell:

```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/<webhook-id>/<webhook-token>"
```

Command Prompt:

```bat
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/<webhook-id>/<webhook-token>
```

If the variable is not set, job discovery and Markdown output still work; Discord notifications are skipped.

The role terms, location terms, and company slugs are currently defined directly in `daily_job_scraper.py` as `TARGET_TERMS`, `TARGET_LOCATIONS`, and `COMPANIES`. The company values must match the public board slugs used by the ATS providers.

## Running It

From the repository directory:

```powershell
python daily_job_scraper.py
```

The script prints progress while it downloads sponsors, checks ATS endpoints, identifies new jobs, and sends notifications.

This repository does not include a scheduler. To run it daily, invoke the command from an external scheduler such as Windows Task Scheduler, GitHub Actions, or cron. Run it from the repository directory so that `history.json` and `daily_jobs.md` are read and written in the expected location.

## Generated Files

These files are created at runtime and are intentionally not part of the source configuration:

### `history.json`

Stores previously processed job URLs. It prevents the same job from generating another alert on later runs. The file is written only when at least one new job is found.

### `daily_jobs.md`

An append-only Markdown log. The first successful write adds the document title, followed by dated sections containing company, job title, location, and application links.

## Discord Notifications

Each new job is sent as a Discord embed containing:

- Company and job title
- Location
- An `Apply Here` link
- The footer `UK Sponsorship Job Validator`

The message currently includes the role mention `<@&123456789>`. Replace that role ID in `send_discord_webhook()` if a different Discord role should be notified. Keep the webhook URL private and do not commit it to the repository.

## Important Limitations

- Only the companies listed in `COMPANIES` are checked.
- ATS availability varies by company. Non-existent boards, API errors, malformed responses, and request failures are silently skipped by the individual provider checks.
- Sponsor matching is based on company-name strings, not Companies House identity, legal-entity verification, or a guarantee that a specific vacancy is eligible for sponsorship.
- Location matching is substring-based. A broad term such as `uk` can match other text containing those letters, and `hybrid` does not prove that the role is UK-based.
- A job is considered seen by URL only. Changed or reused URLs may therefore be treated as the same job.
- The script uses `verify=False` for the sponsor-register requests and suppresses the related warning. This avoids certificate issues with that source but disables TLS certificate verification for those requests; production use should restore certificate verification where possible.
- The direct sponsor CSV URL contains a dated filename and may need updating if GOV.UK changes its publication structure. The fallback attempts to discover a current matching CSV from the publication page.
- Discord POST requests do not specify a timeout or inspect the response status, so a slow or unsuccessful webhook request may not be reported clearly.

## Project Files

| File | Purpose |
| --- | --- |
| `daily_job_scraper.py` | Sponsor download, ATS fetching, filtering, deduplication, notifications, and report generation |
| `requirements.txt` | Python package dependencies |
| `ReadME.md` | Project documentation |

## Troubleshooting

**No jobs are found**

Check the console output, confirm that the ATS company slugs are still valid, and review the title and location filters in `daily_job_scraper.py`.

**The sponsor list cannot be loaded**

Confirm network access to GOV.UK and check whether the publication page or CSV format has changed. The script exits before checking jobs when no sponsor data is loaded.

**Discord alerts are missing**

Confirm that `DISCORD_WEBHOOK_URL` is set in the same environment that runs the script and that the webhook is still valid. A missing variable intentionally disables notifications.

**A previously alerted job appears again**

Inspect `history.json` and confirm that the job URL has not changed. Deleting or replacing that file resets the deduplication history.
