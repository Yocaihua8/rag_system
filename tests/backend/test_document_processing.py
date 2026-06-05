import base64
import sys
import types
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.knowledge_island.api import dispatch
from backend.knowledge_island.document_processing import process_bytes
from backend.knowledge_island.storage import KnowledgeStore


def test_directory_import_extracts_docx_text(tmp_path: Path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_docx(project_dir / "notes.docx", ["项目背景", "支持 DOCX 正文抽取"])
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    documents = store.list_documents(project.id)

    assert response.status == 200
    assert response.body["result"]["imported"] == 1
    assert documents[0].relative_path == "notes.docx"
    assert "支持 DOCX 正文抽取" in documents[0].content


def test_upload_import_accepts_docx_base64_payload(tmp_path: Path):
    docx_path = tmp_path / "upload.docx"
    _write_docx(docx_path, ["浏览器文件夹导入", "二进制文档内容"])
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_name": "浏览器项目",
            "files": [
                {
                    "relative_path": "docs/upload.docx",
                    "content_base64": base64.b64encode(docx_path.read_bytes()).decode("ascii"),
                    "size": docx_path.stat().st_size,
                },
            ],
        },
    )
    document_id = response.body["documents"][0]["id"]
    preview = dispatch(store, "GET", f"/api/document?document_id={document_id}")

    assert response.status == 200
    assert response.body["result"]["created"] == 1
    assert preview.body["document"]["relative_path"] == "docs/upload.docx"
    assert "二进制文档内容" in preview.body["document"]["content"]


def test_pdf_import_is_skipped_with_explicit_reason_when_parser_is_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setitem(sys.modules, "pymupdf", None)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "manual.pdf").write_bytes(b"%PDF-1.4\n% minimal placeholder")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert response.status == 200
    assert response.body["result"]["imported"] == 0
    assert response.body["result"]["skipped"] == 1
    assert response.body["result"]["skipped_details"] == [
        {"path": "manual.pdf", "reason": "pdf extraction requires optional parser"}
    ]


def test_pdf_bytes_extract_text_when_pymupdf_is_available(monkeypatch):
    class FakePage:
        def __init__(self, text: str):
            self.text = text

        def get_text(self, _kind: str, sort: bool = False) -> str:
            assert sort is True
            return self.text

    class FakeDocument:
        def __enter__(self):
            return [FakePage("第一页内容"), FakePage("第二页内容")]

        def __exit__(self, *_args):
            return None

    fake_pymupdf = types.SimpleNamespace(open=lambda *args, **kwargs: FakeDocument())
    monkeypatch.setitem(sys.modules, "pymupdf", fake_pymupdf)

    processed = process_bytes("manual.pdf", b"%PDF-1.4")

    assert processed.is_importable
    assert processed.content == "第一页内容\n\n第二页内容"


def test_directory_import_persists_pdf_text_when_pymupdf_is_available(tmp_path: Path, monkeypatch):
    _install_fake_pymupdf(monkeypatch, ["PDF 项目背景", "PDF 正文片段"])
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "manual.pdf").write_bytes(b"%PDF-1.4")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    documents = store.list_documents(project.id)

    assert response.status == 200
    assert response.body["result"]["imported"] == 1
    assert documents[0].relative_path == "manual.pdf"
    assert "PDF 正文片段" in documents[0].content


def test_pdf_bytes_skip_when_parser_returns_no_text(monkeypatch):
    _install_fake_pymupdf(monkeypatch, ["", "   "])

    processed = process_bytes("manual.pdf", b"%PDF-1.4")

    assert not processed.is_importable
    assert processed.skipped_reason == "no extractable text"


def test_pdf_bytes_keep_explicit_skip_reason_when_pymupdf_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "pymupdf", None)

    processed = process_bytes("manual.pdf", b"%PDF-1.4")

    assert not processed.is_importable
    assert processed.skipped_reason == "pdf extraction requires optional parser"


def _install_fake_pymupdf(monkeypatch, page_texts: list[str]) -> None:
    class FakePage:
        def __init__(self, text: str):
            self.text = text

        def get_text(self, _kind: str, sort: bool = False) -> str:
            assert sort is True
            return self.text

    class FakeDocument:
        def __enter__(self):
            return [FakePage(text) for text in page_texts]

        def __exit__(self, *_args):
            return None

    fake_pymupdf = types.SimpleNamespace(open=lambda *args, **kwargs: FakeDocument())
    monkeypatch.setitem(sys.modules, "pymupdf", fake_pymupdf)


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    body = "".join(
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
        for text in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            "</Types>",
        )
        archive.writestr("word/document.xml", document_xml)
