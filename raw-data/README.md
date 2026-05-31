# Raw Textbook Data

Place raw textbook files (PDF, TXT) here, organized by grade or category.

## Structure

```
raw-data/
  materials/
    grade-4/     # Grade 4 textbooks
    grade-5/     # Grade 5 textbooks
    grade-8/     # Grade 8 textbooks
    grade-10/    # Grade 10 textbooks
    grade-11/    # Grade 11 textbooks
    other/       # Uncategorized / archival sources
```

## Batch Processing

Run all sources in a directory tree, using the parent folder name as the category:

```bash
PYTHONPATH=src python -m vocab_pipeline.cli run-batch raw-data/materials --category-from-parent
```

Or process a single file:

```bash
PYTHONPATH=src python -m vocab_pipeline.cli run-all raw-data/materials/grade-4/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt --category grade-4
```

## Output

All pipeline outputs go to `content/` — see the project [README](../README.md) for details.
