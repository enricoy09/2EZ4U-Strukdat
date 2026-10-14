# 2EZ4U — Laporan Proyek Struktur Data

Repositori: <https://github.com/enricoy09/2EZ4U-Strukdat>

## 1. Deskripsi Umum

**2EZ4U** adalah engine *delivery service* mini (seperti GoFood/GrabFood versi
sederhana) yang dibangun sebagai proyek mata kuliah **Struktur Data & Analisa
Algoritma (EC234303)**. Tujuannya bukan mengejar tampilan, melainkan
memperlihatkan alur sebuah **struktur data dan algoritma buatan sendiri** —
kapan ia cepat, kapan ia lambat, dan mengapa.

Aplikasi terdiri atas tiga lapis, persis seperti pola yang diminta soal:

| Lapis | Isi | Keterangan |
| --- | --- | --- |
| Data | `data/pesanan.csv` | 200.000 pesanan (header + 200.000 baris) |
| Backend | `backend/*.py` | struktur data & algoritma buatan sendiri, satu berkas per milestone |
| Frontend | `frontend/ui.py` | satu jendela Tkinter yang memanggil backend dan memperlihatkan alurnya |

Setiap pesanan punya kolom: `oid`, `pelanggan`, `resto`, `menu`, `harga`,
`prioritas` (1 = VIP, 2 = Prioritas, 3 = Reguler), `t_masuk_detik`,
`t_selesai_detik` (kosong bila belum selesai), dan `status`
(`DONE` / `CANCEL` / `ANTRE`). Dari 200.000 baris, **19.850** berstatus
`ANTRE`.

**Aturan main yang dipatuhi di seluruh kode backend:**

- Tidak memakai fungsi bawaan sekali pakai: `dict`, `set`, `sorted`, `.sort()`,
  `heapq`, `bisect`, `collections.*`, literal `{}`, maupun *comprehension*
  dict/set.
- Yang dipakai hanya: **list sebagai array primitif**, **tuple**, aritmetika,
  I/O, serta OOP kelas sendiri.
- Setiap berkas backend **hanya berisi struktur data/algoritmanya**. Semua
  logika pemanggilan, parsing, dan tampilan ada di `frontend/ui.py`.

Antarmuka memakai Tkinter: daftar menu di kiri, form parameter dan hasil di
kanan, panel **COMMAND** di bawah yang mencatat setiap aksi beserta waktu
eksekusinya.

## 2. Cara Menjalankan

**Prasyarat:** Python 3 (diuji pada Python 3.10) dengan Tkinter — keduanya
umumnya sudah terpasang bersama Python. **Tidak ada paket pihak ketiga** yang
perlu di-`pip install`.

```bash
# dari dalam folder proyek
python3 app.py
```

Bila ingin memakai berkas CSV lain:

```bash
python3 app.py data/pesanan.csv
```

Cara pakai aplikasi:

1. Klik salah satu menu di panel kiri (mis. `SORT - MERGE SORT`).
2. Isi parameter di form kanan (mis. kunci `oid`, jumlah `4000`).
3. Klik **Jalankan**. Hasil muncul di panel kanan; rincian waktu dan jumlah
   operasi tercatat di panel **COMMAND** bawah.

Saat dibuka, aplikasi otomatis membaca 200.000 baris ke `Array` dan
`LinkedList` sekaligus (sekitar 1,6 detik), lalu mengisi kedua antrean M2.

## 3. Struktur Repositori

```
2EZ4U-Strukdat/
|-- README.md                <- laporan ini
|-- app.py                   <- titik masuk: "python3 app.py"
|-- data/
|   ‘-- pesanan.csv          <- 200.000 pesanan
|-- backend/
|   |-- m1_pesanan.py        <- M1: Array + Node + LinkedList
|   |-- m2_antrean.py        <- M2: Stack + NaiveQueue + CircularQueue
|   ‘-- m3_laporan.py        <- M3: insertion_sort, merge_sort, linear_search, binary_search
‘-- frontend/
    ‘-- ui.py                <- satu jendela Tkinter + seluruh logika aplikasi
```

## 4. Penjelasan Modul

### 4.1 M1 — `backend/m1_pesanan.py`: Array vs Linked List

Modul ini menyimpan data pesanan yang **sama** pada dua struktur sekaligus,
sehingga keduanya bisa diadu langsung di layar.

| Kelas | Isi |
| --- | --- |
| `Array` | larik dinamis: `get(i)`, `insert(i, v)`, `remove(i)`, plus `_grow()` |
| `Node` | simpul: menyimpan nilai dan alamat simpul berikutnya |
| `LinkedList` | rantai simpul dengan penunjuk `tail`: `get(i)`, `insert(i, v)`, `remove(i)` |

