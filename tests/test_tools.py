from pathlib import Path
import pytest
from crystal_agent.tools import FolderTools

def test_reads_only_inside_allowed_folder(tmp_path):
    root = tmp_path / "allowed"; root.mkdir()
    f = root / "notes.md"; f.write_text("hello local agent", encoding="utf-8")
    outside = tmp_path / "outside.md"; outside.write_text("secret", encoding="utf-8")
    tools = FolderTools([str(root)])
    assert "hello local agent" in tools.read_file(str(f))
    with pytest.raises(PermissionError): tools.read_file(str(outside))

def test_rejects_binary_and_large_files(tmp_path):
    root = tmp_path / "allowed"; root.mkdir()
    image = root / "image.png"; image.write_bytes(b"not actually png")
    with pytest.raises(ValueError): FolderTools([str(root)]).read_file(str(image))
    huge = root / "large.txt"; huge.write_text("x" * 200)
    with pytest.raises(ValueError): FolderTools([str(root)], max_file_mb=0).read_file(str(huge))

def test_lists_only_selected_folder(tmp_path):
    root = tmp_path / "allowed"; root.mkdir(); (root / "notes.txt").write_text("hi")
    output = FolderTools([str(root)]).list_files()
    assert "notes.txt" in output
