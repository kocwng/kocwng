# Gaya visual profil kocwng — playful

Satu sistem untuk semua aset (`assets/*.svg`) dan halaman Pendopo (`docs/index.html`).

## Rasa
Ceria, warna-warni, ilustratif, seperti lembar stiker. Bentuk bulat dan gendut, sedikit miring,
gerak memantul (squash & stretch), tidak ada yang kaku atau "korporat". Tidak ada latar kotak
gelap. Tidak ada gradasi indigo/emas gaya lama.

## Palet (pakai persis)
| nama     | hex     | pakai untuk |
|----------|---------|-------------|
| krem     | #FFF6E5 | isi stiker, outline luar |
| tinta    | #2B2340 | detail di DALAM bentuk krem/terang saja |
| jeruk    | #FF8A3D | aksen utama |
| pink     | #FF5FA2 | aksen |
| kuning   | #FFD23F | pisang, bintang |
| mint     | #3DDC97 | aksen |
| langit   | #4CC9F0 | aksen |
| anggur   | #7B5CFF | aksen |

## Aturan wajib: terbaca di tema terang (#ffffff) DAN gelap (#0d1117)
- Latar SVG **transparan**. Jangan ada persegi latar penuh.
- Setiap bentuk berwarna diberi **outline krem #FFF6E5 tebal (4–6px)** → "stiker".
- Bayangan stiker: salinan bentuk yang sama, digeser (+4,+5), warna tinta #2B2340 opacity 0.35.
- Warna tinta tidak boleh berdiri langsung di atas latar transparan (tidak terlihat di tema gelap);
  tinta hanya untuk teks/detail di atas bentuk krem atau berwarna terang.
- Teks judul: isi warna + `stroke="#FFF6E5" stroke-width="6" paint-order="stroke"` + bayangan tinta.

## Huruf (tanpa web font)
- Judul: `'Arial Rounded MT Bold', 'Nunito', 'Varela Round', 'Trebuchet MS', 'Segoe UI', sans-serif`, weight 800.
- Teks kecil: `'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif`.
- Tanpa emoji.

## Gerak
- CSS @keyframes di `<style>` atau SMIL, loop tak hingga, durasi 1.5–4 s, easing `cubic-bezier(.5,-0.4,.5,1.4)` untuk pantulan.
- Delay berbeda-beda supaya tidak serempak.
- `@media (prefers-reduced-motion: reduce)` → matikan semua animasi.

## Teknis (GitHub merender SVG lewat `<img>` + proxy camo)
- Tanpa JavaScript, tanpa resource eksternal, tanpa @import.
- `xmlns`, `width`/`height` = viewBox, `<title>`; < 25 KB; XML valid.

## Isi (hanya fakta ini; jangan mengarang)
username kocwng (jangan tulis nama asli) · Universitas Brawijaya · Indonesia · backend engineer ·
belajar Go (Golang) · suka sains & teknologi · suka baca buku · fun fact: pisang mengandung dopamin ·
stack: Go, Docker, Swagger, MySQL, AWS, Google Cloud, Cloudflare.
