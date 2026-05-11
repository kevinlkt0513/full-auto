import browser_register


class _Locator:
    def __init__(self, text):
        self._text = text

    def inner_text(self, timeout=0):
        return self._text


class _Page:
    def __init__(self, url, body_text):
        self.url = url
        self._body_text = body_text

    def locator(self, selector):
        return _Locator(self._body_text)


def test_summarize_auth_error_page_detects_operation_timeout():
    page = _Page(
        "https://auth.openai.com/create-account",
        "Oops, an error occurred!\nOperation timed out\nTry again",
    )

    summary = browser_register._summarize_auth_error_page(page)

    assert "Operation timed out" in summary


def test_summarize_auth_error_page_ignores_non_auth_pages():
    page = _Page(
        "https://chatgpt.com/",
        "Oops, an error occurred! Operation timed out",
    )

    assert browser_register._summarize_auth_error_page(page) == ""


def test_summarize_auth_error_page_ignores_normal_auth_pages():
    page = _Page(
        "https://auth.openai.com/create-account",
        "Create your account Continue",
    )

    assert browser_register._summarize_auth_error_page(page) == ""
