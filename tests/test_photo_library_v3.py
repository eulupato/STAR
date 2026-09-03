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



def test_photo_library_imports_images_without_removing_source(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = source_root / "foto.jpg"
    source.write_bytes(b"image")

    target = tmp_path / "album"
    library = PhotoLibrary(target)
    imported = library.import_images([source])

    assert source.exists()
    assert len(imported) == 1
    assert imported[0].parent == target
    assert imported[0].read_bytes() == b"image"


def test_photo_library_renames_collisions(tmp_path):
    first_root = tmp_path / "one"
    second_root = tmp_path / "two"
    first_root.mkdir()
    second_root.mkdir()
    first = first_root / "foto.jpg"
    second = second_root / "foto.jpg"
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    library = PhotoLibrary(tmp_path / "album")
    imported = library.import_images([first, second])

    assert [path.name for path in imported] == ["foto.jpg", "foto_2.jpg"]
    assert imported[0].read_bytes() == b"one"
    assert imported[1].read_bytes() == b"two"
