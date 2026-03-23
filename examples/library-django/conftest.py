import pytest
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode


class HTMLSnapshotExtension(SingleFileSnapshotExtension):
    _write_mode = WriteMode.TEXT
    file_extension = "html"


@pytest.fixture()
def snapshot(snapshot):
    return snapshot.use_extension(HTMLSnapshotExtension)
