"""
WoW BiS Scraper
Renders each Wowhead spec BIS guide with a headless browser and extracts
the "Overall BiS" table. Outputs bis_data.json.
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

def _s(cls, spec, role, url_class=None, url_spec=None):
    url_class = url_class or cls.lower().replace(" ", "-")
    url_spec = url_spec or spec.lower().replace(" ", "-")
    return {
        "class": cls,
        "spec": spec,
        "role": role,
        "url": f"https://www.wowhead.com/guide/classes/{url_class}/{url_spec}/bis-gear",
    }

SPECS = [
    # Death Knight
    _s("Death Knight", "Blood",  "Tank"),
    _s("Death Knight", "Frost",  "DPS"),
    _s("Death Knight", "Unholy", "DPS"),
    # Demon Hunter
    _s("Demon Hunter", "Havoc",      "DPS"),
    _s("Demon Hunter", "Vengeance",  "Tank"),
    # Druid
    _s("Druid", "Balance",     "DPS"),
    _s("Druid", "Feral",       "DPS"),
    _s("Druid", "Guardian",    "Tank"),
    _s("Druid", "Restoration", "Healer"),
    # Evoker
    _s("Evoker", "Augmentation", "DPS"),
    _s("Evoker", "Devastation",  "DPS"),
    _s("Evoker", "Preservation", "Healer"),
    # Hunter
    _s("Hunter", "Beast Mastery",  "DPS", url_spec="beast-mastery"),
    _s("Hunter", "Marksmanship",   "DPS"),
    _s("Hunter", "Survival",       "DPS"),
    # Mage
    _s("Mage", "Arcane", "DPS"),
    _s("Mage", "Fire",   "DPS"),
    _s("Mage", "Frost",  "DPS"),
    # Monk
    _s("Monk", "Brewmaster", "Tank"),
    _s("Monk", "Mistweaver", "Healer"),
    _s("Monk", "Windwalker", "DPS"),
    # Paladin
    _s("Paladin", "Holy",        "Healer"),
    _s("Paladin", "Protection",  "Tank"),
    _s("Paladin", "Retribution", "DPS"),
    # Priest
    _s("Priest", "Discipline", "Healer"),
    _s("Priest", "Holy",       "Healer"),
    _s("Priest", "Shadow",     "DPS"),
    # Rogue
    _s("Rogue", "Assassination", "DPS"),
    _s("Rogue", "Outlaw",        "DPS"),
    _s("Rogue", "Subtlety",      "DPS"),
    # Shaman
    _s("Shaman", "Elemental",   "DPS"),
    _s("Shaman", "Enhancement", "DPS"),
    _s("Shaman", "Restoration", "Healer"),
    # Warlock
    _s("Warlock", "Affliction",  "DPS"),
    _s("Warlock", "Demonology",  "DPS"),
    _s("Warlock", "Destruction", "DPS"),
    # Warrior
    _s("Warrior", "Arms",       "DPS"),
    _s("Warrior", "Fury",       "DPS"),
    _s("Warrior", "Protection", "Tank"),
]

ITEM_ID_RE = re.compile(r"/item=(\d+)/")


def parse_bis_table(html: str, spec_label: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Try the canonical ID first, then fall back to any tab-bis-items-* div
    container = soup.find("div", id="tab-bis-items-overall-bis")
    if not container:
        for div in soup.find_all("div", id=True):
            if div["id"].startswith("tab-bis-items-"):
                candidate = div.find("table")
                if candidate:
                    rows = candidate.find_all("tr")
                    if rows and "Slot" in rows[0].get_text():
                        container = div
                        print(f"  INFO: Using fallback tab #{div['id']} for {spec_label}")
                        break

    if not container:
        print(f"  WARNING: No BiS tab found for {spec_label}")
        return []

    table = container.find("table")
    if not table:
        print(f"  WARNING: No table inside BiS tab for {spec_label}")
        return []

    items = []
    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header row
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        slot = cells[0].get_text(strip=True)

        # Search all cells for the item link (some guides add extra columns e.g. enchant)
        item_link = None
        item_cell_idx = None
        for idx, cell in enumerate(cells[1:], start=1):
            link = cell.find("a", attrs={"data-entity": "item"})
            if link:
                item_link = link
                item_cell_idx = idx
                break

        if not item_link:
            continue

        href = item_link.get("href", "")
        id_match = ITEM_ID_RE.search(href)
        item_id = int(id_match.group(1)) if id_match else None

        name_span = item_link.find("span", class_="tinyicontxt")
        item_name = name_span.get_text(strip=True) if name_span else item_link.get_text(strip=True)

        source_cell_idx = item_cell_idx + 1
        source = cells[source_cell_idx].get_text(strip=True) if source_cell_idx < len(cells) else ""

        items.append({
            "slot": slot,
            "item_id": item_id,
            "item_name": item_name,
            "source": source,
            "wowhead_url": f"https://www.wowhead.com/item={item_id}" if item_id else None,
        })

    return items


MAX_RETRIES = 3
RETRY_DELAY = 15   # seconds to wait before retrying after a timeout
CONCURRENCY = 3    # simultaneous pages
REQUEST_DELAY = 2  # seconds between each spec's first request


async def scrape_spec(browser, spec: dict, semaphore: asyncio.Semaphore) -> dict:
    label = f"{spec['spec']} {spec['class']}"

    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"Scraping {label} (attempt {attempt}/{MAX_RETRIES}) ...")
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            try:
                await page.goto(spec["url"], wait_until="load", timeout=90000)
                await page.wait_for_timeout(2000)
                try:
                    await page.wait_for_selector("#tab-bis-items-overall-bis table", timeout=15000)
                except Exception:
                    print(f"  WARNING: BIS table selector timed out for {label}, parsing what we have")
                html = await page.content()
                await page.close()

                items = parse_bis_table(html, label)
                print(f"  Done: {label} — {len(items)} items")
                return {
                    "class": spec["class"],
                    "spec": spec["spec"],
                    "role": spec["role"],
                    "url": spec["url"],
                    "bis_items": items,
                }

            except Exception as e:
                await page.close()
                if attempt < MAX_RETRIES:
                    print(f"  ERROR {label}: {e} — waiting {RETRY_DELAY}s before retry ...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    print(f"  FAILED {label} after {MAX_RETRIES} attempts: {e}")
                    return {
                        "class": spec["class"],
                        "spec": spec["spec"],
                        "role": spec["role"],
                        "url": spec["url"],
                        "bis_items": [],
                        "error": str(e),
                    }


async def main():
    out_path = "bis_data.json"
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Stagger task starts by REQUEST_DELAY so all 3 slots don't hit at once
        tasks = []
        for i, spec in enumerate(SPECS):
            await asyncio.sleep(REQUEST_DELAY if i > 0 else 0)
            tasks.append(asyncio.create_task(scrape_spec(browser, spec, semaphore)))

        results = await asyncio.gather(*tasks)
        await browser.close()

    # Preserve original SPECS order in output
    results = list(results)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total_items = sum(len(r["bis_items"]) for r in results)
    failed = [r for r in results if not r["bis_items"]]
    print(f"\nDone. Scraped {len(results)} specs, {total_items} total items.")
    if failed:
        print(f"  {len(failed)} spec(s) returned no items: {[f['spec']+' '+f['class'] for f in failed]}")
    print(f"Output: {out_path}")


asyncio.run(main())
