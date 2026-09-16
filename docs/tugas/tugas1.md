# Tugas 1 - Static Web with HTML5 and CSS3

## Pertanyaan Reflektif

### Tugas 1

1. Pada Tutorial dan Tugas 1, Anda diberi kebebasan untuk menentukan tampilan dari website portofolio Anda. Saat Anda merancang struktur HTML yang digunakan, apakah Anda menggunakan elemen semantik HTML5 seperti <section>, <article>, atau <aside>? Jika iya, bagaimana elemen tersebut membantu Anda dalam membuat static web? Jika tidak, mengapa tanpa elemen tersebut sudah memenuhi kebutuhan desain Anda?

Ans: Iya, saya pakai elemen semantik HTML5 kayak `<header>`, `<nav>`, `<main>`, `<section>`, dan `<footer>` untuk memisah tiap bagian halaman (Profile, Skills, Portfolio). Selain itu di section Portfolio saya pakai `<figure>` dan `<figcaption>` buat tiap foto, karena itu lebih sesuai secara nama elemen dibanding sekadar `<div>` biasa untuk gambar + keterangannya. Awalnya section Skills saya bikin pakai `<dl>`/`<dt>`/`<dd>` meniru contoh dari Tutorial 01, tapi setelah dipikir lagi itu kurang cocok untuk menampilkan grid ikon skill (karena `dl` semestinya untuk pasangan label-nilai, bukan kumpulan ikon), jadi saya restructure jadi card-based (`<div class="skill-card">`) yang isinya judul kategori + grid ikon. Elemen-elemen semantik ini cukup membantu ketika saya baca ulang kode sendiri, karena struktur section langsung terbaca hanya dari nama tag-nya, tidak perlu nebak-nebak div mana isinya apa. Bonusnya juga lebih ramah screen reader dan SEO dibanding numpuk `<div>` saja.

2. Ketika Anda mengatur CSS Anda agar tetap responsive, tantangan tata letak apa yang Anda temukan? Bagaimana Anda mengevaluasi elemen mana yang harus diubah posisinya atau diprioritaskan ukurannya saat berpindah dari tampilan desktop ke mobile?

Ans: Tantangan paling kerasa itu di section Skills dan Portfolio, karena isinya bisa bertambah kapan aja (misal menambah kategori skill baru atau foto baru), jadi saya tidak mau menulis breakpoint manual satu-satu seperti di section Profile (yang masih pakai `@media (max-width: 600px)` dari Tutorial 01). Solusinya saya pakai `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))` di kedua section itu. Jadi browser otomatis nentuin berapa kolom yang muat, dan kalau layar makin sempit, kolom otomatis collapse jadi satu tanpa saya nulis breakpoint tambahan. Cara saya evaluasi elemen mana yang perlu diprioritasin itu dengan saya coba resize browser manual dari lebar ke sempit, terus lihat titik mana yang mulai keliatan sempit/numpuk (foto ke-crop aneh, ikon ke-squeeze, dst), baru dari situ saya tentuin ukuran minimum kartu/item yang wajar.

3. Website yang Anda buat saat ini adalah static web murni. Batasan apa yang Anda rasakan saat mencoba menyajikan informasi pada portofolio Anda secara optimal? Berdasarkan batasan tersebut, fungsionalitas dinamis apa yang paling ingin Anda persiapkan dan tambahkan pada iterasi proyek selanjutnya?

Ans: Batasan paling kerasa itu semua konten (skill, foto portfolio, dst) masih hardcoded langsung di HTML. Kalau saya mau nambah 1 skill baru atau ganti 1 foto, saya harus edit `index.html` manual, push, terus deploy ulang. Tidak ada tempat buat menyimpan data yang bisa diubah tanpa nyentuh kode, apalagi ada semacam panel buat update konten sendiri. Dari batasan ini, yang paling ingin saya siapkan di iterasi selanjutnya itu bikin model Django untuk Skills dan Portfolio (pakai database), jadi nanti nambah/edit/hapus item bisa lewat Django admin tanpa perlu edit HTML/CSS langsung.

## AI Disclosure

Saya menggunakan Claude sonnet 4.6 untuk bantu menyusun workflow commit push dan mengukur responsiveness CSS grid. Namun beberapa kali ditemukan batasan ukuran responsiveness yang tampak secara visual kurang pas dilihat oleh mata sehingga ukuran responsiveness tetap perlu di adjust manual kembali. 

Dalam menyusun layout CSS yang responsif, generator AI digunakan untuk membuat struktur tata letak dasar berbasis kalkulasi geometris murni. Namun, penyesuaian nilai margin, padding, dan ukuran elemen tetap dilakukan secara manual menggunakan pendekatan optical alignment. Langkah ini didukung oleh temuan McManus et al. (2011) yang menunjukkan bahwa kalkulasi fisik/matematis murni (seperti Centre of Mass) tidak selalu menghasilkan persepsi keseimbangan visual yang harmonis bagi mata manusia, sehingga koreksi visual secara manual tetap diperlukan.

Bagian yang saya kerjain/putuskan sendiri mulai dari pemilihan konten section (Skills & Portfolio), isi/teks tiap bagian (bio, daftar skill, caption foto), skema warna dan font (lanjutin dari palet Tutorial 01), serta keputusan final struktur HTML/CSS yang dipakai.

## Sumber Referensi
McManus, I. C., Stöver, K., & Kim, D. (2011). Arnheim's Gestalt Theory of Visual Balance: Examining the Compositional Structure of Art Photographs and Abstract Images. i-Perception, 2(6), 615–647. https://doi.org/10.1068/i0445aap