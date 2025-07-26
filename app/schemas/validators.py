import re


def protection_against_xss(value: str) -> str:
    # Regex to detect any HTML tag: anything between < and >
    html_tag_pattern = re.compile(r'<[^>]+>', re.IGNORECASE)

    # Regex to detect javascript: or data: URIs
    js_uri_pattern = re.compile(r'javascript:', re.IGNORECASE)

    # Regex to detect event handlers like onclick=, onload= etc.
    event_handler_pattern = re.compile(r'on\w+\s*=', re.IGNORECASE)

    if html_tag_pattern.search(value):
        raise ValueError("HTML tags are not allowed.")
    if js_uri_pattern.search(value):
        raise ValueError("JavaScript URIs are not allowed.")
    if event_handler_pattern.search(value):
        raise ValueError("Event handlers are not allowed.")

    return value
