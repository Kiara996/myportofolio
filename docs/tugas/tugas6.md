# Tugas 6

## Pertanyaan Reflektif


1. Jelaskan apa yang dimaksud dengan REST dan mengapa mengembalikan JSON saja belum cukup untuk menyebut sebuah API sebagai RESTful! Jelaskan pula perbedaan `PUT` dan `PATCH` beserta contoh kapan masing-masing sebaiknya digunakan!

Ans: REST adalah gaya arsitektur untuk layanan web yang diperkenalkan Roy Fielding. Intinya, sistem dipandang sebagai kumpulan **resource** (misalnya sebuah pengalaman) yang punya alamat sendiri (URI), lalu klien memanipulasinya lewat **representasi** (JSON) dan **method HTTP** yang maknanya baku. Beberapa batasan (*constraint*) utamanya: client-server, *stateless* (setiap request membawa semua informasi yang dibutuhkan), *cacheable*, *uniform interface*, dan *layered system*.

JSON hanyalah format datanya, bukan arsitekturnya. Di Tugas 5, endpoint `/api/experience/` mengembalikan JSON tetapi belum RESTful. Namanya tunggal dan tidak menunjuk ke satu resource, hanya melayani `GET`, bentuk datanya dibungkus ala" `{"pk": ..., "fields": {...}}`, dan aksi lain berjalan di URL berbentuk kata kerja seperti `/experience/add-ajax/` dan `/experience/<id>/delete/`. Di Tugas 6 polanya diubah menjadi:

`/api/v1/experiences/` dengan method `GET` / `POST` parameter bisa `?title=` dengan respon 200 / 201 
`/api/v1/experiences/<id>/` dengan method `GET` / `PUT` / `PATCH` / `DELETE` berfungsi untuk menampilkan detail / ganti / ubah sebagian / hapus dengan respon 200 / 200 / 200 / 204 
`/api/v1/experiences/<id>/star/` dengan method `POST` berfungsi untuk memberi atau membatalkan star dengan respon 200

URL-nya kata/verb, aksinya ditentukan oleh method HTTP, dan hasilnya dilaporkan lewat kode status yang tepat (201, 204, 400, 403, 404). API saya sendiri belum "REST penuh", saya hanya memakai `SessionAuthentication` (identitas dibawa cookie sesi, bukan token per request) dan belum menyertakan tautan antar-resource (HATEOAS). Jadi lebih tepat disebut REST-style API.

`PUT` dan `PATCH` sama-sama mengubah resource yang sudah ada, bedanya di cakupan:

- **`PUT` mengganti seluruh resource**. Klien harus mengirim semua field yang wajib. Di `api_views.py` ini ditangani lewat `partial=request.method == "PATCH"`, sehingga `PUT {"title": "Sebagian"}` ditolak `400` karena `description` hilang.
- **`PATCH` mengubah sebagian field saja**, field lain dibiarkan. Cocok untuk kasus sehari-hari seperti Editor yang hanya memperbaiki typo judul. Modal edit di halaman Experience memakai `PATCH`, dan jika pengalaman sudah selesai, field `ended_at` dikirim `null` untuk membatalkan tanggal selesai tanpa menyentuh field lain.

2. Jelaskan peran *serializer* pada Django REST Framework! Apa keuntungannya dibandingkan merakit *dictionary* secara manual dengan `JsonResponse` seperti pada Tutorial 05?

Ans: *Serializer* adalah penerjemah dua arah antara objek model Django dan data sederhana (dict/JSON). untuk output `ExperienceSerializer(experience).data` mengubah satu objek `Experience` menjadi dict siap dijadikan JSON. untuk input `ExperienceSerializer(data=request.data)` menerima JSON dari klien, memvalidasinya lewat `is_valid()`, lalu `save()` menyimpannya menjadi objek model. Jadi satu kelas mengurus **representasi, validasi, dan penyimpanan** langsung sekaligus.

Keuntungan serializer dibanding cara merakit rakit dictionary dianaranya:

- **Satu sumber valid.** Contohnya `ModelSerializer` membaca definisi model (tipe field, `max_length`, `choices`, `blank`/`null`). Field `category` otomatis menolak nilai di luar pilihan `EXPERIENCE_CHOICES` dengan `400`, tanpa saya menulis pengecekan sendiri. Kalau model berubah, serializer ikut menyesuaikan, sedangkan dict manual harus diedit satu per satu.
- **Validasi langsung dengan datanya.** Contohnya `validate_title` dan `validate_description` menjalankan `strip_tags` (setara `clean_<field>` di Tugas 5) sehingga aturan yang sama berlaku untuk `POST`, `PUT`, dan `PATCH`, di mana pun serializer dipakai. Dengan `JsonResponse` tidak ada tempat resmi untuk validasi input.
- **Kontrol field yang eksplisit.** Contohnya Daftar `fields` ditulis satu per satu (bukan `"__all__"`), jadi data akun seperti email atau hash password secara teoritical tidak mungkin bocor. `starred_by` sengaja tidak saya masukkan dan hanya `starred_by_names` yang berisi *username*.
- **Counting field pasti read-only.** Contohnya `star_count`, `is_starred`, dan `starred_by_names` memakai `SerializerMethodField`, `is_ongoing` dan `status_display` memakai `ReadOnlyField`, serta `id` dan `started_at` masuk `read_only_fields`. Klien yang mengirim `"star_count": 99` atau `"started_at": "2000-01-01"` akan diabaikan.
- **Konsisten dan mudah diuji.** Contohnya Bentuk respons sama untuk daftar, detail, dan star, serta serializer bisa dites tanpa HTTP. Kalau memakai dict manual, format tanggal, `None`, dan UUID harus ditangani sendiri.

