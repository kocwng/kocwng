# Make your own tape

This repo is a GitHub profile README with a cassette tape that plays a song. A banana mascot plays ukulele along with the chords. You can copy it and put your own song in it. You only edit one settings file, and a GitHub Action redraws the pictures for you.

## What you get

- **hero.svg**: your greeting in big colourful letters, with the banana playing the chords of your song.
- **music.svg**: a cassette with your label on it. Clicking it opens your music page.
- **docs/index.html**: the music page. It has a play button, a visualizer, and a chord card that follows the song.
- **footer.svg**: a thank-you ribbon with your own words.

All the pictures are animated SVG files with no scripts, so GitHub shows them as they are.

## Steps

1. **Copy the repo.** Click **Use this template** (or fork it). Name the new repo exactly like your GitHub username. That is what makes GitHub show it on your profile.

2. **Let the Action save its work.** Go to *Settings → Actions → General → Workflow permissions*. Choose **Read and write permissions** and save. If you forked the repo, also open the **Actions** tab and turn workflows on.

3. **Turn on the music page.** Go to *Settings → Pages*. Choose **Deploy from a branch**, then branch `main` and folder `/docs`. The page will live at `https://<you>.github.io/<you>/`.

4. **Add your song.** Upload it into the `docs/` folder. It can be mp3, m4a, ogg, or wav. Keep it short, around a minute and under 10 MB, so it loads fast. Delete `docs/music.m4a`, because that recording isn't yours to reuse (see [License](#license)).

5. **Edit `tape.toml`.** It holds your greeting, the song file name, the cassette label, and the footer text. Each line has a comment explaining it.

6. **Edit `README.md`.** Write your own intro, list, and tech badges. Leave the `<!-- tape:start -->` and `<!-- tape:end -->` lines in place: the build uses them to fill in the cassette link.

7. **Commit.** The **build tape** Action works out the chords, redraws the pictures, and commits them. It takes about a minute. You can watch it in the **Actions** tab.

## Chords

When `mode = "auto"`, the chords are detected from the song whenever the song file changes. The detector is simple, so expect a few wrong chords, especially on songs with singing or drums.

To fix them by hand, edit `docs/chords.json`:

- **`timeline`**: entries of `["chord", start_seconds, end_seconds]`.
- **`shapes`**: the ukulele fingering for each chord. It has 4 digits for the strings G C E A. Each digit is the fret to press, `0` means an open string, and `x` means muted.
- **`beat`**: seconds per strum.

Then set `mode = "keep"` in `tape.toml`, so the Action never overwrites your fixes.

If your song has no chords to show, set `mode = "off"`. The banana will just strum.

## Building on your own computer

You only need this if you don't want to use the Action. You need Python 3.11 or newer and ffmpeg.

```bash
pip install numpy scipy
```

```bash
python3 tools/build.py
```

## Cleaning up a phone recording

`tools/master.py` makes a rough recording sound better. It trims silence, balances left and right, reduces noise, applies EQ and light compression, adds a touch of room reverb, and sets loudness to −16 LUFS. It works on WAV files:

```bash
pip install numpy scipy soundfile noisereduce pyloudnorm
```

```bash
ffmpeg -i my-song.m4a my-song.wav
```

```bash
python3 tools/master.py my-song.wav docs/my-song.wav
```

## License

The code and the pictures (the banana, cassette, and ribbon) are MIT licensed. Use them however you like. The recording in `docs/music.m4a` belongs to kocwng and is **not** included in that license. Replace it with your own.
