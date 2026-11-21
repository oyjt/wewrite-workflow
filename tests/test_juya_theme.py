from bs4 import BeautifulSoup
from pathlib import Path
import pytest

from wewrite.commands.validate_html import validate_html
from wewrite.toolkit.converter import WeChatConverter, make_paste_safe, preview_html
from wewrite.toolkit.theme import load_theme


def test_juya_theme_wechat_output():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        "# 资讯标题\n\n开场内容。\n\n## 热点速读\n\n正文与 **重点**。\n\n"
        "> **补充说明**与 `Fable 5.2`。\n\n- 第一项\n- 第二项\n\n`token`\n\n"
        "| 项目 | 说明 |\n| --- | --- |\n| 模型 | 测试 |"
    )
    soup = BeautifulSoup(result.html, "html.parser")
    assert soup.h1.get_text() == "资讯标题"
    assert "background" not in soup.section["style"]
    assert "background: rgba(" in soup.h2["style"]
    assert "font-size: 17px" in soup.h2["style"]
    assert "border-radius: 12px" in soup.h2["style"]
    assert soup.blockquote is None
    card = soup.find("strong", string="补充说明").find_parent("section")
    assert "background: rgba(" in card["style"]
    assert "border: 1px solid rgba(" in card["style"]
    assert "border-radius: 24px" in card["style"]
    assert "padding: 0" in card["style"]
    assert "overflow: hidden" in card["style"]
    assert "background: transparent" in card.p["style"]
    assert "isolation: isolate" in card.p["style"]
    assert "padding: 12px 16px" in card.p["style"]
    assert card.p.code.get_text() == "Fable 5.2"
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
    assert "width: 100%" in image["style"].split("; ")
    assert "margin: 0" in image.parent["style"]
    assert "padding: 0" in image.parent["style"]
    caption = image.parent.find_next_sibling()
    assert caption.get_text() == "图片说明"
    assert "font-size: 13px" in caption["style"]
    assert "line-height: 1.6" in caption["style"]
    assert "width: fit-content" in caption["style"]
    assert "margin: 0 auto 14px" in caption["style"]
    assert "text-align: left" in caption["style"]
    card = soup.find("p", string="摘要内容。").parent
    assert "margin: 12px 0" in card["style"]
    assert "line-height: 0" not in soup.find_all("img")[1].parent["style"]


def test_juya_gallery_caption_and_reference_list_survive_paste():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        ":::gallery\n![提示图](limits.png)\n![动图](demo.gif)\n:::\n\n"
        "_图片来自**官方公告**。_\n\n"
        "对照[公告](https://example.com/release)与[说明](https://example.com/help)。\n\n"
        "### 参考链接\n\n- [正式公告](https://example.com/release)\n"
        "- [重复地址](https://example.com/release)\n\n觉得有用，欢迎收藏。"
    )
    soup = BeautifulSoup(make_paste_safe(result.html), "html.parser")
    track = soup.img.parent
    assert [el.name for el in track.find_all(recursive=False)] == ["img", "img"]
    caption = track.find_previous_sibling()
    assert caption.get_text() == "图片来自官方公告。 · 横滑看 2 张"
    assert "margin: 0 0 6px" in caption["style"]
    assert "text-align: left" in caption["style"]
    assert "fit-content" not in caption["style"]
    assert "font-size: 13px" in caption["style"]
    assert caption.strong.get_text() == "官方公告"
    assert "对照公告" in track.parent.find_next_sibling().get_text()
    assert soup.get_text().count("参考链接") == 1
    assert soup.ul.parent.find_previous_sibling().get_text() == "觉得有用，欢迎收藏。"
    assert [item.get_text() for item in soup.ul.find_all("li")] == [
        "[1] 正式公告 https://example.com/release",
        "[2] 说明 https://example.com/help",
    ]
    names = soup.ul.select('span[style*="font-weight: 600"]')
    assert [name.get_text() for name in names] == ["正式公告", "说明"]
    assert all("https://" not in name.get_text() for name in names)
    items = soup.ul.find_all("li")
    for item in [soup.ul.find_previous_sibling("p"), *items]:
        assert "text-align: left" in item["style"]
        assert "text-align-last: left" in item["style"]
        assert "letter-spacing: normal" in item["style"]
    for item in items:
        url = item.select_one('span[style*="display: block"]')
        assert url.get_text().startswith("https://")
        assert "font-weight: 400" in url["style"]
    assert not [issue for issue in validate_html(str(soup)) if issue["level"] == "ERROR"]


