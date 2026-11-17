"""Assemble the reviewed research deliverables and a checksummed archive."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
PREFIX = 'Optical_Review_Coating_Reproducibility'


def main():
    rendered = ROOT / 'qa/approved_Optical_Review_Coating_Manuscript/Optical_Review_Coating_Manuscript.pdf'
    pdf = OUT / 'Optical_Review_Coating_Manuscript.pdf'
    if rendered.exists():
        shutil.copyfile(rendered, pdf)
    if not pdf.exists():
        raise FileNotFoundError('Export and visually inspect the manuscript PDF before packaging.')
    shutil.copyfile(ROOT / 'qa/equations.md', ROOT / 'notes/equations.md')

    excluded = {
        'HfO2_original.yml', 'Ta2O5_original.yml', 'Ta2O5_nk.npy',
        'SiO2_film_original.yml', 'SiO2_film_nk.npy',
        'metadata_check.json', 'metadata.log',
    }
    files = [ROOT / 'README.md', ROOT / 'requirements.txt']
    files += sorted((ROOT / 'code').glob('*.py'))
    for directory in ['data', 'figures', 'references']:
        files += sorted(p for p in (ROOT / directory).iterdir()
                        if p.is_file() and p.name not in excluded)
    files += sorted(p for p in (ROOT / 'notes').iterdir()
                    if p.is_file() and p.suffix in {'.md', '.json'})
    files += sorted(OUT.glob('*.docx')) + [pdf]
    files += [ROOT / 'qa/integrity_audit.json', ROOT / 'qa/visual_quality.json']
    assert all(p.is_file() and not p.is_symlink() for p in files)
    assert not any(p.name == 'primary_materials_internal.pdf' for p in files)
    assert len(files) == len(set(files))
    sums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
                   p.relative_to(ROOT).as_posix() + '\n' for p in files)
    archive = OUT / (PREFIX + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, PREFIX + '/' + p.relative_to(ROOT).as_posix())
        z.writestr(PREFIX + '/SHA256SUMS.txt', sums)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for p in files:
            name = PREFIX + '/' + p.relative_to(ROOT).as_posix()
            assert hashlib.sha256(z.read(name)).digest() == hashlib.sha256(p.read_bytes()).digest()
    print(json.dumps({'archive': str(archive), 'payload_files': len(files),
                      'size_bytes': archive.stat().st_size,
                      'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                      'archive_integrity': 'passed'}, indent=2))


if __name__ == '__main__':
    main()
