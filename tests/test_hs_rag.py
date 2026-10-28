"""Offline-Tests für Persistenz, Updates, abgebrochene Importe und RAG-Grenzen."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from hs_rag import (IndexErrorBase, VectorIndex, answer_question, build_index,
                    embedding_text, index_plan, index_status, read_chunks)


class FakeEmbeddings:
    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        return [[1.0, 0.01, 0.01] if 'informatik' in t.casefold()
                else [0.01, 1.0, 0.01] if 'sozial' in t.casefold()
                else [0.01, 0.01, 1.0] for t in texts]


def chunk(identifier, text, **extra):
    return {'id': identifier, 'text': text, 'file': identifier + '.md',
            'document_title': identifier, 'heading': 'Studieninhalte',
            'source_urls': ['https://www.hs-osnabrueck.de/'],
            'studiengang': identifier, 'abschluss': 'B.Sc.', 'campus': 'Osnabrück',
            'status': 'im Verzeichnis', 'retrieved_at': '2026-10-28', **extra}


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'chunks.jsonl'
        self.db = self.root / 'index.sqlite3'
        self.chunks = [chunk('informatik', 'Informatik und Datenbanken'),
                       chunk('soziales', 'Soziale Arbeit und Kinderhilfe', campus='Lingen')]
        self.fake = FakeEmbeddings()
        self.write()

    def write(self, chunks=None):
        data = self.chunks if chunks is None else chunks
        self.source.write_text(''.join(json.dumps(c) + '\n' for c in data), encoding='utf-8')

    def build(self, **options):
        return build_index(self.source, self.db, embedder=self.fake, **options)

    def test_plan_has_no_network_or_write_side_effects(self):
        plan = index_plan(self.source, self.db)
        self.assertEqual(plan['new_embeddings'], 2)
        self.assertFalse(self.db.exists())

    def test_duplicate_ids_are_rejected_before_creating_database(self):
        self.write([self.chunks[0], self.chunks[0]])
        with self.assertRaises(IndexErrorBase):
            self.build()
        self.assertFalse(self.db.exists())
        self.assertFalse(self.fake.calls)

    def test_missing_sources_are_rejected(self):
        data = deepcopy(self.chunks)
        data[0]['source_urls'] = []
        self.write(data)
        with self.assertRaises(IndexErrorBase):
            read_chunks(self.source)

    def test_vectors_survive_restart_and_only_query_is_embedded(self):
        self.build()
        query_fake = FakeEmbeddings()
        index = VectorIndex(self.db, embedder=query_fake)
        self.assertEqual(index.search('Informatik', top_k=1)[0].chunk['id'], 'informatik')
        self.assertEqual(query_fake.calls, [['Informatik']])
        index.search('Informatik')
        self.assertEqual(len(query_fake.calls), 1)

    def test_unchanged_import_reuses_all_embeddings(self):
        self.build()
        self.fake.calls.clear()
        result = self.build()
        self.assertEqual(result['embedded_now'], 0)
        self.assertEqual(result['reused_embeddings'], 2)
        self.assertFalse(self.fake.calls)

    def test_metadata_change_updates_without_reembedding(self):
        self.build()
        self.chunks[0]['source_urls'] = ['https://www.hs-osnabrueck.de/studium/']
        self.write()
        self.assertTrue(index_status(self.db, self.source)['source_changed'])
        self.fake.calls.clear()
        self.build()
        index = VectorIndex(self.db, embedder=self.fake)
        self.assertEqual(index.search('Informatik', top_k=1)[0].chunk['source_urls'],
                         self.chunks[0]['source_urls'])
        self.assertFalse(index_status(self.db, self.source)['source_changed'])
        self.assertEqual(len(self.fake.calls), 1)  # query only

    def test_changed_text_only_embeds_the_changed_chunk(self):
        self.build()
        self.chunks[0]['text'] += ' und Programmierung'
        self.write()
        self.fake.calls.clear()
        result = self.build()
        self.assertEqual(result['embedded_now'], 1)
        self.assertEqual(sum(map(len, self.fake.calls)), 1)

    def test_removed_documents_disappear_from_active_index(self):
        self.build()
        self.write(self.chunks[:1])
        self.build()
        index = VectorIndex(self.db, embedder=self.fake)
        self.assertEqual([c['id'] for c in index.chunks], ['informatik'])
        self.assertEqual(index.search('Soziale Arbeit'), [])

    def test_failed_update_keeps_previous_collection_and_resumes(self):
        self.build()
        for c in self.chunks:
            c['text'] += ' neuer Text'
        self.write()
        calls = []

        def fail_second(texts):
            calls.append(texts)
            if len(calls) == 2:
                raise RuntimeError('simulated interruption')
            return self.fake(texts)

        with self.assertRaises(RuntimeError):
            build_index(self.source, self.db, batch_size=1, embedder=fail_second)
        index = VectorIndex(self.db, embedder=self.fake)
        self.assertTrue(all('neuer Text' not in c['text'] for c in index.chunks))
        self.assertTrue(index_status(self.db, self.source)['ready'])
        self.assertEqual(index_plan(self.source, self.db)['new_embeddings'], 1)
        result = self.build()
        self.assertEqual(result['embedded_now'], 1)
        self.assertTrue(all('neuer Text' in c['text'] for c in VectorIndex(self.db).chunks))

    def test_failed_first_import_is_not_a_ready_database(self):
        with self.assertRaises(IndexErrorBase):
            build_index(self.source, self.db, embedder=lambda texts: [[float('nan')]] * len(texts))
        self.assertFalse(index_status(self.db, self.source)['ready'])
        with self.assertRaises(IndexErrorBase):
            VectorIndex(self.db)

    def test_model_change_cannot_reuse_vectors_from_other_model(self):
        self.build(model='model-one')
        self.assertEqual(index_plan(self.source, self.db, 'model-two')['new_embeddings'], 2)
        self.build(model='model-two')
        self.assertEqual(VectorIndex(self.db).info['model'], 'model-two')

    def test_inconsistent_dimensions_never_publish_partial_collection(self):
        with self.assertRaises(IndexErrorBase):
            build_index(self.source, self.db, embedder=lambda texts: [[1, 0], [1, 0, 0]])
        self.assertFalse(index_status(self.db, self.source)['ready'])

    def test_empty_corpus_cannot_clear_existing_collection(self):
        self.build()
        self.write([])
        with self.assertRaises(IndexErrorBase):
            self.build()
        self.assertEqual(len(VectorIndex(self.db).chunks), 2)

    def test_filters_and_archived_programmes(self):
        self.chunks[1]['status'] = 'auslaufend'
        self.write()
        self.build()
        index = VectorIndex(self.db, embedder=self.fake)
        self.assertEqual(index.search('Soziale Arbeit'), [])
        self.assertEqual(len(index.search('Soziale Arbeit', include_archived=True, campus='Lingen')), 1)
        self.assertEqual(index.search('Informatik', campus='Lingen'), [])

    def test_missing_evidence_does_not_call_language_model(self):
        self.build()
        index = VectorIndex(self.db, embedder=self.fake)

        def forbidden(*args, **kwargs):
            self.fail('No generator call is allowed without evidence')

        result = answer_question('Astronomie', index, generator=forbidden)
        self.assertFalse(result['grounded'])
        self.assertEqual(result['sources'], [])

    def test_answer_preserves_sources_and_context(self):
        self.build()
        index = VectorIndex(self.db, embedder=self.fake)
        calls = []

        def generator(prompt, **kwargs):
            calls.append((prompt, kwargs))
            return 'Datenbanken gehören zu Informatik [1].'

        result = answer_question('Informatik', index, generator=generator)
        self.assertTrue(result['grounded'])
        self.assertEqual(result['sources'][0]['urls'], self.chunks[0]['source_urls'])
        self.assertIn('QUELLEN BEGINN', calls[0][0])
        self.assertIn('keine URLs', calls[0][1]['system'])

    def test_embedding_preparation_keeps_labels_and_source_document_unchanged(self):
        text = '[Informatik](https://www.hs-osnabrueck.de/) am Westerberg'
        self.assertEqual(embedding_text(text), 'Informatik am Westerberg')
        self.assertIn('https://', text)


if __name__ == '__main__':
    unittest.main()
