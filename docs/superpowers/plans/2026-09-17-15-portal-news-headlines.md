# 15-Portal Bangladesh News Headlines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Bootstrap 5.3 static news dashboard that displays at least 10 headlines from each of 15 Bangladesh news portals and refreshes the source data every 5 minutes through GitHub Actions.

**Architecture:** A GitHub Actions scheduled workflow runs the Python collector every five minutes. The collector reads RSS feeds when available and falls back to the publisher homepage when necessary, writes `data/headlines.json`, and deploys the complete static site to GitHub Pages. The browser reads the generated JSON and refreshes it every five minutes.

**Tech Stack:** Bootstrap 5.3, vanilla JavaScript, Python 3.12, requests, feedparser, BeautifulSoup, pytest, GitHub Actions, GitHub Pages.

**Spec:** Approved chat design for 15 portals, minimum 10 headlines per portal, five-minute automated collection, GitHub-based deployment.

## Global Constraints

- 15 configured publishers.
- Target at least 10 usable headlines per publisher.
- Prefer publisher RSS feeds; use homepage extraction as fallback.
- Store headline title, source URL, article URL, and available publication time.
- Do not copy full article bodies.
- GitHub Actions schedule is five minutes.
- GitHub Pages hosts only static frontend output.
- Source failures must not prevent other sources from rendering.
