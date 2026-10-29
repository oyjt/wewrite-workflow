from bs4 import BeautifulSoup
from pathlib import Path
import pytest

from wewrite.commands.validate_html import validate_html
from wewrite.toolkit.converter import WeChatConverter, make_paste_safe
from wewrite.toolkit.theme import load_theme


def test_juya_theme_wechat_output():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        "# 资讯标题\n\n开场内容。\n\n## 热点速读\n\n正文与 **重点**。\n\n"
        "> 补充说明\n\n- 第一项\n- 第二项\n\n`token`\n\n"
        "| 项目 | 说明 |\n| --- | --- |\n| 模型 | 测试 |"
    )
    soup = BeautifulSoup(result.html, "html.parser")
    assert soup.h1.get_text() == "资讯标题"
    assert "#faf9f5" in soup.section["style"]
    assert "#f0eee6" in soup.h2["style"]
    assert "border-radius: 12px" in soup.h2["style"]
    assert "border-radius: 24px" in soup.blockquote["style"]
    assert "background: #fff" in soup.blockquote["style"]
    assert "padding: 0" in soup.blockquote["style"]
    assert "background: #fff" in soup.blockquote.p["style"]
    assert "isolation: isolate" in soup.blockquote.p["style"]
    assert "padding: 12px 16px" in soup.blockquote.p["style"]
    assert "overflow: hidden" in soup.blockquote["style"]
    assert "辅助创作" not in result.html
    assert not [issue for issue in validate_html(make_paste_safe(result.html)) if issue["level"] == "ERROR"]


@pytest.mark.parametrize("extension", ["png", "gif"])
@pytest.mark.parametrize("count", [1, 2, 4])
def test_gallery_keeps_images_and_counts_hint(count, extension):
    markdown = ":::gallery\n" + "\n".join(f"![图{i}](images/{i}.{extension})" for i in range(count)) + "\n:::"
    result = WeChatConverter(theme_name="professional-clean").convert(markdown)
    soup = BeautifulSoup(make_paste_safe(result.html), "html.parser")
    assert result.images == [f"images/{i}.{extension}" for i in range(count)]
    assert len(soup.find_all("img")) == count
    if count > 1:
        assert f"左右滑动查看 · 共 {count} 张" in soup.get_text()
        assert "overflow-x: scroll" in result.html
        assert all("display: inline-block" in img["style"] for img in soup.find_all("img"))
        track = soup.find("img").parent
        assert [child.name for child in track.children if child.name] == ["img"] * count
    else:
        assert "左右滑动查看" not in soup.get_text()
    assert not [issue for issue in validate_html(str(soup)) if issue["level"] == "ERROR"]


@pytest.mark.parametrize("content", ["没有图片", "![不安全](javascript:alert)", "![不安全](data:image/svg+xml,svg)"])
def test_gallery_rejects_missing_or_unsafe_images(content):
    with pytest.raises(ValueError):
        WeChatConverter().convert(":::gallery\n" + content + "\n:::")


def test_image_spacing_does_not_stack_paragraph_and_image_margins():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        "> 摘要内容。\n\n![产品图](image.jpg)\n\n*图片说明*\n\n正文中的 ![小图](inline.png) 继续阅读。"
    )
    soup = BeautifulSoup(result.html, "html.parser")
    image = soup.find("img")
    assert "margin: 12px auto 6px" in image["style"]
    assert "margin: 0" in image.parent["style"]
    assert "padding: 0" in image.parent["style"]
    assert "margin: 12px 0" in soup.blockquote["style"]
    assert "line-height: 0" not in soup.find_all("img")[1].parent["style"]
