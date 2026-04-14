"""
Slug generation utilities.
"""
from __future__ import annotations

import re
import secrets
import unicodedata

# Hebrew consonant → latin transliteration (phonetic approximation)
_HE_TO_LATIN: dict[str, str] = {
    'א': 'a',  'ב': 'b',  'ג': 'g',  'ד': 'd',  'ה': 'h',
    'ו': 'v',  'ז': 'z',  'ח': 'kh', 'ט': 't',  'י': 'y',
    'כ': 'k',  'ך': 'k',  'ל': 'l',  'מ': 'm',  'ם': 'm',
    'נ': 'n',  'ן': 'n',  'ס': 's',  'ע': 'a',  'פ': 'p',
    'ף': 'p',  'צ': 'ts', 'ץ': 'ts', 'ק': 'k',  'ר': 'r',
    'ש': 'sh', 'ת': 't',
}


def generate_secure_slug(business_name: str) -> str:
    """
    Convert a business name into a branded but cryptographically unguessable URL slug.

    Steps:
      1. Transliterate Hebrew characters to latin equivalents.
      2. Normalise (NFKD) and strip remaining non-ASCII.
      3. Lowercase and replace non-alphanumeric runs with hyphens.
      4. Truncate the readable prefix to 40 chars.
      5. Append a 6-character cryptographically random hex suffix.

    Examples:
      "חשמלאי אמנון"  → "khshmlai-amnon-a7f9b2"
      "Amnon Electric" → "amnon-electric-3d8c1e"
      ""               → "biz-f041ab"
    """
    name = (business_name or '').strip()

    # 1. Transliterate Hebrew
    latin = ''.join(_HE_TO_LATIN.get(ch, ch) for ch in name)

    # 2. Strip diacritics / non-ASCII
    latin = (
        unicodedata.normalize('NFKD', latin)
        .encode('ascii', 'ignore')
        .decode('ascii')
        .lower()
    )

    # 3. Slugify
    latin = re.sub(r'[^a-z0-9]+', '-', latin).strip('-')
    latin = re.sub(r'-{2,}', '-', latin)

    # 4. Readable prefix (max 40 chars)
    prefix = latin[:40].strip('-') or 'biz'

    # 5. Cryptographically random 6-char hex suffix — makes enumeration infeasible
    suffix = secrets.token_hex(3)  # 3 bytes → 6 hex chars, 16M possibilities

    return f"{prefix}-{suffix}"
