# jp_errant_bea (2025) by stanza

ERRANT toolkit for grammatical error correction evaluation and M2 format processing, supporting multiple languages including European languages, Chinese, and Korean.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd jp_errant_bea-main

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Basic Usage

#### Convert Parallel Text to M2 Format (Main Command)
```bash
jp_errant_parallel -orig path/to/original.txt -cor path/to/corrected.txt -out path/to/output.m2 -lang en
```

#### Extract Original Sentences from M2 Files
```bash
python jp_errant/commands/rev_from_m2.py input.m2 -out original_sentences.txt
```

#### Extract Corrected Sentences from M2 Files
```bash
python jp_errant/commands/corr_from_m2.py input.m2 -out corrected_sentences.txt -id 0
```

#### Compare M2 Files
```bash
jp_errant_compare reference.m2 hypothesis.m2
```

## Supported Languages

- **English** (en)
- **Chinese** (zh) 
- **Korean** (ko)
- **Czech** (cs)
- **German** (de)
- **Ukrainian** (uk)
- **Multi-language** support

## Command Line Tools

| Command | Description |
|---------|-------------|
| `jp_errant_parallel` | **Main command**: Convert parallel texts to M2 format |
| `jp_errant_compare` | Compare different M2 files |
| `jp_errant_m2` | Convert between M2 formats |
| `rev_from_m2.py` | Extract original sentences from M2 files |
| `corr_from_m2.py` | Apply corrections and generate corrected sentences |

### jp_errant_parallel Options

```bash
jp_errant_parallel -orig ORIG -cor COR [COR ...] -out OUT [options]

Required:
  -orig ORIG           Path to the original text file
  -cor COR [COR ...]   Paths to one or more corrected text files
  -out OUT             Output filepath for M2 format

Optional:
  -lang LANG           2-letter language code (default: en)
  -tsv yes             Input files are TSV format
  -lev                 Use standard Levenshtein alignment
  -merge STRATEGY      Merging strategy: rules, all-split, all-merge, all-equal
```

## M2 Format

The M2 format contains:
- **S lines**: Original sentences (source)
- **A lines**: Annotation/edit information with start position, end position, correction type, replacement text, and annotator ID

Example:
```
S This are a example sentence .
A 1 2|||Verb:SVA|||is|||REQUIRED|||-NONE-|||0

S He go to school yesterday .
A 1 2|||Verb:Tense|||went|||REQUIRED|||-NONE-|||0
```

## Examples

See the `docs/` directory for detailed examples and Jupyter notebooks demonstrating usage.


Please cite the jp-errant-bea system:
```
@inproceedings{qiu-etal-2025-multilingual,
    title = "Multilingual Grammatical Error Annotation: Combining Language-Agnostic Framework with Language-Specific Flexibility",
    author = "Qiu, Mengyang  and
      Nguyen, Tran Minh  and
      Huang, Zihao  and
      Li, Zelong  and
      Gu, Yang  and
      Gao, Qingyu  and
      Liu, Siliang  and
      Park, Jungyeul",
    editor = {Kochmar, Ekaterina  and
      Alhafni, Bashar  and
      Bexte, Marie  and
      Burstein, Jill  and
      Horbach, Andrea  and
      Laarmann-Quante, Ronja  and
      Tack, Ana{\"i}s  and
      Yaneva, Victoria  and
      Yuan, Zheng},
    booktitle = "Proceedings of the 20th Workshop on Innovative Use of NLP for Building Educational Applications (BEA 2025)",
    month = jul,
    year = "2025",
    address = "Vienna, Austria",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.bea-1.15/",
    pages = "202--212",
    ISBN = "979-8-89176-270-1",
}
```

For the original jp-errnat:
```
@inproceedings{wang-etal-2025-refined,
    title = "Refined Evaluation for End-to-End Grammatical Error Correction Using an Alignment-Based Approach",
    author = "Wang, Junrui  and
      Qiu, Mengyang  and
      Gu, Yang  and
      Huang, Zihao  and
      Park, Jungyeul",
    editor = "Rambow, Owen  and
      Wanner, Leo  and
      Apidianaki, Marianna  and
      Al-Khalifa, Hend  and
      Eugenio, Barbara Di  and
      Schockaert, Steven",
    booktitle = "Proceedings of the 31st International Conference on Computational Linguistics",
    month = jan,
    year = "2025",
    address = "Abu Dhabi, UAE",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.coling-main.52/",
    pages = "774--785",
}
```
