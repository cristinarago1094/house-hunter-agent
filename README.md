# 🏠 House Hunter Agent

An AI-powered real estate monitoring agent that automatically discovers, tracks and prioritizes property opportunities.

Instead of manually checking multiple real estate websites every day, House Hunter Agent continuously monitors Gmail alerts, extracts listing information, detects price drops and new opportunities, scores properties based on custom preferences and delivers actionable daily summaries.

---

# Demo

> 🚧 Currently running as a private personal automation for my own home search in Rome.

Daily workflow:

```
Real estate portals
        │
        ▼
 Gmail alerts
        │
        ▼
House Hunter Agent
        │
 ├── Extract listing data
 ├── Detect duplicates
 ├── Track price changes
 ├── Score each property
 ├── Store historical data
        │
        ▼
Daily WhatsApp digest
```

---

# Features

✅ Gmail integration

Automatically imports alerts from Immobiliare.it and Casa.it.

✅ Property extraction

Extracts structured information from every listing.

✅ Duplicate detection

Avoids processing the same property multiple times.

✅ Price tracking

Detects reductions compared with historical data.

✅ Preference scoring

Ranks every listing according to configurable buying criteria.

Examples include:

- Area
- Budget
- Size
- Number of rooms
- Floor
- Elevator
- Outdoor space

✅ SQLite persistence

Keeps historical listings and price evolution.

✅ Daily automation

Runs automatically every day using GitHub Actions.

✅ WhatsApp notifications

Sends only meaningful updates to avoid notification fatigue.

---

# Tech Stack

- Python
- Flask
- Gmail API
- Meta WhatsApp Cloud API
- SQLite
- GitHub Actions
- Render

---

# Architecture

```
                    Gmail API
                        │
                        ▼
              Import new alerts
                        │
                        ▼
             Listing extraction
                        │
                        ▼
          Duplicate verification
                        │
                        ▼
             Historical database
                        │
                        ▼
             Preference scoring
                        │
                        ▼
          Daily WhatsApp digest
```

---

# Why I built it

Buying a property is a highly manual process.

I wanted to build an autonomous system capable of monitoring hundreds of listings every day, filtering noise, tracking historical price changes and surfacing only the opportunities that match my buying criteria.

The project combines automation, APIs, persistence, scheduling and intelligent filtering into a single workflow.

---

# Project Status

✅ Gmail integration

✅ Daily scheduled execution

✅ SQLite persistence

✅ Render deployment

✅ GitHub Actions automation

✅ WhatsApp notifications

🚧 Continuous improvements

---

# Future roadmap

- AI property ranking using LLMs
- Image analysis of listings
- Interactive WhatsApp commands
- Investment score
- Market trend analysis
- Multi-city support
- Voice assistant integration

---

# Disclaimer

This project is intended for educational and personal use.

No credentials or sensitive information are stored inside the repository.
