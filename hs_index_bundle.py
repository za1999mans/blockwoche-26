"""Portables Deployment-Paket für den bereits berechneten Hochschulindex.

Export und Wiederherstellung laufen vollständig offline. Die Laufzeitdatenbank
bleibt lokal; das komprimierte Paket wird zusammen mit dem Code versioniert.
"""
from contextlib import closing
import gzip
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory, NamedTemporaryFile

from hs_rag import (DEFAULT_CHUNKS, ROOT, SCHEMA_VERSION, IndexErrorBase, VectorIndex,
                    connect_readonly, database_path, index_status, initialize,
                    metadata, set_metadata)

BUNDLE_PATH = ROOT / 'HS_DATA/_rag/vector_index.sqlite3.gz'


def manifest_path(bundle):
    return Path(str(bundle) + '.json')


def export_index(db_path=None, bundle_path=BUNDLE_PATH, chunks_path=DEFAULT_CHUNKS):
    db_path = Path(db_path) if db_path is not None else database_path()
    bundle_path = Path(bundle_path)
    status = index_status(db_path, chunks_path)
    if not status['ready'] or status['source_changed']:
        raise IndexErrorBase('Für das Deployment zuerst den vollständigen Index mit der aktuellen Chunk-Datei erstellen.')
    # Also validate the document/vector mapping before publishing a bundle.
    VectorIndex(db_path)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='hsos-index-export-') as temporary:
        exported = Path(temporary) / 'index.sqlite3'
        with closing(connect_readonly(db_path)) as source, closing(sqlite3.connect(exported)) as target:
            initialize(target)
            info = metadata(source)
            allowed = ['schema_version', 'model', 'dimensions', 'chunks', 'source_sha256', 'indexed_at']
            with target:
                set_metadata(target, **{k: info[k] for k in allowed},
                             source_path='HS_DATA/_rag/chunks.jsonl', last_attempt_status='complete')
                target.executemany('INSERT INTO documents VALUES (?, ?, ?)',
                                   source.execute('SELECT id, content_hash, document FROM documents'))
                target.executemany('INSERT INTO embeddings VALUES (?, ?, ?, ?)', source.execute('''
                    SELECT DISTINCT e.model, e.content_hash, e.dimensions, e.vector
                    FROM embeddings e JOIN documents d ON d.content_hash=e.content_hash
                    WHERE e.model=?
                ''', (info['model'],)))
            target.execute('VACUUM')
        raw = exported.read_bytes()
        description = {
            'bundle_version': 1, 'schema_version': SCHEMA_VERSION,
            'database_sha256': sha256(raw).hexdigest(), 'database_bytes': len(raw),
            'source_sha256': status['source_sha256'], 'chunks': status['chunks'],
            'model': status['model'], 'dimensions': status['dimensions'],
        }
        packed = Path(temporary) / 'index.sqlite3.gz'
        with packed.open('wb') as output, gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=0) as compressed:
            compressed.write(raw)
        description['compressed_bytes'] = packed.stat().st_size
        description['compressed_sha256'] = sha256(packed.read_bytes()).hexdigest()
        # Stage on the destination filesystem so replace remains atomic.
        with NamedTemporaryFile(dir=bundle_path.parent, suffix='.tmp', delete=False) as staged:
            staged_path = Path(staged.name)
            with packed.open('rb') as input_file:
                shutil.copyfileobj(input_file, staged)
        try:
            staged_path.replace(bundle_path)
        finally:
            staged_path.unlink(missing_ok=True)
        manifest_path(bundle_path).write_text(json.dumps(description, ensure_ascii=False, indent=2) + '\n')
    return description


def ensure_index(db_path=None, bundle_path=BUNDLE_PATH, chunks_path=DEFAULT_CHUNKS):
    """Ein fehlendes Laufzeit-DB-File aus dem mitgelieferten Index wiederherstellen."""
    db_path = Path(db_path) if db_path is not None else database_path()
    bundle_path = Path(bundle_path)
    if db_path.exists():
        # An existing locally maintained/imported index is never overwritten.
        return index_status(db_path, chunks_path)
    if not bundle_path.exists() or not manifest_path(bundle_path).exists():
        return index_status(db_path, chunks_path)
    try:
        description = json.loads(manifest_path(bundle_path).read_text())
        if description['bundle_version'] != 1 or description['schema_version'] != SCHEMA_VERSION:
            raise IndexErrorBase('Das mitgelieferte Indexpaket hat eine nicht unterstützte Version.')
        if description['source_sha256'] != sha256(Path(chunks_path).read_bytes()).hexdigest():
            raise IndexErrorBase('Indexpaket und Wissensdaten passen nicht zusammen. Bitte das Deployment-Paket aktualisieren.')
        raw_size = description['database_bytes']
        if not isinstance(raw_size, int) or not 0 < raw_size <= 256 * 1024 * 1024:
            raise IndexErrorBase('Die Größenangabe im Indexpaket ist ungültig.')
        packed = bundle_path.read_bytes()
        if sha256(packed).hexdigest() != description['compressed_sha256']:
            raise IndexErrorBase('Das komprimierte Indexpaket ist beschädigt.')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=db_path.parent, suffix='.sqlite3.tmp', delete=False) as output:
            staged = Path(output.name)
            total = 0
            digest = sha256()
            try:
                with gzip.open(bundle_path, 'rb') as compressed:
                    while block := compressed.read(128 * 1024):
                        total += len(block)
                        if total > raw_size:
                            raise IndexErrorBase('Das Indexpaket enthält unerwartet viele Daten.')
                        digest.update(block)
                        output.write(block)
            except Exception:
                staged.unlink(missing_ok=True)
                raise
        try:
            if total != raw_size or digest.hexdigest() != description['database_sha256']:
                raise IndexErrorBase('Die Prüfsumme des entpackten Index stimmt nicht.')
            with closing(connect_readonly(staged)) as conn:
                if conn.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise IndexErrorBase('Die mitgelieferte Datenbank ist nicht lesbar.')
            restored = index_status(staged, chunks_path)
            if (not restored['ready'] or restored['source_changed']
                    or restored['chunks'] != description['chunks']
                    or restored['model'] != description['model']
                    or restored['dimensions'] != description['dimensions']):
                raise IndexErrorBase('Inhalt und Beschreibung des Indexpakets stimmen nicht überein.')
            VectorIndex(staged)
            # Avoid replacing an index another startup may have completed meanwhile.
            if not db_path.exists():
                staged.replace(db_path)
        finally:
            staged.unlink(missing_ok=True)
    except IndexErrorBase:
        raise
    except (KeyError, TypeError, ValueError, EOFError, OSError, sqlite3.Error) as exc:
        raise IndexErrorBase('Das Indexpaket konnte nicht geladen werden. Bitte das Paket im Deployment prüfen.') from exc
    return index_status(db_path, chunks_path)
