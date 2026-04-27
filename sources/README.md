# Source PDFs

Place future PDFs here when you want batch processing. Use one folder per category:

```text
sources/
  classical-roots/
    Vocabulary_from_classical_roots.pdf
  medical/
    medical_terms.pdf
```

Then run:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-batch sources --category-from-parent
```

PDF files are source material. Generated raw, normalized, review, report, and database artifacts belong under `data/` and `reports/`.
