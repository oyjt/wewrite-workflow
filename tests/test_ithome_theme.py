from pathlib import Path

from bs4 import BeautifulSoup

from wewrite.commands.validate_html import validate_html
from wewrite.toolkit.converter import WeChatConverter, make_paste_safe
from wewrite.toolkit.theme import load_theme


def test_ithome_news_theme():
    theme = load_theme("ithome", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        "# 科技早报\n\n### 早报速览\n\n- 新模型上线\n\n"
        "## 新模型正式发布\n\n**厂商**公布新模型。\n\n> **开放条件**仍需确认。"
    )
    soup = BeautifulSoup(result.html, "html.parser")
    assert "#d22222" in soup.h1["style"]
    assert "#d22222" in soup.h3["style"]
    assert "#222" in soup.h2["style"]
    assert soup.h2.get_text() == "新模型正式发布"
    assert "linear-gradient(#d22222, #d22222)" in soup.h2["style"]
    assert "background-size: 3px 16px" in soup.h2["style"]
    assert "background: #f5f5f5" in soup.blockquote["style"]
    assert "border-left: 3px solid #ddd" in soup.blockquote["style"]
    assert "padding: 14px 16px" in soup.blockquote["style"]
    assert "#d22222" not in soup.blockquote["style"]
    assert soup.blockquote.strong.get_text() == "开放条件"
    assert "#ffffff" in soup.section["style"]
    assert "辅助创作" not in result.html
    assert not [item for item in validate_html(make_paste_safe(result.html)) if item["level"] == "ERROR"]
