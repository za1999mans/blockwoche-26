"""Echte Integrationsprüfung; benötigt API-Zugriff und den fertig importierten Index."""
import argparse
import json
import time

from hs_rag import ROOT, VectorIndex, answer_question, friendly_error, index_status, load_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--answers', action='store_true', help='Zusätzlich eine echte Chatantwort prüfen')
    args = parser.parse_args()
    load_environment()
    try:
        status = index_status()
        if not status['ready'] or status['source_changed']:
            raise ValueError('Index muss vollständig und aktuell importiert sein')
        index = VectorIndex()
        cases = [
            ('Wann findet der Hochschulinfotag 2026 statt?', '05_tag_der_offenen_tuer_faq.md', {}),
            ('Wie erreiche ich den Campus Lingen mit der Bahn und wie lautet die Adresse?',
             '03_campus_und_standorte.md', {}),
            ('Welche Module hat Technische Informatik im ersten Semester?',
             '04_studiengaenge/informatik_technische_informatik_b_sc.md',
             {'programme': 'Informatik – Technische Informatik (B.Sc.)'}),
            ('Welche Zugangsvoraussetzungen braucht ETS Elektrotechnik dual in Lingen?',
             '04_studiengaenge/ets_elektrotechnik_b_eng_dual_standort_lingen_ems.md', {}),
            ('Welche Bewerbungsfrist gilt für Land Use Transformation im Sommersemester 2027 mit deutschem Abschluss?',
             '04_studiengaenge/land_use_transformation_m_sc.md', {}),
            ('Wie hoch war der NC für Wirtschaftspsychologie im Wintersemester 2025/2026?',
             '06_nc_auswahlgrenzen.md', {}),
        ]
        results = []
        for question, expected, options in cases:
            start = time.perf_counter()
            hits = index.search(question, **options)
            found = [h.chunk['file'] for h in hits]
            row = {'question': question, 'expected_file': expected, 'passed': expected in found,
                   'seconds': round(time.perf_counter() - start, 3),
                   'hits': [{'file': h.chunk['file'], 'heading': h.chunk['heading'],
                             'score': round(h.score, 4)} for h in hits]}
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        if args.answers:
            reply = answer_question(cases[0][0], index)
            row = {'question': cases[0][0], 'answer': reply['answer'],
                   'sources': reply['sources'],
                   'passed': bool(reply['sources']) and '19' in reply['answer']
                   and ('November' in reply['answer'] or '11.' in reply['answer'])}
            print(json.dumps({'answer_check': row}, ensure_ascii=False), flush=True)
        else:
            row = None
        report = {'index': status, 'retrieval': results, 'answer_check': row,
                  'passed': all(r['passed'] for r in results) and (row is None or row['passed'])}
        (ROOT/'data/hs_rag_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['passed'] else 1
    except Exception as exc:
        print(friendly_error(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
