import base64
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from webapp.api import dispatch
from webapp.storage import KnowledgeStore


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


def test_pdf_import_is_skipped_with_explicit_reason(tmp_path: Path):
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
