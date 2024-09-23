from __future__ import annotations

import traceback
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

from .processing.scrape_skills import (scrape_pdf_with_pymupdf,
                                       scrape_pdf_with_arxiv)

FILE_DIR = Path(__file__).parent.parent


class BrowserScraper:
    def __init__(self, url: str, session=None):
        self.url = url
        self.session = session
        self.browser_type = "chromium"
        self.headless = False
        self.user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/128.0.0.0 Safari/537.36")
        self.browser = None
        self.page = None
        self.use_browser_cookies = False

    async def scrape(self) -> str:
        if not self.url:
            print("URL not specified")
            return "A URL was not specified, cancelling request to browse website."

        try:
            await self.setup_browser()
            await self._visit_google_and_save_cookies()
            await self._add_header()

            text = await self.scrape_text_with_playwright()
            return text
        except Exception as e:
            print(f"An error occurred during scraping: {str(e)}")
            print("Full stack trace:")
            print(traceback.format_exc())
            return f"An error occurred: {str(e)}\n\nStack trace:\n{traceback.format_exc()}"
        finally:
            if self.browser:
                await self.browser.close()

    async def setup_browser(self) -> None:
        playwright = await async_playwright().start()
        browser_types = {
            "chromium": playwright.chromium,
            "firefox": playwright.firefox,
            "webkit": playwright.webkit
        }

        browser_launch = browser_types.get(self.browser_type, playwright.chromium)
        self.browser = await browser_launch.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        await self.page.set_extra_http_headers({"User-Agent": self.user_agent})

    async def _visit_google_and_save_cookies(self):
        try:
            await self.page.goto("https://www.google.com")
            await self.page.wait_for_timeout(2000)  # Wait for 2 seconds
        except Exception as e:
            print(f"Failed to visit Google: {str(e)}")
            print("Full stack trace:")
            print(traceback.format_exc())

    async def _add_header(self) -> None:
        with open(f"{FILE_DIR}/browser/js/overlay.js", "r") as file:
            js_code = file.read()
        await self.page.evaluate(js_code)

    async def scrape_text_with_playwright(self) -> str:
        await self.page.goto(self.url)
        await self.page.wait_for_load_state("networkidle")

        await self._scroll_to_bottom()

        if self.url.endswith(".pdf"):
            text = scrape_pdf_with_pymupdf(self.url)
        elif "arxiv" in self.url:
            doc_num = self.url.split("/")[-1]
            text = scrape_pdf_with_arxiv(doc_num)
        else:
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, "html.parser")

            for script in soup(["script", "style"]):
                script.extract()

            text = self.get_text(soup)

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text

    def get_text(self, soup: BeautifulSoup) -> str:
        """Get the relevant text from the soup with improved filtering"""
        text_elements = []
        tags = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]

        for element in soup.find_all(tags):
            # Skip empty elements
            if not element.text.strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(element.text.split()) < 3:
                continue

            # Check if the element is likely to be navigation or a menu
            parent_classes = element.parent.get('class', [])
            if any(cls in ['nav', 'menu', 'sidebar', 'footer'] for cls in parent_classes):
                continue

            # Remove excess whitespace and join lines
            cleaned_text = ' '.join(element.text.split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return '\n\n'.join(text_elements)

    async def _scroll_to_bottom(self):
        last_height = await self.page.evaluate("document.body.scrollHeight")
        while True:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(2000)  # Wait for 2 seconds
            new_height = await self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    async def _scroll_to_percentage(self, ratio: float) -> None:
        if ratio < 0 or ratio > 1:
            raise ValueError("Percentage should be between 0 and 1")
        await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")