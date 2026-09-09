<h1 align="center">
  🚀 Sponsorship Scout
</h1>

<p align="center">
  <strong>An automated, multi-tenant scraper for finding UK Visa Sponsored jobs across ATS platforms.</strong>
</p>

<p align="center">
  <a href="https://uk-sponsorship-scraper.streamlit.app/"><strong>🔥 Try the Live Public App Here! 🔥</strong></a>
</p>

![Sponsorship Scout Dashboard](docs/screenshot.png)

## 📌 What is it?
Sponsorship Scout is a robust Python package that dynamically scrapes popular ATS (Applicant Tracking System) platforms (Greenhouse, Lever, Ashby, SmartRecruiters) and cross-references the hiring companies against the **official UK Government Register of Licensed Sponsors**. 

It guarantees that every job it finds is from a company officially licensed to offer UK Visa Sponsorship.

---

## 🌐 Try the Live Public App
Don't want to install anything? We host a live, real-time search engine for sponsored jobs directly on Streamlit Community Cloud.

👉 **[Launch UK Sponsorship Job Scout](https://uk-sponsorship-scraper.streamlit.app/)** 👈

---

## ✨ Features
- **🌍 Multi-Tenant:** Configure unlimited profiles for yourself and friends in a single YAML file.
- **⚡ Async Engine:** Blazing fast concurrent scraping of over 60,000+ endpoints.
- **🛡️ Gov.uk Validation:** Automatically downloads the latest official UK Sponsor Register to filter companies.
- **🔌 Pluggable Destinations:** Send newly found jobs to **Discord**, a **GitHub Gist**, or a **local SQLite database**.
- **📊 Streamlit Dashboards:** Includes a beautiful local dashboard to view your database, and a public-facing ad-hoc search app.
- **🕰️ Built-in Scheduler:** Run it once, or leave it running continuously in the background.

---

## 🛠️ Installation

Sponsorship Scout is officially available on PyPI! You can install it using your preferred Python package manager.

### Option A: Using `uv` (Recommended)
`uv` is incredibly fast and installs the CLI tool into an isolated global environment:

```bash
uv tool install sponsorship-scout
```
*(Or run it instantly without installing: `uvx sponsorship-scout run --config config.yaml`)*

### Option B: Using `pip`
```bash
pip install sponsorship-scout
```

---

## 🚀 Quick Start (Local CLI & Config)

The scraper uses a declarative `config.yaml` to define profiles and destinations.

### 1. Create a `config.yaml`
Create a file named `config.yaml` in your working directory:

```yaml
profiles:
  - name: "Software Engineer"
    target_terms: ["software", "backend", "python"]
    target_locations: ["london", "uk"]
    industry_keywords: ["tech", "software"]
    destinations:
      - type: sqlite
        table_name: "software_jobs"
      - type: discord
        webhook_url: "https://discord.com/api/webhooks/..."
```

> **?? Pro Tip on `industry_keywords`**: 
> * **The Fast Path**: Specifying keywords like `["tech", "software"]` filters the 127,000+ UK sponsors down to matching companies, making the CLI finish scraping in under 5 minutes.
> * **God Mode**: If you set `industry_keywords: []`, the engine completely bypasses the filter and scans **all 127,000+ UK sponsors** against the ATS APIs. This guarantees you catch jobs from giants like Monzo or Revolut (who don't have "tech" in their legal name), but the scan will take around ~2.5 hours to complete.

### 2. Run the CLI
The `sponsorship-scout` command is now available in your terminal:

```bash
# Run a one-off scrape
sponsorship-scout run --config config.yaml

# Run continuously every 24 hours
sponsorship-scout start-schedule --config config.yaml --hours 24
```

### 3. View the Dashboard
Once the scraper has populated your SQLite database, you can view the jobs in the beautiful local web dashboard:

```bash
sponsorship-scout ui --config config.yaml
```
