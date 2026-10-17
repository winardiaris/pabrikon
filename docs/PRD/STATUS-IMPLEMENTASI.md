# Status Implementasi Pabrikon v2

**Diperbarui:** 2026-10-17
**Sumber status:** Checklist PRD Sections 33 dan 46, source, test, CI, README, manual, dan delapan referensi struktur repo icon theme ditinjau 2026-10-17.

Dokumen ini merangkum pekerjaan yang selesai, parsial, dan belum tersedia; lihat laporan akhir task untuk hasil validasi terakhir. Untuk rincian kebutuhan, lihat [PRD utama](PRD-pabrikon.md).

## Keputusan kesiapan rilis v2

**Task 22 perlu ditinjau ulang; rilis stabil MVP belum siap.** Adopsi repo icon
theme (task 7a) sudah memiliki implementasi awal, tetapi belum memiliki fixture
ter-pinned dan verifikasi terhadap delapan struktur referensi. Rilis alpha
bisa dibuat dengan batasan ini diumumkan, tetapi belum memenuhi scope rilis
stabil MVP saat ini.

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
- README, manual, dan `CONTRIBUTING.md` untuk instalasi, alur lengkap, panduan adopsi repo icon theme, serta pemeriksaan contributor melalui Ubuntu atau Docker.

## Parsial

- **Adopsi project (task 7a):** CLI dapat memindai repo lokal atau clone eksplisit, membuat rencana dry-run, mempertahankan struktur direktori SVG sesuai `index.theme`, serta mengimpor symlink SVG aman sebagai usulan alias di `data/aliases.toml` sambil mempertahankan sumber. Output SVG mengikuti direktori sumber; PNG diarahkan ke direktori fixed-size yang dideklarasikan dan menghormati `Scale`. Symlink rusak, keluar dari theme root, tak didukung, atau ambigu dilaporkan untuk tinjauan manual; file alias yang sudah ada tidak ditimpa. Belum ada fixture ter-pinned untuk delapan repo referensi dan verifikasi penuh HiDPI, symbolic, cursor, metadata alternatif, serta pola symlink; ini tetap blocker rilis stabil MVP.
- **Dukungan metadata theme:** field dasar `index.theme` tersedia, tetapi cakupan spesifikasi Freedesktop belum lengkap. Rincian gap ada di [PRD utama, bagian 18](PRD-pabrikon.md#18-theme-metadata).

## Belum dikerjakan

- **Fixture adopsi delapan repo:** belum tersedia untuk BlankOn/Tebu-Flat, Shadow, Newaita, Paper, Numix, Adwaita, Citropy, dan Breeze. Cakupan struktur yang perlu diuji mencakup root bertingkat atau ganda, susunan size-first dan context-first, metadata alternatif/terpisah, HiDPI, symbolic/cursors, file tersembunyi, collision, lisensi, dan submodule. Breeze juga perlu dibangun untuk menghasilkan `index.theme`. Rincian dan sumber ada di PRD task 7a.
- **Pemetaan adopsi tambahan:** metadata `index.theme` deklarasi `Type=Scalable` dipakai untuk memetakan SVG scalable ke layout v2, termasuk direct-context dan direktori berukuran. Raster-only, symbolic, cursor, metadata alternatif selain `index.theme` utama, dan layout tanpa metadata yang dihasilkan tetap perlu penanganan.

### Gap metadata Freedesktop yang masih terbuka

- Dukungan field header `Hidden`, `Example`, serta nama dan deskripsi terlokalisasi.
- Dukungan lengkap metadata per direktori: `Size`, `Context`, `Type`, `MinSize`, `MaxSize`, dan `Threshold`.
- Peninjauan daftar context yang didukung.
- Keputusan dukungan aset XPM dan file metadata icon `.icon`.
- Opsi konfigurasi skala mandiri dan fixture kompatibilitas HiDPI seperti `22x22@2x`; adopsi saat ini mengikuti nilai `Scale` yang ada di `index.theme`. Ini terpisah dari spesifikasi 0.10.
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
