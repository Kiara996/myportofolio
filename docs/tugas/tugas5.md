### Tugas 5

1. Jelaskan apa itu debouncing dan mengapa teknik ini penting diterapkan pada fitur pencarian yang menggunakan AJAX!

Ans: Debouncing adalah teknik menunda sebuah aksi sampai pengguna benar-benar berhenti melakukan sesuatu selama jeda waktu tertentu. 

Di halaman Experience, pencarian saya dipasangi listener `input` yang jalan di setiap ketikan. Tanpa debouncing, mengetik kata "fotografi" (8 huruf) akan memicu 8 request `fetch()` ke `/api/experience/`, padahal yang dibutuhkan pengguna cuma hasil akhirnya. Dengan debouncing, setiap ketikan me-reset timer lewat `clearTimeout(searchDebounceTimer)`, lalu `setTimeout(searchExperiences, 300)` memasang timer baru. Request baru dikirim kalau pengguna diam selama 300 milidetik, jadi hasilnya cukup 1 request.

Hal ini penting karena pertama, server tidak dibebani query database yang sebenarnya tidak berguna. Kedua, tampilan tidak berkedip-kedip karena daftar terus diganti. Ketiga, ada risiko 'balapan' respons dimana request lama yang lebih lambat bisa saja selesai belakangan dan menimpa hasil pencarian yang terbaru. Untuk itu saya juga memakai `AbortController` yang membatalkan request lama sebelum membuat yang baru, jadi debouncing dan abort bekerja sama.

2. Jelaskan fungsi dari penggunaan await ketika kita menggunakan fetch()! Apa yang akan terjadi jika kita tidak menggunakan await?

Ans: `fetch()` tidak langsung mengembalikan data. Dia mengembalikan sebuah `Promise`, yaitu janji bahwa hasilnya akan datang nanti, karena meminta data ke server butuh waktu. `await` artinya "tunggu sampai antrian ini ditukar jadi data yang sebenarnya (Response) baru lanjut ke baris berikutnya". Jadi halaman tidak ikut membeku selama menunggu server.

Di source code saya ada dua tempat `await`: `await fetch(url, ...)` untuk menunggu respons HTTP datang, dan `await response.json()` untuk menunggu isi respons selesai dibaca dan diurai jadi objek JavaScript.

Kalau `await` tidak dipakai, baris-baris setelahnya langsung jalan padahal datanya belum ada. Variabel `response` isinya masih Promise, bukan Response, sehingga `response.ok` bernilai `undefined` dan pengecekan error jadi salah. Begitu juga `experienceData` akan berupa Promise, sehingga `experienceData.length` jadi `undefined` dan `forEach` melempar error karena Promise bukan array. Selain itu, `try/catch` tidak akan menangkap kegagalan jaringan, karena error-nya terjadi nanti setelah blok `try` sudah selesai dijalankan. Akibatnya state loading, error, dan empty di halaman saya tidak akan tampil dengan benar.

3. Jelaskan apa itu serangan XSS (Cross-Site Scripting) dan mengapa data yang ditampilkan melalui AJAX/JavaScript lebih rentan terhadap serangan ini daripada data yang ditampilkan langsung melalui template Django!

Ans: XSS adalah serangan ketika penyerang berhasil menyelipkan kode JavaScript ke dalam halaman yang kemudian dijalankan di browser korban. Contohnya, penyerang mengisi judul pengalaman dengan `<img src="x" onerror="alert('XSS!')">`. Kalau teks itu masuk ke halaman sebagai HTML mentah, browser akan menganggapnya tag gambar sungguhan, gagal memuat gambar `x`, lalu menjalankan `onerror`. Di serangan sungguhan isinya bukan `alert`, melainkan kode yang mencuri cookie sesi atau melakukan aksi atas nama korban. Karena datanya tersimpan di database dan tampil ke semua pengunjung, ini disebut stored XSS.

Template Django relatif lebih aman karena `{{ experience.title }}` otomatis di-escape: `<` jadi `&lt;`, `>` jadi `&gt;`, `"` jadi `&quot;`. Browser lalu menampilkannya sebagai teks biasa. Perlindungan ini aktif tanpa kita melakukan apa-apa.

Di AJAX, datanya datang sebagai JSON dan saya sendiri yang merakit HTMLnya lewat template string lalu memasukkannya dengan `innerHTML`. Di sini tidak ada auto-escape sama sekali. `innerHTML` menafsirkan seluruh string sebagai HTML, jadi tag yang diselipkan penyerang ikut di run. Pengamannya harus dipasang manual, dan satu saja field yang lupa dibungkus `escapeHtml()` sudah cukup jadi celah. Karena itu di `buildExperienceCardElement` setiap nilai dari JSON (judul, deskripsi, thumbnail, nama pemberi star, bahkan `star_count`) saya bungkus `escapeHtml()`. Alternatif lain yang lebih aman secara bawaan adalah `textContent`, yang selalu memperlakukan isinya sebagai teks.

## AI Disclosure Tugas 5

> Draft. Sesuaikan dengan apa yang benar-benar kamu lakukan, lalu lampirkan tautan chat/log prompt.

Saya menggunakan Claude (isi versi yang dipakai) untuk membantu meninjau kode Tugas 5, menyusun unit test AJAX (`tests_experience_ajax.py`).

Checklist lain pada tugas 5 kali ini saya kerjakan sendiri mengikuti pola tutorial 5 yang ada dan coba saya pisah antara script di html menjadi terpisah sepenuhnya dalam file js dan html sendiri