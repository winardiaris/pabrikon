# Status Implementasi Pabrikon v2

**Diperbarui:** 2026-10-17  
**Sumber status:** Checklist PRD Sections 33 dan 46 serta source, test, CI, README, dan manual ditinjau kembali 2026-10-17.

Dokumen ini merangkum pekerjaan yang selesai, parsial, dan belum tersedia; lihat laporan akhir task untuk hasil validasi terakhir. Untuk rincian kebutuhan, lihat [PRD utama](PRD-pabrikon.md).

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
- README dan manual untuk instalasi, alur lengkap, serta panduan manual menyiapkan repo icon theme yang sudah ada.

## Parsial

- **Adopsi project manual:** dokumentasi menjelaskan cara menyalin SVG ke layout v2. Otomatisasi analisis repo dan normalisasi layout belum tersedia.
- **CI dan panduan contributor:** CI menjalankan test, acceptance workflow, Ruff, mypy, dan build wheel. Panduan contributor masih terbatas.
- **Dukungan metadata theme:** field dasar `index.theme` tersedia, tetapi cakupan spesifikasi Freedesktop belum lengkap. Rincian gap ada di [PRD utama, bagian 18](PRD-pabrikon.md#18-theme-metadata).

## Belum dikerjakan

- **Adopsi icon theme yang sudah ada:** belum ada alur untuk menemukan root theme, termasuk root bertingkat atau beberapa pilihan theme; menyusun `pabrikon.toml` dari bukti repo; menampilkan dry-run; dan menata aset yang dikenali ke layout v2 dengan aman.
- **Acceptance fixture adopsi:** belum ada fixture/test integrasi untuk BlankOn/tebu-flat, rudrab/Shadow, dan cbrnix/Newaita. Uji harus mencakup root ambigu, beberapa file `index.theme`, aset/folder yang tidak dikenal, konflik nama/path, konfigurasi yang sudah ada, lisensi, symlink, dan submodule.
- **Review penyelesaian MVP dan persiapan rilis:** belum dilakukan.

### Gap metadata Freedesktop yang masih terbuka

- Dukungan field header `Hidden`, `Example`, serta nama dan deskripsi terlokalisasi.
- Dukungan lengkap metadata per direktori: `Size`, `Context`, `Type`, `MinSize`, `MaxSize`, dan `Threshold`.
- Peninjauan daftar context yang didukung.
- Keputusan dukungan aset XPM dan file metadata icon `.icon`.
- Peninjauan konvensi HiDPI seperti `22x22@2x`; ini terpisah dari spesifikasi 0.10.
- Fixture kompatibilitas dan validasi untuk metadata serta ekstensi yang dipilih.

## Ditunda, bukan syarat MVP

- Preview lokal di browser dan icon browser.
- GUI dan editor icon.
- Paket Debian/RPM.
- Hosting project atau sinkronisasi remote otomatis.
- Pembuatan icon dengan AI.

Dokumentasi migrasi dari Pabrikon lama bukan pekerjaan yang diperlukan: Pabrikon v2 diperlakukan sebagai project baru. Fitur adopsi pada daftar di atas adalah untuk repo icon theme pihak ketiga.
