from __future__ import annotations

from src.application.markdown_content import normalize_document_content


class TestMarkdownContent:

    def test_normalize_markdown_removes_unsafe_html_and_renders_safe_html(self):
        raw = (
            "\ufeff# 标题\r\n\r\n"
            "正文  \r\n\r\n"
            "<script>alert('x')</script>\r\n"
            "<div onclick=\"alert(1)\">保留文本</div>"
        )

        result = normalize_document_content(raw, "markdown")

        assert result.raw_content == raw
        assert result.normalized_markdown == "# 标题\n\n正文\n\n保留文本"
        assert result.plain_text == "标题\n\n正文\n\n保留文本"
        assert "<h1>标题</h1>" in result.rendered_html
        assert "<p>正文</p>" in result.rendered_html
        assert "<p>保留文本</p>" in result.rendered_html
        assert "<script" not in result.rendered_html.lower()
        assert "onclick" not in result.rendered_html.lower()
        assert "alert" not in result.rendered_html.lower()

    def test_render_markdown_supports_lists_and_fenced_code_safely(self):
        raw = (
            "## 清单\n\n"
            "- Python\n"
            "- RAG\n\n"
            "```python\n"
            "print('<script>bad</script>')\n"
            "```"
        )

        result = normalize_document_content(raw, "md")

        assert "<h2>清单</h2>" in result.rendered_html
        assert "<ul>" in result.rendered_html
        assert "<li>Python</li>" in result.rendered_html
        assert "<pre><code" in result.rendered_html
        assert "&lt;script&gt;bad&lt;/script&gt;" in result.rendered_html
        assert "<script>bad</script>" not in result.rendered_html

    def test_plain_text_source_renders_as_preformatted_escaped_text(self):
        raw = "hello <b>world</b>\n<script>alert(1)</script>"

        result = normalize_document_content(raw, "txt")

        assert result.normalized_markdown == raw
        assert result.plain_text == raw
        assert result.rendered_html == (
            "<pre><code>hello &lt;b&gt;world&lt;/b&gt;\n"
            "&lt;script&gt;alert(1)&lt;/script&gt;</code></pre>"
        )

    def test_markdown_style_blocks_are_removed(self):
        raw = (
            "# 标题\n\n"
            "<style>\n"
            "  .danger { color: red; }\n"
            "</style>\n"
            "正文内容"
        )

        result = normalize_document_content(raw, "markdown")

        assert "style" not in result.normalized_markdown.lower()
        assert "danger" not in result.normalized_markdown
        assert result.plain_text == "标题\n\n正文内容"
        assert "<h1>标题</h1>" in result.rendered_html
        assert "<style>" not in result.rendered_html