def test_juya_gallery_optional_short_title_moves_with_its_image():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        ':::gallery\n![评测图的完整替代文字](bench.png "评测对比")\n'
        '![盲测过程](blind.gif "用户盲测")\n![补充图](other.png)\n:::\n\n*腾讯公告配图*'
    )
    soup = BeautifulSoup(make_paste_safe(result.html), "html.parser")
    track = soup.img.parent.parent
    assert "overflow-x: scroll" in track["style"]
    slides = track.find_all("section", recursive=False)
    assert all("display: inline-block" in slide["style"] for slide in slides)
    assert [slide.img["src"] for slide in slides] == ["bench.png", "blind.gif", "other.png"]
    assert slides[0].img["alt"] == "评测图的完整替代文字"
    assert [p.get_text() for p in track.find_all("p")] == ["评测对比", "用户盲测"]
    assert all("line-height: 1.6" in p["style"] for p in track.find_all("p"))
    assert track.find_previous_sibling("p").get_text() == "腾讯公告配图 · 横滑看 3 张"
    assert not [issue for issue in validate_html(str(soup)) if issue["level"] == "ERROR"]


def test_juya_compacts_only_news_overview_and_keeps_short_model_names_together():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    result = WeChatConverter(theme=theme).convert(
        "**今日资讯概览**\n\n- 发布 `Qwen4-Max`。\n- 推出 `Hy4 flash`。\n\n"
        "## 用法\n\n- 运行 `long-command --with-a-long-option`。\n\n"
        "```text\nQwen4-Max\n```"
    )
    soup = BeautifulSoup(result.html, "html.parser")
    overview = soup.p.find_next_sibling()
    assert "padding: 0" in soup.p["style"]
    assert all("margin-bottom: 4px" in item["style"] for item in overview.find_all("section", recursive=False))
    assert all("white-space: nowrap" in code["style"] for code in overview.select("code"))
    ordinary = soup.h2.find_next_sibling()
    assert "margin-bottom: 8px" in ordinary.section["style"]
    assert "nowrap" not in ordinary.code["style"]
    assert "nowrap" not in soup.pre.code["style"]


def test_juya_dark_preview_styles_cards_and_small_text_without_fixing_article_background():
    theme = load_theme("juya-ai", themes_dir=str(Path(__file__).parents[1] / "src/wewrite/toolkit/themes"))
    raw = WeChatConverter(theme=theme).convert(
        "## 标题\n\n> 摘要和 `Qwen4-Max`。\n\n![图](chart.png)\n\n*图注*\n\n"
        "### 参考链接\n\n- [来源](https://example.com)"
    ).html
    soup = BeautifulSoup(raw, "html.parser")
    assert "background" not in soup.section["style"] and "color:" not in soup.section["style"]
    assert soup.h2["data-darkmode-bgcolor"] == "#282623"
    card = soup.code.find_parent("section")
    assert card["data-darkmode-bgcolor"] == "#282623"
    assert card.p["data-darkmode-color"] == "#e7e4de"
    assert soup.code["data-darkmode-bgcolor"] == "#30281f"
    assert soup.code["data-darkmode-color"] == "#efad7c"
    assert soup.img.parent.find_next_sibling()["data-darkmode-color"] == "#b6b1a7"
    assert [(span.get_text(), span["data-darkmode-color"]) for span in soup.ul.li.find_all("span")] == [
        ("来源", "#b6b1a7"), ("https://example.com", "#a7a39b"),
    ]
    assert all(not key.startswith("data-darkmode") for key in soup.img.attrs)
    assert not validate_html(raw)
    preview = BeautifulSoup(preview_html(make_paste_safe(raw), theme), "html.parser")
    assert "@media (prefers-color-scheme: dark)" in preview.head.style.text
    assert 'body { color-scheme: dark; background: #191919;' in preview.head.style.text
    assert '#a7a39b !important' in preview.head.style.text