Keduanya melayani operasi yang persis sama, yang membedakan hanyalah biayanya.
Array menghitung alamat secara langsung, sehingga `get` O(1), tetapi setiap
penyisipan/pencabutan di tengah harus **menggeser** isi. Linked List sebaliknya:
tidak ada yang digeser, tetapi untuk mencapai posisi ke-i ia harus
**menelusuri** simpul satu per satu.

Biaya penyisipan menurut tiga jenis pesanan:

| Aksi | Arti di aplikasi | Array | Linked List |
| --- | --- | --- | --- |
| Lihat pesanan ke-i | buka detail satu pesanan | O(1) | O(n) |
| Tambah REGULER | masuk barisan paling belakang | O(1) amortized | O(1) (lewat `tail`) |
| Tambah PRIORITAS | menyerobot ke tengah (`size // 2`) | O(n) geser | O(n) telusur |
| Tambah VIP | langsung ke urutan pertama | O(n) geser seluruh isi | O(1) ubah satu penunjuk |
| Hapus pesanan ke-i | mencabut pesanan | O(n) geser | O(n) telusur |

Array tumbuh dengan **menggandakan kapasitas** saat penuh. Penyalinan O(n) itu
jarang terjadi (sekali setiap kapasitas berlipat), sehingga biaya rata-ratanya
tetap O(1) *amortized*. Kalau salah menyalin setiap kali, app akan menjadi
O(n²) saat memuat data.

### 4.2 M2 — `backend/m2_antrean.py`: Stack & Antrean

Tiga kelas, masing-masing berdiri di atas array primitif:

| Kelas | Operasi | Sifat |
| --- | --- | --- |
| `Stack` | `push`, `pop`, `peek`, `is_empty`, `size` | LIFO — untuk kasir (postfix) dan undo/redo |
| `NaiveQueue` | `enqueue`, `dequeue`, `enqueue_front`, `dequeue_back`, `size` | FIFO di atas larik biasa |
| `CircularQueue` | sama seperti `NaiveQueue`, plus `capacity` dan `_grow` | FIFO melingkar (modulo) |

**Postfix.** Struk `( 3 * 12000 ) + ( 2 * 8500 ) - 5000` ditulis dalam infix.
Komputer menghitungnya lewat dua tahap yang sama-sama memakai stack: ubah dulu
ke postfix (`3 12000 * 2 8500 * + 5000 -`), lalu evaluasi. Saat evaluasi, yang
keluar pertama adalah operand **kanan**, jadi untuk `-` dan `/` urutan
`pop()` harus benar (b ≠ a) atau hasilnya salah tanpa pesan galat.

**Naif vs melingkar.** Antrean naif mengambil elemen depan dengan memindahkan
seluruh sisa isi (setara `pop(0)`), O(n) per layanan. Antrean melingkar cukup
memajukan penunjuk `front` dengan modulo, O(1). Keduanya disimpan berdampingan
di UI supaya selisihnya terbaca langsung — mis. satu `dequeue` pada 19.852
pesanan menggeser ~19.850 elemen di versi naif tetapi **0** di versi melingkar.

**Undo/redo.** Setiap aksi yang mengubah keadaan di-push ke `Stack` undo
beserta informasi untuk membalikkannya. `undo` menjalankan kebalikannya dan
memindahkannya ke `Stack` redo; `redo` mengerjakan ulang aksi aslinya. Aksi
baru **mengosongkan redo**, karena setelah beberapa kali undo riwayatnya akan
bercabang bila tidak.

**Kenapa ada `count`?** Bila hanya menyimpan `front` dan `rear`, keadaan
kosong dan penuh sama-sama menghasilkan `front == rear` dan tidak bisa
dibedakan. Penghitung `count` yang eksplisit menyelesaikannya.

### 4.3 M3 — `backend/m3_laporan.py`: Empat Algoritma

Berkas ini berisi empat fungsi murni yang bekerja di atas list primitif dan
mengembalikan **jumlah perbandingan** (bukan hanya waktu), karena jumlah
perbandingan adalah angka yang sama di komputer siapa pun dan itulah yang
membuktikan O(n²) versus O(n log n).

| Fungsi | Kembalian | Kompleksitas | Sifat |
| --- | --- | --- | --- |
| `insertion_sort(data, kunci)` | `(banding, pindah)` | O(n²), O(n) bila hampir terurut | **stabil**, bekerja di tempat |
| `merge_sort(data, kunci)` | `(hasil, banding, pindah)` | O(n log n) | **stabil** |
| `linear_search(data, target, kunci)` | `(indeks, banding)` | O(n) | data boleh berantakan |
| `binary_search(data, target, kunci)` | `(indeks, banding)` | O(log n) | menuntut data terurut |

