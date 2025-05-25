# InternshipFinder
![Project Banner](./github_assets/InternshipFinder.png)


**InternshipFinder** is an automated internship application engine built in Python. 
> It scrapes job offers, stores and ranks them based on relevance, and sends personalized application emails — all from a single pipeline.

---

## Features

- **Web Scraping**: Extracts internship offers from the internet.
- **Vectorization**: Transforms offer content into embeddings for semantic comparison.
- **Relevance Matching**: Uses cosine similarity to rank offers against a custom query.
- **Database Storage**: Offers and applications are stored in a SQLite3 database.
- **Email Automation**: Sends applications via Gmail API, supports draft creation and sending.
- **Duplicate Filtering**: Prevents reapplication by checking offer uniqueness and past submissions.
- **Language Detection**: Automatically detects offer language to adjust email template.
- **Tagging & Logging**: Labels sent mails and logs database/application activity.
- **Configurable Strategy**: Supports brute-force mode or relevance-based filtering.

---

## Motivation

Internship hunting is time-consuming and breaks focus with constant context-switching.  
**InternshipFinder** was built to solve this by offloading the entire application loop.

---

## Architecture Overview

- `Orchestrator.py`: Orchestrates scraping, database sync, and email dispatch.
- `DBManager.py`: Handles all interactions with the SQLite3 database.
- `DeliveryMachine.py`: Gmail API interface for draft creation and email delivery.
- `ReverseHeadHunter.py`: Scrapes job offers.

---

## Security Note

API credentials and mail access are required.  
Sensitive information is never committed. `.env` variables control all credentials.

---

## Planned Improvements

- GUI for monitoring and controlling pipeline execution.
- Response tracking (email replies, follow-ups).
- Analytics on application performance (CTR, response rate, etc).

---

## Lessons & Challenges

- Designing resilient systems with minimal moving parts.
- Handling corrupt database schema in production.
- Managing concurrency with Gmail APIs and local storage.
- Making Python scripts interact with the real world through automated email delivery.

---

This was my first solo script interacting with real users — by sending emails. A real bridge between code and real world.