3. Jelaskan perbedaan autentikasi dan otorisasi pada Django REST Framework! Mengapa hak akses harus diperiksa dengan *permission class* di server, bukan hanya dengan menyembunyikan tombol di *template*?

Ans: **Autentikasi** menjawab "who are you?", sedangkan **otorisasi** menjawab "what u can do?". Di DRF hal tersebut dipisah, detailnya sebagai berikut:

- Autentikasi ditangani oleh *authentication class*. `@authentication_classes([SessionAuthentication])` membaca cookie `sessionid`, mencari pengguna terkait, lalu mengisi `request.user`. Kalau tidak ada sesi, `request.user` adalah `AnonymousUser`.
- Otorisasi dikerjakan oleh *permission class*. `IsPortfolioOwnerOrEditorOrReadOnly.has_permission()` melihat `request.user` dan `request.method`, semua dapat menerima `GET`, superuser berwenang atas semua method, anggota grup `Editor` hanya boleh `PUT`/`PATCH`, sisanya ditolak. Endpoint star memakai `IsAuthenticated` dan akun pemberi star selalu `request.user`, tidak pernah dari body request.

Karena `SessionAuthentication` tidak punya header `WWW-Authenticate`, DRF mereturn `403` (bukan `401`) baik untuk pengunjung yang belum login maupun pengguna login yang tidak berhak. Yang pertama gagal di autentikasi, yang kedua lolos autentikasi tetapi gagal otorisasi.

Menyembunyikan tombol di *template* hanya perbaikan tampilan saja, bukan fitur keamanan. Siapa pun bisa membuka DevTools atau memakai `curl`/`fetch` dan mengirim `DELETE /api/v1/experiences/<id>/` langsung ke server. Karena itu pemeriksaan harus ada di server, di tempat semua request wajib lewat. Dalam pengujian, Editor yang memanggil `fetch` `DELETE` dan `POST` secara manual dari konsol tetap mendapat `403` dengan pesan "Only the owner or an editor can change this data.", walau tombol Hapus dan Tambah memang tidak ditampilkan. Memisahkannya ke *permission class* juga membuat aturan hak akses ada di satu tempat, bukan tersebar di `if` di dalam setiap *view*, dan bisa diuji per permission.

4. Jelaskan mengapa permintaan yang mengubah data tetap memerlukan token CSRF ketika API memakai `SessionAuthentication`! Mengapa *test* yang memakai `force_authenticate` tidak cukup untuk membuktikan bahwa perlindungan CSRF berjalan?

Ans: Dengan `SessionAuthentication`, identitas pengguna dibawa oleh **session cookie**, dan browser menempelkan cookie itu **otomatis** pada setiap request ke domain tersebut, termasuk request yang dipicu oleh halaman lain. Contohnya, saat saya login sebagai owner lalu membuka situs palsu, situs itu bisa menyuruh browser saya mengirim `POST`/`DELETE` ke API saya, dan server melihat cookie sesi yang sah sehingga menganggap itu perbuatan saya. Token CSRF menutup celah ini dengan server meminta nilai rahasia di header `X-CSRFToken` yang cocok dengan cookie `csrftoken`. Situs nakal tidak bisa membaca cookie tersebut karena dibatasi *same-origin policy*, jadi tidak bisa membuat header yang valid. Itulah sebabnya `experience.js` selalu mengirim `X-CSRFToken: getCookie('csrftoken')` pada `POST`, `PATCH`, dan `DELETE`, dan view halaman diberi `@ensure_csrf_cookie` supaya cookie itu tersedia untuk pengguna biasa dan Editor juga. (Pengecualiannya autentikasi berbasis token di header tidak rentan CSRF karena tidak dikirim otomatis oleh browser).

`force_authenticate` tidak cukup karena hal tersebut **melewati seluruh proses autentikasi**. DRF langsung memasang pengguna ke `request` tanpa menjalankan `SessionAuthentication.authenticate()`, padahal pengecekan CSRF (`enforce_csrf`) ada di dalam method itu. Selain itu `APIClient` secara bawaan memang tidak menegakkan CSRF. Jadi unit test dengan `force_authenticate` akan tetap hijau walaupun perlindungan CSRF dimatikan. Untuk membuktikannya (`ExperienceCsrfAPITest`) saya memakai `APIClient(enforce_csrf_checks=True)` dan `client.login(...)` agar sesi benar-benar dibuat. Hasilnya: `POST`/`PATCH`/`DELETE` tanpa token mendapat `403` ("CSRF Failed"), token yang salah juga `403`, token yang benar berhasil, dan di semua kasus penolakan isi database dicek tidak berubah.

## AI Disclosure Tugas 6

Tools: Gemini Flash.

Cara penggunaan AI untuk tugas ini saya memperlakukan AI sebagai teman diskusi yang saya tanyai terus-menerus terkait teori dan materi dari django rest framework dan untuk membantu proses pembuatan unittest.

**Keterbatasan AI yang saya temui dan perbaikan manual:**

Sejauh saya gunakan AI memang mengikuti requirement, tapi ada beberapa part yang menurut saya tidak cocok baik dari segi code mauppun style saya sehingga saya sesuaikan lagi dengan style saya. AI sangat membantu saya, tapi untuk style memang belum menemukan 100% yang cocok dan masih butuh finishing akhir dari saya sendiri

**Log percakapan:** https://share.gemini.google/mQT5F6pLvX00