**Insertion sort** meniru cara merapikan kartu: ambil elemen berikutnya, geser
ke kiri melewati elemen yang lebih besar. Stabil berarti dua data berkunci sama
tetap mempertahankan urutan aslinya — dalam kode, syarat geser memakai `>`
bukan `>=`.

**Merge sort** membelah data sampai tersisa satu elemen lalu menggabungkannya
kembali. Dua jebakan yang dihindari: (1) sisa salah satu bagian **ikut
disalin** setelah perulangan utama berhenti, dan (2) syarat pembandingan
memakai `<=` agar bagian kiri selalu didahulukan sehingga stabil.

**Binary search** tiap langkah membuang separuh sisa kemungkinan. Karena itu
daftar harus terurut menurut kunci yang dicari. Pada kunci yang berbeda,
daftar terurut lama **tidak sah** dan harus dibangun ulang.

Contoh hasil nyata dari antarmuka (data asli 200.000 baris):

- `SORT - INSERTION SORT` 10 baris kunci harga: **24 perbandingan**; terlihat
  `O-000002` dan `O-000009` sama-sama Rp 11.000 dan tetap berurutan seperti
  asalnya (bukti stabil).
- `SORT - MERGE SORT` 4.000 baris kunci oid: **23.728 perbandingan** dan
  **47.904 pemindahan**.
- `SEARCH - LINEAR SEARCH` mencari `O-137442`: **137.442 perbandingan**,
  ditemukan di indeks 137.441.
- `SEARCH - BINARY SEARCH` target yang sama cukup **17 perbandingan**. Namun
  sebelumnya daftar terurut oid harus dibangun sekali dengan merge sort
  (**1.730.048 perbandingan**).

#### Alasan memilih tiap algoritma

- **Insertion sort** untuk data kecil atau hampir terurut; sederhana dan
  bilamana data hampir terurut ia nyaris O(n).
- **Merge sort** untuk data besar, karena O(n log n)-nya tidak bergantung pada
  kondisi awal data.
- **Linear search** bila pencarian hanya sekali-sekali, karena mengurutkan
  lebih mahal daripada satu kali penelusuran.
- **Binary search** bila datanya sudah terurut dan dicari berkali-kali.

## 5. Hasil Pengukuran: n vs Jumlah Perbandingan

Diukur pada potongan data asli, kunci `harga`:

| n | Insertion sort | (× lipatan) | Merge sort | (× lipatan) |
| ---: | --- | ---: | --- | ---: |
| 500 | 55.847 | — | 3.829 | — |
| 1.000 | 233.802 | 4,19× | 8.650 | 2,26× |
| 2.000 | 962.430 | 4,12× | 19.240 | 2,22× |
| 4.000 | 3.831.520 | 3,98× | 42.355 | 2,20× |

Waktu (ms) untuk pengukuran yang sama:

| n | Insertion sort | Merge sort |
| ---: | ---: | ---: |
| 500 | 38,1 | 4,5 |
| 1.000 | 119,2 | 9,6 |
| 2.000 | 433,1 | 17,8 |
| 4.000 | 1.728,4 | 35,0 |

**Grafik perbandingan (panjang batang proporsional):**

```
Insertion sort
   n=500   #
   n=1000  ###
   n=2000  #############
   n=4000  ##################################################

Merge sort
   n=500   #####
   n=1000  ##########
   n=2000  #######################
   n=4000  ##################################################
```

Polanya jelas: begitu **n dilipatduakan**, perbandingan insertion sort menjadi
sekitar **4×** (kuadratik), sedangkan merge sort hanya sekitar **2×**
(log-linear). Pada data yang sama, linear search memakai puluhan ribu kali
lebih banyak perbandingan daripada binary search (137.442 berbanding 17).

## 6. Catatan Penting

- **Insertion sort menolak data besar.** Karena O(n²), menu insertion sort
  menolak masukan di atas **5.000 baris** dengan pesan galat, bukan membeku.
- **Daftar terurut oid di-cache.** Binary search memerlukan daftar terurut oid.
  Daftar itu dibangun **sekali saja** dengan merge sort lalu dipakai ulang,
  sehingga pencarian berikutnya nyaris instan (mis. 1.763 ms sekali di awal,
  kemudian ~0 ms). Cache otomatis dibuang saat data berubah (tambah, hapus,
  atau muat ulang).
- **Array dan Linked List selalu sinkron.** Setiap aksi M1 dikerjakan pada
  kedua struktur; bila ada selisih `oid`, aplikasi melempar galat alih-alih
  diam-diam tidak konsisten.
- **Antrean naif dan melingkar selalu sinkron.** Keduanya diisi dari data yang
  sama dan diuji tetap sama panjang setelah seluruh rangkaian aksi.
- **Semua aksi tercatat.** Panel COMMAND menyimpan perintah, modul, jumlah
  operasi, dan waktunya, sehingga pengukuran bisa diperiksa ulang.