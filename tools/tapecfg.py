"""Shared settings loader for the tape tools.

    from tapecfg import load, ROOT
    cfg = load()

Reads tape.toml at the repo root (Python 3.11+, standard library only) and fills in
defaults plus a few derived values, so every generator sees the same thing:

    cfg['hero']['greeting']   list of 1-2 str
    cfg['tape']['song']       path relative to the repo root, e.g. "docs/music.m4a"
    cfg['tape']['song_abs']   absolute path
    cfg['tape']['song_url']   path relative to docs/, e.g. "music.m4a" (for the page)
    cfg['tape']['label'], ['side'], ['caption'] (list of 2 str), ['link'] (resolved, never empty)
    cfg['tape']['video']      uploaded video URL (github.com/user-attachments/...) or ''
    cfg['tape']['duration']   float seconds (ffprobe, then macOS afinfo; 0.0 if unknown)
    cfg['tape']['length']     "m:ss" or "" if unknown
    cfg['chords']['mode']     "auto" | "keep" | "off"
    cfg['chords']['file']     absolute path of docs/chords.json
    cfg['footer']['text']
    cfg['owner'], cfg['repo'] GitHub owner / repo name (env, git remote, or folder name)
"""
import os
import re
import subprocess
import tomllib

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

DEFAULTS = {
    'hero': {'greeting': ['hello', 'there!']},
    'tape': {'song': 'docs/music.m4a', 'label': 'my tape', 'side': 'A',
             'caption': ['give it', 'a listen!'], 'link': '', 'video': ''},
    'chords': {'mode': 'auto'},
    'footer': {'text': 'thanks for stopping by!'},
}


def _owner_repo():
    gh = os.environ.get('GITHUB_REPOSITORY', '')
    if '/' in gh:
        return gh.split('/', 1)
    try:
        url = subprocess.run(['git', '-C', ROOT, 'remote', 'get-url', 'origin'],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        m = re.search(r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', url)
        if m:
            return m.group(1), m.group(2)
    except (OSError, subprocess.SubprocessError):
        pass
    name = os.path.basename(ROOT)
    name = name[:-len('-profile')] if name.endswith('-profile') else name
    return name, name


def duration(path):
    """Length of an audio file in seconds, or 0.0 if no tool can tell."""
    for cmd in (['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                ['afinfo', path]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        m = re.search(r'estimated duration:\s*([\d.]+)', out) or re.search(r'^([\d.]+)\s*$', out.strip(), re.M)
        if m:
            return float(m.group(1))
    return 0.0


def _two(v, fallback):
    if isinstance(v, str):
        v = [v]
    v = [str(s) for s in (v or []) if str(s).strip()][:2]
    return v or list(fallback)


def load(path=None):
    path = path or os.path.join(ROOT, 'tape.toml')
    raw = {}
    if os.path.exists(path):
        with open(path, 'rb') as f:
            raw = tomllib.load(f)
    cfg = {k: dict(v, **raw.get(k, {})) for k, v in DEFAULTS.items()}

    cfg['hero']['greeting'] = _two(cfg['hero']['greeting'], DEFAULTS['hero']['greeting'])
    t = cfg['tape']
    t['caption'] = _two(t['caption'], DEFAULTS['tape']['caption'])
    t['label'] = str(t['label']).strip() or DEFAULTS['tape']['label']
    t['side'] = (str(t['side']).strip() or 'A')[:2]
    t['song'] = str(t['song']).strip().lstrip('./') or DEFAULTS['tape']['song']
    t['song_abs'] = os.path.join(ROOT, t['song'])
    t['song_url'] = os.path.relpath(t['song_abs'], os.path.join(ROOT, 'docs')).replace(os.sep, '/')
    t['duration'] = duration(t['song_abs']) if os.path.exists(t['song_abs']) else 0.0
    d = int(round(t['duration']))
    t['length'] = f"{d // 60}:{d % 60:02d}" if d else ''

    owner, repo = _owner_repo()
    cfg['owner'], cfg['repo'] = owner, repo
    t['link'] = str(t['link']).strip() or (
        f"https://{owner}.github.io/" if repo.lower() == f"{owner}.github.io".lower()
        else f"https://{owner}.github.io/{repo}/")

    t['video'] = str(t['video']).strip()
    mode = str(cfg['chords']['mode']).strip().lower()
    cfg['chords']['mode'] = mode if mode in ('auto', 'keep', 'off') else 'auto'
    cfg['chords']['file'] = os.path.join(ROOT, 'docs', 'chords.json')
    cfg['footer']['text'] = str(cfg['footer']['text']).strip() or DEFAULTS['footer']['text']
    return cfg


if __name__ == '__main__':
    import json
    print(json.dumps(load(), indent=2))
