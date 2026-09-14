# Tugas 2 - Implementasi MVT pada Django

## Pertanyaan Reflektif

### Tugas 2

1. Jelaskan alur yang terjadi ketika pengguna membuka halaman portofolio baru, mulai dari permintaan yang diterima proyek hingga data ditampilkan pada browser. Dalam jawabanmu, jelaskan peran urls.py proyek, urls.py aplikasi, view, model, dan template.

Ans: Alurnya dimulai waktu browser kirim request ke `/photography/`. Request itu pertama ketemu `portofolio/urls.py` (urlconf proyek), yang cuma punya dua path yaitu `admin/` dan `""` yang di-include ke `main.urls` lewat `include("main.urls")`. Karena URL-nya diawali `photography/`, Django lempar ke urlconf aplikasi, lalu dicocokin lagi di `main/urls.py` yang punya `path("photography/", show_photography, name="show_photography")`. Setelah ketemu match, Django panggil fungsi `show_photography` di `main/views.py`.

Di dalam view itu, diquery semua objek `Photograph` lewat `Photograph.objects.all()`. Ini bagian yang komunikasi ke model, jadi model di sini berperan sebagai lapisan yang tahu struktur tabel database dan cara ambil datanya. Hasil query itu dimasukin ke dictionary `context` dengan key `featured_photographs`, lalu view manggil `render(request, "photography.html", context)`, artinya data itu diserahin ke template.

Di `templates/photography.html`, Django Template Language baca context yang dikirim, terus loop `{% for photograph in featured_photographs %}` buat render tiap objek jadi HTML (judul, cerita, spek kamera, proses editing, dst). Kalau querysetnya kosong, blok `{% empty %}` yang jalan dan nampilin pesan placeholder. Hasil akhirnya HTML lengkap yang dikirim balik ke browser sebagai response.

2. Mengapa data untuk bagian portofolio baru sebaiknya disimpan pada model dan tidak ditulis langsung di dalam template? Jelaskan dampaknya terhadap kemudahan pemeliharaan dan pengembangan aplikasi.

Ans: Kalau data ditulis langsung di template, setiap kali mau nambah atau ubah satu foto harus edit file HTML manual, commit, push, terus nunggu redeploy ke PWS. Cara ini ribet dan mudah salah kalau formatnya nggak konsisten antar entri.

Kalau disimpan di model bisa nambah, ubah, atau hapus data lewat Django admin di `/admin/` tanpa nyentuh kode sama sekali, dan perubahannya langsung kelihatan begitu tersimpan ke database tanpa perlu deploy ulang. Pendekatan ini juga memisah concern antara data (isi/konten) dengan presentation (cara nampilinnya), jadi kalau suatu saat mau ubah desain kartu foto, cukup ubah template dan datanya tetap aman. Selain itu jadi lebih gampang ditest juga, karena bisa bikin data dummy lewat `Photograph.objects.create()` di unit test tanpa harus menyentuh HTML.

3. Apa perbedaan fungsi makemigrations dan migrate pada Django? Berikan contoh perubahan model yang mengharuskanmu menjalankan kedua perintah tersebut.

Ans: `makemigrations` tugasnya baca perubahan yang ada di `models.py`, lalu generate file migrasi baru (misalnya `0002_photograph.py`) yang isinya instruksi perubahan skema, semacam blueprint perubahan. Tapi perintah ini sendiri belum ngubah apa-apa di database sungguhan, dia cuma nyiapin filenya.

`migrate` itu yang beneran eksekusi blueprint tadi ke database, jadi tabel yang dimaksud baru kebentuk atau berubah setelah `migrate` dijalanin.

Contoh konkretnya waktu nambah model `Photograph` di tugas ini. Setelah menulis modelnya di `main/models.py` dengan field seperti `story`, `camera_gear`, `capture_settings`, dan `editing_software`, kemudian menjalankan `python manage.py makemigrations main`, dan itu yang mengenerate `main/migrations/0002_photograph.py`. Setelah itu baru dijalankan `python manage.py migrate`, baru tabel `Photograph` beneran ada di `db.sqlite3`. Kalau cuma `makemigrations` saja tanpa `migrate`, aplikasinya bakal error waktu mencoba query `Photograph.objects.all()` karena tabelnya belum kebentuk di database.

## AI Disclosure

Saya menggunakan Claude Sonnet 4.6 free untuk membantu membuat desain CSS halaman photography beserta responsivitasnya. AI juga membantu menyusun tiga unit test dasar (akses URL dan template, kemunculan data, serta kondisi kosong).

Keputusan konten seperti struktur code template, konsep halaman, dan pemilihan field model (kamera dan lensa apa yang relevan buat ditampilkan, gaya penulisan cerita foto, dan struktur museum-plaque di tampilan) beserta functional core program lainnya pada main/ dan portfolio/ tetap saya tentukan sendiri, begitu juga data dummy yang saya isi lewat Django admin. Saya juga yang menentukan bagaimana halaman Photography ini terhubung secara navigasi dengan section Portfolio statis yang sudah ada di halaman utama dari Tugas 1.