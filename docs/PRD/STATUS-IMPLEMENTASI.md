# Status Implementasi Pabrikon v2

**Diperbarui:** 2026-10-17
**Sumber status:** Checklist PRD Sections 33 dan 46, source, test, CI, README, manual, dan enam referensi struktur repo icon theme ditinjau 2026-10-17.

Dokumen ini merangkum pekerjaan yang selesai, parsial, dan belum tersedia; lihat laporan akhir task untuk hasil validasi terakhir. Untuk rincian kebutuhan, lihat [PRD utama](PRD-pabrikon.md).

## Keputusan kesiapan rilis v2

**Review task 22 selesai; rilis stabil MVP belum siap.** Satu syarat Required di
PRD yang belum dikerjakan adalah adopsi repo icon theme yang sudah ada (task
7a). Pengguna masih harus menyalin aset dan menyiapkan konfigurasi secara
manual. Rilis alpha bisa dibuat dengan batasan ini diumumkan, tetapi belum
memenuhi scope rilis stabil MVP saat ini.

## Selesai

- Fondasi package Python 3.12+, `pyproject.toml`, entry point CLI, dan penanganan error dasar.
- `pabrikon init` untuk membuat project baru.
- Perencanaan build dan `pabrikon build`, termasuk opsi build dan output yang incremental.
- `pabrikon clean` dengan dry-run, filter, dan perlindungan source.
- Validasi dasar konfigurasi, path, SVG/XML, alias, dan metadata `index.theme`.
- Optimasi SVG dengan output terpisah secara default dan opsi in-place.
- Manajemen alias berbasis TOML, termasuk pemeriksaan target dan siklus.
- `pabrikon info`, perintah listing dasar, dan packaging tar.gz.
- Opsi CLI verbose, quiet, JSON, exit code, shell completion, serta pemeriksaan Ruff dan mypy di CI.
- Test unit, acceptance end-to-end pada wheel terpasang, dan GitHub Actions untuk test, lint, type check, serta build wheel.
- README, manual, dan `CONTRIBUTING.md` untuk instalasi, alur lengkap, panduan menyiapkan repo icon theme yang sudah ada, serta pemeriksaan contributor melalui Ubuntu atau Docker.

## Parsial

- **Adopsi project:** dokumentasi menjelaskan penyiapan manual. Otomatisasi analisis repo dan normalisasi layout belum tersedia; ini blocker rilis stabil MVP.
- **Dukungan metadata theme:** field dasar `index.theme` tersedia, tetapi cakupan spesifikasi Freedesktop belum lengkap. Rincian gap ada di [PRD utama, bagian 18](PRD-pabrikon.md#18-theme-metadata).

## Belum dikerjakan

- **Adopsi icon theme yang sudah ada:** belum ada alur untuk menemukan root theme, termasuk root bertingkat atau beberapa pilihan theme; menyusun `data/pabrikon.toml` dari bukti repo; menampilkan dry-run; dan menata aset yang dikenali ke layout v2 dengan aman.
- **Fixture adopsi enam repo:** belum tersedia untuk BlankOn/Tebu-Flat, Shadow, Newaita, Paper, Numix, dan Adwaita. Cakupan struktur yang perlu diuji mencakup root bertingkat atau ganda, susunan size-first dan context-first, metadata alternatif/terpisah, HiDPI, symbolic/cursors, file tersembunyi, collision, lisensi, dan submodule. Rincian dan sumber ada di PRD task 7a.

### Gap metadata Freedesktop yang masih terbuka

- Dukungan field header `Hidden`, `Example`, serta nama dan deskripsi terlokalisasi.
- Dukungan lengkap metadata per direktori: `Size`, `Context`, `Type`, `MinSize`, `MaxSize`, dan `Threshold`.
- Peninjauan daftar context yang didukung.
- Keputusan dukungan aset XPM dan file metadata icon `.icon`.
- Peninjauan konvensi HiDPI seperti `22x22@2x`; ini terpisah dari spesifikasi 0.10.
- Fixture kompatibilitas dan validasi untuk metadata serta ekstensi yang dipilih.

Review task 22 sudah mencatat bahwa kekurangan metadata lanjutan bukan blocker
MVP; implementasi dasar `index.theme` sudah tersedia.

## Ditunda, bukan syarat MVP

- Preview lokal di browser dan icon browser.
- GUI dan editor icon.
- Paket Debian/RPM.
- Hosting project atau sinkronisasi remote otomatis.
- Pembuatan icon dengan AI.

Dokumentasi migrasi dari Pabrikon lama bukan pekerjaan yang diperlukan: Pabrikon v2 diperlakukan sebagai project baru. Fitur adopsi pada daftar di atas adalah untuk repo icon theme pihak ketiga.
