# Configured Sources

Exactly the 15 portals requested, in order. Feed availability is rechecked on every run; if a feed fails or returns too few items the collector falls back to parsing the homepage.

1. **বাংলাদেশ প্রতিদিন** — https://www.bd-pratidin.com/ — RSS: `https://www.bd-pratidin.com/rss.xml` ✅
2. **প্রথম আলো** — https://www.prothomalo.com/ — RSS: `https://www.prothomalo.com/feed/` ✅
3. **কালবেলা** — https://www.kalbela.com/ — Bing News mirror (`site:kalbela.com`); direct site blocks bots
4. **ঢাকা পোস্ট** — https://www.dhakapost.com/ — Bing News mirror + `/latest-news` page fallback
5. **এশিয়া পোস্ট** — https://www.asia-post.com/ — RSS: `https://www.asia-post.com/feed` ✅
6. **জাগো নিউজ ২৪** — https://www.jagonews24.com/ — RSS: `https://www.jagonews24.com/rss/rss.xml` ✅
7. **কালের কণ্ঠ** — https://www.kalerkantho.com/ — Bing News mirror + print-archive page fallback (Cloudflare blocks direct feeds)
8. **যুগান্তর** — https://www.jugantor.com/ — Bing News mirror (`site:jugantor.com`); direct site blocks bots
9. **সমকাল** — https://samakal.com/ — RSS: `https://samakal.com/rss` ✅
10. **বিডিনিউজ২৪ বাংলা** — https://bangla.bdnews24.com/ — homepage parsing with hex-id article filter
11. **ডেইলি স্টার বাংলা** — https://bangla.thedailystar.net/ — RSS: `https://bangla.thedailystar.net/rss.xml` ✅
12. **TBS বাংলা** — https://www.tbsnews.net/bangla/ — RSS: `https://www.tbsnews.net/bangla/rss.xml` ✅
13. **ইত্তেফাক** — https://www.ittefaq.com.bd/ — RSS: `https://www.ittefaq.com.bd/feed/` ✅ (discovered from homepage markup)
14. **ঢাকা ট্রাইবিউন বাংলা** — https://bangla.dhakatribune.com/ — no stable RSS; homepage fallback
15. **বাংলানিউজ২৪** — https://www.banglanews24.com/ — RSS: `https://www.banglanews24.com/rss.xml` ✅

✅ = verified returning valid RSS XML during development (September 2026).

Bing News mirror feeds (`https://www.bing.com/news/search?q=site%3A<domain>&format=RSS`) are used for sites that block datacenter traffic; the collector unwraps Bing's redirect links to the original article URLs.

As a last resort, the collector also queries **Google News site-search RSS** (`https://news.google.com/rss/search?q=site:<domain>&hl=bn&gl=BD&ceid=BD:bn`). This always yields items, but its article links point to `news.google.com` redirect pages — clicking them still opens the real article, so they are only accepted when every earlier strategy failed.

Publishers can change or remove feeds at any time; the multi-feed and page fallbacks keep those sources working when that happens.
