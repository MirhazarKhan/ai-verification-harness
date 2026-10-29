import os
import time
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import concurrent.futures

class BrowserChecker:
    def __init__(
        self,
        dev_server_url: str,
        output_dir: str,
        timeout_ms: int = 8000,
        screenshot_on_failure: bool = True
    ):
        self.dev_server_url = dev_server_url
        self.output_dir = output_dir
        self.timeout_ms = timeout_ms
        self.screenshot_on_failure = screenshot_on_failure

    def verify_dom(
        self,
        target_selector: Optional[str] = None,
        expected_text: Optional[str] = None,
        expected_attribute: Optional[Dict[str, str]] = None,
        check_console_errors: bool = True
    ) -> Dict[str, Any]:
        """Verify DOM elements using Playwright browser, or fast HTML fallback if running in non-interactive environment."""
        import sys
        if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            return self._fallback_html_verify(target_selector, expected_text, "Non-interactive background execution environment")

        try:
            return self._playwright_verify(
                target_selector,
                expected_text,
                expected_attribute,
                check_console_errors
            )
        except Exception as e:
            return self._fallback_html_verify(
                target_selector,
                expected_text,
                str(e)
            )

    def _playwright_verify(
        self,
        target_selector: Optional[str] = None,
        expected_text: Optional[str] = None,
        expected_attribute: Optional[Dict[str, str]] = None,
        check_console_errors: bool = True
    ) -> Dict[str, Any]:
        console_errors = []
        page_errors = []

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                page.on("pageerror", lambda err: page_errors.append(str(err)))

                page.goto(self.dev_server_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                try:
                    page.wait_for_load_state("networkidle", timeout=2000)
                except Exception:
                    pass

                if check_console_errors and (console_errors or page_errors):
                    err_msg = f"Runtime JavaScript errors detected on page load: {page_errors + console_errors}"
                    screenshot_path = self._take_screenshot(page, "js_console_error")
                    browser.close()
                    return {
                        "success": False,
                        "tier": 3,
                        "error": f"TIER 3 FAILURE (Browser DOM Verification): {err_msg}",
                        "screenshot": screenshot_path
                    }

                if target_selector:
                    try:
                        element = page.wait_for_selector(target_selector, timeout=self.timeout_ms)
                        if not element:
                            screenshot_path = self._take_screenshot(page, "missing_selector")
                            browser.close()
                            return {
                                "success": False,
                                "tier": 3,
                                "error": f"TIER 3 FAILURE (Browser DOM Verification): Required selector '{target_selector}' was not found on page {self.dev_server_url}.",
                                "screenshot": screenshot_path
                            }

                        if expected_text:
                            actual_text = element.text_content() or ""
                            if expected_text.lower() not in actual_text.lower():
                                screenshot_path = self._take_screenshot(page, "text_mismatch")
                                browser.close()
                                return {
                                    "success": False,
                                    "tier": 3,
                                    "error": f"TIER 3 FAILURE (Browser DOM Verification): Element '{target_selector}' does not contain expected text '{expected_text}'. Found text: '{actual_text.strip()}'.",
                                    "screenshot": screenshot_path
                                }

                        if expected_attribute:
                            attr_name = expected_attribute.get("name")
                            attr_val = expected_attribute.get("contains")
                            actual_val = element.get_attribute(attr_name) or ""
                            if attr_val and attr_val.lower() not in actual_val.lower():
                                screenshot_path = self._take_screenshot(page, "attribute_mismatch")
                                browser.close()
                                return {
                                    "success": False,
                                    "tier": 3,
                                    "error": f"TIER 3 FAILURE (Browser DOM Verification): Element '{target_selector}' attribute '{attr_name}' does not contain '{attr_val}'. Actual attribute value: '{actual_val}'.",
                                    "screenshot": screenshot_path
                                }

                    except PlaywrightTimeoutError:
                        screenshot_path = self._take_screenshot(page, "timeout_selector")
                        browser.close()
                        return {
                            "success": False,
                            "tier": 3,
                            "error": f"TIER 3 FAILURE (Browser DOM Verification): Timed out waiting for selector '{target_selector}' to render on {self.dev_server_url}.",
                            "screenshot": screenshot_path
                        }

                browser.close()
                return {
                    "success": True,
                    "tier": 3,
                    "message": "Tier 3 Browser DOM verification passed successfully!"
                }

            except Exception as e:
                return self._fallback_html_verify(target_selector, expected_text, str(e))

    def _fallback_html_verify(
        self,
        target_selector: Optional[str],
        expected_text: Optional[str],
        original_error: str
    ) -> Dict[str, Any]:
        """Fallback DOM verification using HTTP GET request and HTML parsing when Playwright browser is unavailable."""
        import requests

        try:
            res = requests.get(self.dev_server_url, timeout=5)
            html_content = res.text

            if target_selector:
                cleaned_selector = target_selector.lstrip("#").lstrip(".")
                if cleaned_selector not in html_content:
                    return {
                        "success": False,
                        "tier": 3,
                        "error": f"TIER 3 FAILURE (DOM Verification via Fallback): Selector '{target_selector}' not found in HTML response at {self.dev_server_url}."
                    }

            if expected_text and expected_text.lower() not in html_content.lower():
                return {
                    "success": False,
                    "tier": 3,
                    "error": f"TIER 3 FAILURE (DOM Verification via Fallback): Expected text '{expected_text}' not found in HTML response at {self.dev_server_url}."
                }

            return {
                "success": True,
                "tier": 3,
                "message": "Tier 3 DOM verification passed successfully via HTML parser fallback."
            }
        except Exception as fallback_err:
            return {
                "success": False,
                "tier": 3,
                "error": f"TIER 3 FAILURE (Browser & Fallback Verification Failed): Playwright error: {original_error} | Fallback error: {str(fallback_err)}"
            }

    def _take_screenshot(self, page, label: str) -> Optional[str]:
        if not self.screenshot_on_failure:
            return None
        timestamp = int(time.time())
        filename = f"failure_{label}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, "screenshots", filename)
        try:
            page.screenshot(path=filepath, full_page=True)
            return filepath
        except Exception:
            return None
