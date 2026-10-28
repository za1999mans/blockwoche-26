from pathlib import Path
import json
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from hs_index_bundle import ensure_index, export_index, manifest_path
from hs_rag import ROOT, IndexErrorBase, VectorIndex, build_index, database_path, index_status
from test_hs_rag import FakeEmbeddings, chunk


class IndexBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'chunks.jsonl'
        self.db = self.root/'local.sqlite3'
        self.remote = self.root/'cloud/data/index.sqlite3'
        self.bundle = self.root/'deployment/vector_index.sqlite3.gz'
        self.chunks = [chunk('informatik', 'Informatik und Datenbanken'),
                       chunk('soziales', 'Soziale Arbeit')]
        self.write_chunks()
        build_index(self.source, self.db, embedder=FakeEmbeddings())

    def write_chunks(self):
        self.source.write_text(''.join(json.dumps(c)+'\n' for c in self.chunks))

    def export(self):
        return export_index(self.db, self.bundle, self.source)

    def restore(self):
        return ensure_index(self.remote, self.bundle, self.source)

    def test_fresh_cloud_restore_requires_no_embedding_calls(self):
        self.export()
        with patch('hs_rag.OpenAIEmbeddings.__call__', side_effect=AssertionError('No API during startup')):
            status = self.restore()
        self.assertTrue(status['ready'])
        self.assertEqual(status['chunks'], 2)
        self.assertFalse(status['source_changed'])
        restored = VectorIndex(self.remote, embedder=FakeEmbeddings())
        self.assertEqual(restored.search('Informatik', top_k=1)[0].chunk['id'], 'informatik')
        self.assertEqual(restored.info['source_path'], 'HS_DATA/_rag/chunks.jsonl')
        self.assertNotIn(str(self.root), self.remote.read_bytes().decode('latin-1'))

    def test_existing_database_is_not_overwritten(self):
        self.export()
        self.restore()
        before = self.remote.stat().st_mtime_ns
        self.assertTrue(self.restore()['ready'])
        self.assertEqual(before, self.remote.stat().st_mtime_ns)

    def test_missing_bundle_returns_not_ready_without_creating_database(self):
        self.assertFalse(self.restore()['ready'])
        self.assertFalse(self.remote.exists())

    def test_corrupt_compressed_file_is_not_installed(self):
        self.export()
        self.bundle.write_bytes(b'broken')
        with self.assertRaises(IndexErrorBase):
            self.restore()
        self.assertFalse(self.remote.exists())

    def test_wrong_database_checksum_never_leaves_partial_database(self):
        self.export()
        manifest = manifest_path(self.bundle)
        description = json.loads(manifest.read_text())
        description['database_sha256'] = '0' * 64
        manifest.write_text(json.dumps(description))
        with self.assertRaises(IndexErrorBase):
            self.restore()
        self.assertFalse(self.remote.exists())
        self.assertFalse(list(self.remote.parent.glob('*.tmp')))

    def test_bundle_for_different_chunks_is_rejected(self):
        self.export()
        self.chunks[0]['text'] += ' geändert'
        self.write_chunks()
        with self.assertRaises(IndexErrorBase):
            self.restore()
        self.assertFalse(self.remote.exists())

    def test_export_of_stale_index_is_rejected(self):
        self.chunks[0]['text'] += ' geändert'
        self.write_chunks()
        with self.assertRaises(IndexErrorBase):
            self.export()
        self.assertFalse(self.bundle.exists())

    def test_only_active_vectors_are_packaged(self):
        self.chunks[0]['text'] += ' neuer Inhalt'
        self.write_chunks()
        build_index(self.source, self.db, embedder=FakeEmbeddings())
        self.assertEqual(index_status(self.db, self.source)['cached_vectors'], 3)
        self.export()
        self.assertEqual(self.restore()['cached_vectors'], 2)

    def test_relative_configuration_is_resolved_against_project_root(self):
        original = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ, {'HS_RAG_DB': 'data/relative.sqlite3'}):
                self.assertEqual(database_path(), ROOT/'data/relative.sqlite3')
        finally:
            os.chdir(original)


if __name__ == '__main__':
    unittest.main()
