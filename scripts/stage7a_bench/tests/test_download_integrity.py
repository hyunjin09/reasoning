import pytest

from scripts.stage7a_bench.download_datasets import verify_content_hashes, safe_target


def test_standard_git_empty_blob_is_verified():
    verify_content_hashes(b'', {'git_blob_oid': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'})


def test_corrupt_release_payload_is_rejected():
    with pytest.raises(ValueError, match='SHA256'):
        verify_content_hashes(b'corrupted', {
            'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'})


def test_lfs_payload_uses_sha256_instead_of_pointer_blob():
    verify_content_hashes(b'', {
        'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        'git_blob_oid': 'this-is-the-pointer-not-the-payload'})


def test_manifest_cannot_escape_dataset_directory():
    with pytest.raises(ValueError, match='escape'):
        safe_target('/data/dataset/reasoning_steps_stage7a_bench/mathvision_wild', '../other/file')
