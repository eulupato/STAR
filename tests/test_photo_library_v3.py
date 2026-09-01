from core.photo_library import PhotoLibrary


def test_photo_library_only_lists_supported_nonempty_images(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"image")
    (tmp_path / "b.png").write_bytes(b"image")
    (tmp_path / "empty.webp").write_bytes(b"")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")

    images = PhotoLibrary(tmp_path).list_images()

    assert {path.name for path in images} == {"a.jpg", "b.png"}


def test_photo_library_is_bounded(tmp_path):
    for index in range(5):
        (tmp_path / f"{index}.jpg").write_bytes(b"image")

    assert len(PhotoLibrary(tmp_path).list_images(limit=2)) == 2


def test_photo_library_missing_folder_is_empty(tmp_path):
    library = PhotoLibrary(tmp_path / "missing")
    assert library.list_images() == []
