Nama: Kevin Fauzan Arjuna
NPM: 2506612266
Kelas: PBP E

# myportofolio

Website portofolio untuk tugas PBP Semester 3, Fakultas Ilmu Komputer UI.

HTML5 + CSS3, isinya:
- **Profile** - bio singkat dan kontak
- **Skills** - tools/bahasa yang dikuasai, dibagi per kategori (Multimedia & Programming)
- **Portfolio** - galeri foto

## Tech Stack

- Django
- HTML5 & CSS3 murni
- Deploy ke [PWS (Pacil Web Service)](https://kevin-fauzan-myportofolio.pws.cs.ui.ac.id)

## Setup

```bash
python -m venv env
env/Scripts/activate #Windows
source env/bin/activate #Unix (macOS, Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Buka `http://localhost:8000/`.

## Struktur Proyek

```
myportofolio/
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── img/
├── portofolio/
└── docs/
    └── tugas/ #Tugas mingguan
```

## Dokumentasi Tugas Mingguan

Jawaban pertanyaan reflektif dan catatan pengerjaan tiap minggu ada di folder `docs/tugas/`, terpisah dari README ini agar lebih rapi.

- [Tugas 1 - Static Web with HTML5 and CSS3](docs/tugas/tugas1.md)

## Deployment

Auto deploy ke PWS pada branch `master`