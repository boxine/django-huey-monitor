#!/usr/bin/env python3

"""
    Source code parts are borrowed from Django and bx_py_utils ;)
"""

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


def clean_filename(filename):
    """
    >>> clean_filename('Test äöüß !.exe')
    'test-aou.exe'
    """
    suffix = Path(filename).suffix
    filename = filename[:-len(suffix)]
    return f'{slugify(filename)}.{slugify(suffix)}'


def main():
    base_path = Path('.').resolve()
    print(f"Process path: {base_path}")
    readme_path = base_path / 'README.md'
    assert readme_path.is_file(), f'File not found: {readme_path}'

    image_names = []

    for image_path in sorted(base_path.glob('*.png'), reverse=True):
        cleaned_filename = clean_filename(image_path.name)
        if cleaned_filename != image_path.name:
            print(f'Rename "{image_path.name}" to "{cleaned_filename}"')
            target = image_path.parent / cleaned_filename
            image_path.rename(target)

        image_names.append(image_path.name)

    assert image_names

    print(image_names)
    with readme_path.open('w') as f:
        f.write('## Django-Huey-Monitor screenshots\n')
        f.write('\n')
        f.write('[github.com/boxine/django-huey-monitor](https://github.com/boxine/django-huey-monitor)\n')
        f.write('\n')
        f.write('---\n')
        for image_name in image_names:
            f.write('\n')
            f.write(f'### {image_name}\n')
            f.write('\n')
            f.write(
                f'![{image_name}](https://raw.githubusercontent.com'
                f'/boxine/django-huey-monitor/gh-pages/{image_name})\n'
            )

        f.write('\n')
        f.write('---\n')
        f.write('\n')
        f.write('[github.com/boxine/django-huey-monitor](https://github.com/boxine/django-huey-monitor)\n')
        f.write('\n')
        f.write('---\n')
        f.write('\n')
        f.write(f'(Auto generated with `{Path(__file__).name}` on {datetime.utcnow()})')

    print('Updated:', readme_path)


if __name__ == '__main__':
    main()
