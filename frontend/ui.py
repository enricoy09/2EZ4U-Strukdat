"""Antarmuka Tkinter M1 - Array vs LinkList.

Tiga bagian seperti di dokumen: daftar menu di kiri, form parameter dan hasil
di kanan, panel COMMAND di bawah. Setiap aksi mengubah kedua struktur sekaligus
supaya datanya tetap sama, lalu waktu keduanya diperlihatkan agar bisa diadu.

Backend (backend/m1_pesanan.py) hanya berisi kelas Array dan LinkList; model
pesanan, pembacaan CSV, dan penyelaras kedua struktur ada di file ini.
"""

import csv
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

from backend.m1_pesanan import Array, LinkList

JUDUL = "2EZ4U - M1 Array vs LinkList"
BARIS_PER_LAPOR = 50000

AKAR_PROYEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_BAWAAN = os.path.join(AKAR_PROYEK, "data", "pesanan.csv")

URUTAN_KOLOM = ("oid", "pelanggan", "resto", "menu", "harga",
                "prioritas", "t_masuk", "t_selesai", "status")

ALIAS_KOLOM = (
    ("oid", ("oid", "id", "order_id", "order", "no_pesanan")),
    ("pelanggan", ("pelanggan", "customer", "nama_pelanggan", "pemesan")),
    ("resto", ("resto", "restoran", "restaurant", "merchant", "toko")),
    ("menu", ("menu", "item", "produk", "makanan")),
    ("harga", ("harga", "price", "harga_menu")),
    ("prioritas", ("prioritas", "priority", "kelas")),
    ("t_masuk", ("t_masuk", "t_masuk_detik", "waktu_masuk", "t_masuk_sek")),
    ("t_selesai", ("t_selesai", "t_selesai_detik", "waktu_selesai", "t_selesai_sek")),
    ("status", ("status", "keadaan", "state")),
)

MENU = (
    ("ARRAY", (
        ("A_LIHAT", "ARRAY - LIHAT PESANAN", "lihat", "array", "no",
         "Buka detail satu pesanan. Array O(1) karena alamat dihitung langsung, "
         "LinkList O(n) karena harus menelusuri simpul."),
        ("A_REG", "ARRAY - TAMBAH PESANAN REGULER", "tambah", "array", "reguler",
         "Pesanan reguler masuk barisan paling belakang. Keduanya O(1); Array "
         "hanya sesekali menyalin saat kapasitas berlipat."),
        ("A_PRI", "ARRAY - TAMBAH PESANAN PRIORITAS", "tambah", "array", "prioritas",
         "Pesanan prioritas menyerobot ke tengah (size // 2). Array menggeser "
         "separuh isi, LinkList menelusuri separuh simpul."),
        ("A_VIP", "ARRAY - TAMBAH PESANAN VIP", "tambah", "array", "vip",
         "Pesanan VIP langsung ke urutan pertama. Array menggeser seluruh isi, "
         "LinkList hanya mengubah satu petunjuk."),
        ("A_HAPUS", "ARRAY - HAPUS PESANAN", "hapus", "array", "no",
         "Pesanan dicabut dari barisan. Array menggeser sisa isi, LinkList "
         "menelusuri sampai simpul sebelumnya."),
    )),
    ("LINKED LIST", (
        ("L_LIHAT", "LINKED LIST - LIHAT PESANAN", "lihat", "link", "no",
         "Sama dengan ARRAY - LIHAT PESANAN, tetapi yang disorot waktu LinkList."),
        ("L_REG", "LINKED LIST - TAMBAH PESANAN REGULER", "tambah", "link", "reguler",
         "Menempel di ujung belakang lewat penunjuk tail, O(1) tanpa telusur."),
        ("L_PRI", "LINKED LIST - TAMBAH PESANAN PRIORITAS", "tambah", "link", "prioritas",
         "Menelusuri sampai tengah lalu menyambung sekali, O(n)."),
        ("L_VIP", "LINKED LIST - TAMBAH PESANAN VIP", "tambah", "link", "vip",
         "Mengubah satu petunjuk saja, O(1), tidak ada yang digeser."),
        ("L_HAPUS", "LINKED LIST - HAPUS PESANAN", "hapus", "link", "no",
         "Telusuri sampai simpul sebelum yang dicabut, potong rantai."),
    )),
    ("SISTEM", (
        ("S_MUAT", "MUAT ULANG DATA", "muat", "", "",
         "Baca ulang data/pesanan.csv ke kedua struktur."),
        ("S_CEK", "CEK KONSISTENSI", "cek", "", "",
         "Pastikan Array dan LinkList memuat urutan pesanan yang sama."),
        ("S_STAT", "STATISTIK STRUKTUR", "stat", "", "",
         "Panjang, kapasitas, perluasan, geseran, dan simpul yang ditelusuri."),
        ("S_CUPLIK", "CUPLIKAN 200 PESANAN", "cuplik", "", "",
         "Tampilkan 200 pesanan pertama beserta posisinya."),
    )),
)


class GalatIndeks(IndexError):
    """Indeks di luar jangkauan atau nomor pesanan tidak ada."""


class GalatData(ValueError):
    """Berkas CSV tidak bisa dibaca atau isinya tidak lengkap."""


def format_angka(nilai, desimal=0):
    """1234567 -> '1.234.567'; 0,0234 -> '0,02' (gaya Indonesia)."""
    teks = "{0:.{1}f}".format(float(nilai), desimal)
    bulat, _, pecahan = teks.partition(".")
    potongan = []
    while len(bulat) > 3:
        potongan.insert(0, bulat[-3:])
        bulat = bulat[:-3]
    potongan.insert(0, bulat)
    hasil = ".".join(potongan)
    if pecahan:
        hasil = hasil + "," + pecahan
    return hasil


def rupiah(nilai):
    return "Rp " + format_angka(nilai)


class Pesanan:
    """Satu baris pesanan, sembilan kolom seperti di CSV."""

    __slots__ = ("oid", "pelanggan", "resto", "menu", "harga",
                 "prioritas", "t_masuk", "t_selesai", "status")

    def __init__(self, oid, pelanggan, resto, menu, harga, prioritas,
                 t_masuk, t_selesai, status):
        self.oid = oid
        self.pelanggan = pelanggan
        self.resto = resto
        self.menu = menu
        self.harga = harga
        self.prioritas = prioritas
        self.t_masuk = t_masuk
        self.t_selesai = t_selesai
        self.status = status

    @property
    def jenis(self):
        if self.prioritas == 1:
            return "VIP"
        if self.prioritas == 2:
            return "PRIORITAS"
        return "REGULER"

    def ringkas(self):
        return "{0} | {1:<14} | {2:<13} | {3:<18} | {4:>10} | {5:<9} | {6}".format(
            self.oid, self.pelanggan[:14], self.resto[:13], self.menu[:18],
            format_angka(self.harga), self.jenis, self.status)

    def detail(self):
        selesai = "-" if self.t_selesai is None else str(self.t_selesai) + " dtk"
        return (
            "oid       : {0}\n"
            "pelanggan : {1}\n"
            "resto     : {2}\n"
            "menu      : {3}\n"
            "harga     : {4}\n"
            "prioritas : {5} ({6})\n"
            "t masuk   : {7} dtk\n"
            "t selesai : {8}\n"
            "status    : {9}"
        ).format(self.oid, self.pelanggan, self.resto, self.menu,
                 rupiah(self.harga), self.prioritas, self.jenis,
                 self.t_masuk, selesai, self.status)


class Catatan:
    """Hasil satu operasi: apa yang terjadi dan berapa ongkosnya di tiap struktur."""

    __slots__ = ("aksi", "pesan", "nilai", "indeks",
                 "ms_array", "ms_link", "geseran", "langkah")

    def __init__(self, aksi, pesan, nilai=None, indeks=-1,
                 ms_array=0.0, ms_link=0.0, geseran=0, langkah=0):
        self.aksi = aksi
        self.pesan = pesan
        self.nilai = nilai
        self.indeks = indeks
        self.ms_array = ms_array
        self.ms_link = ms_link
        self.geseran = geseran
        self.langkah = langkah


class AntreanPesanan:
    """Satu antrean, dua struktur: Array dan LinkList selalu dijaga identik.

    Antarmuka di sini 1-based (dipakai jendela Tkinter), Array/LinkList 0-based.
    """

    def __init__(self, path=None):
        self.array = Array()
        self.link = LinkList()
        self.path = path
        self.jumlah_muat = 0
        self.nomor_baru = 0

    def panjang(self):
        return self.array.size

    def muat_csv(self, path=None, lapor=BARIS_PER_LAPOR):
        if path is None:
            path = self.path
        if path is None:
            raise GalatData("path CSV belum diberikan")
        self.path = path
        awal = time.perf_counter()
        jumlah = 0
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            self.array = Array()
            self.link = LinkList()
            probe = f.readline()
            f.seek(0)
            bacaan = csv.reader(f, delimiter=_pemisah(probe))
            try:
                baris_pertama = next(bacaan)
            except StopIteration:
                raise GalatData("CSV kosong: {0}".format(path))
            if _mungkin_header(baris_pertama):
                peta = _petakan_kolom(baris_pertama)
            else:
                peta = _petakan_urutan()
                if _baris_isi(baris_pertama):
                    self._satu_baris(baris_pertama, peta)
                    jumlah += 1
            for baris in bacaan:
                if not _baris_isi(baris):
                    continue
                self._satu_baris(baris, peta)
                jumlah += 1
                if lapor and jumlah % lapor == 0:
                    print("  ... {0} baris termuat".format(format_angka(jumlah)))
        ms = (time.perf_counter() - awal) * 1000.0
        self.jumlah_muat = jumlah
        return jumlah, ms

    def oid_baru(self):
        self.nomor_baru += 1
        return "O-{0:06d}".format(self.jumlah_muat + self.nomor_baru)

    def lihat(self, no):
        i = self._ke_indeks(no)
        a, b, ms_array, ms_link, geseran, langkah = self._adu(
            lambda: self.array.get(i), lambda: self.link.get(i))
        if a is None or b is None or a.oid != b.oid:
            raise GalatData("struktur tidak sinkron di indeks {0}".format(i))
        return Catatan("LIHAT no " + str(no), "1 pesanan dibuka", a, i,
                       ms_array, ms_link, geseran, langkah)

    def tambah_reguler(self, pesanan):
        return self._tambah(pesanan, "TAMBAH REGULER", "reguler")

    def tambah_prioritas(self, pesanan):
        return self._tambah(pesanan, "TAMBAH PRIORITAS", "prioritas")

    def tambah_vip(self, pesanan):
        return self._tambah(pesanan, "TAMBAH VIP", "vip")

    def hapus(self, no):
        i = self._ke_indeks(no)
        a, b, ms_array, ms_link, geseran, langkah = self._adu(
            lambda: self.array.hapus(i), lambda: self.link.hapus(i))
        if a is None or b is None or a.oid != b.oid:
            raise GalatData("struktur tidak sinkron saat hapus indeks {0}".format(i))
        return Catatan("HAPUS no " + str(no), a.oid + " dicabut dari antrean",
                       a, i, ms_array, ms_link, geseran, langkah)

    def potongan(self, mulai=0, jumlah=10):
        n = self.array.size
        if mulai < 0 or mulai > n:
            raise GalatIndeks("mulai {0} di luar jangkauan 0..{1}".format(mulai, n))
        keluar = []
        i = mulai
        while i < n and len(keluar) < jumlah:
            keluar.append(self.array.get(i))
            i += 1
        return keluar

    def verifikasi(self):
        if self.array.size != self.link.size:
            return False, "panjang berbeda: {0} vs {1}".format(
                self.array.size, self.link.size)
        s = self.link.head
        for i in range(self.array.size):
            a = self.array.get(i)
            if a is not s.data:
                return False, "indeks {0} berbeda".format(i)
            s = s.next
        return True, "identik pada {0} posisi".format(self.array.size)

    def stat(self):
        isi = [("jumlah pesanan", self.array.size)]
        for nama, nilai in self.array.stat():
            isi.append(("array. " + nama, nilai))
        for nama, nilai in self.link.stat():
            isi.append(("linklist. " + nama, nilai))
        return isi

    def _adu(self, kerja_array, kerja_link):
        geser0, langkah0 = self.array.geseran, self.link.langkah
        t0 = time.perf_counter()
        nilai_array = kerja_array()
        ms_array = (time.perf_counter() - t0) * 1000.0
        t0 = time.perf_counter()
        nilai_link = kerja_link()
        ms_link = (time.perf_counter() - t0) * 1000.0
        return (nilai_array, nilai_link, ms_array, ms_link,
                self.array.geseran - geser0, self.link.langkah - langkah0)

    def _tambah(self, pesanan, aksi, jenis):
        if jenis == "reguler":
            hasil = self._adu(lambda: self.array.tambah_reguler(pesanan),
                              lambda: self.link.tambah_reguler(pesanan))
        elif jenis == "vip":
            hasil = self._adu(lambda: self.array.tambah_vip(pesanan),
                              lambda: self.link.tambah_vip(pesanan))
        else:
            hasil = self._adu(lambda: self.array.tambah_prioritas(pesanan),
                              lambda: self.link.tambah_prioritas(pesanan))
        posisi, posisi_link, ms_array, ms_link, geseran, langkah = hasil
        if posisi != posisi_link:
            raise GalatData("kedua struktur memakai posisi berbeda")
        if posisi == 0:
            pesan = pesanan.oid + " masuk di urutan pertama"
        else:
            pesan = pesanan.oid + " masuk di posisi ke-" + str(posisi + 1)
        return Catatan(aksi, pesan, pesanan, posisi,
                       ms_array, ms_link, geseran, langkah)

    def _ke_indeks(self, no):
        n = self.array.size
        if n == 0:
            raise GalatIndeks("antrean masih kosong")
        try:
            nomor = int(str(no).strip())
        except ValueError:
            raise GalatIndeks("nomor pesanan bukan angka: {0}".format(no))
        if nomor < 1 or nomor > n:
            raise GalatIndeks("nomor {0} di luar jangkauan 1..{1}".format(nomor, n))
        return nomor - 1

    def _satu_baris(self, baris, peta):
        oid = _ambil(baris, peta[0])
        if not oid:
            return
        pesanan = Pesanan(
            oid,
            _ambil(baris, peta[1]),
            _ambil(baris, peta[2]),
            _ambil(baris, peta[3]),
            _angka(_ambil(baris, peta[4]), 0),
            _angka(_ambil(baris, peta[5]), 3),
            _angka(_ambil(baris, peta[6]), 0),
            _angka(_ambil(baris, peta[7]), None),
            _ambil(baris, peta[8]) or "ANTRE",
        )
        self.array.tambah_reguler(pesanan)
        self.link.tambah_reguler(pesanan)


def _ambil(baris, indeks):
    if indeks < 0 or indeks >= len(baris):
        return ""
    return baris[indeks].strip()


def _angka(teks, bawaan):
    teks = (teks or "").strip()
    if teks == "":
        return bawaan
    try:
        return int(teks)
    except ValueError:
        pass
    try:
        return int(float(teks))
    except ValueError:
        return bawaan


def _baris_isi(baris):
    for s in baris:
        if s.strip():
            return True
    return False


def _pemisah(teks):
    if teks.count(";") > teks.count(","):
        return ";"
    return ","


def _mungkin_header(baris):
    if not baris:
        return False
    awal = baris[0].strip().lower()
    return awal.startswith("oid") or awal.startswith("id")


def _normal(nama):
    return nama.strip().lower().replace(" ", "_").replace("-", "_")


def _petakan_kolom(header):
    normal = []
    for nama in header:
        normal.append(_normal(nama))
    peta = []
    for _, alias in ALIAS_KOLOM:
        ketemu = -1
        for a in alias:
            for i, nama in enumerate(normal):
                if nama == a:
                    ketemu = i
                    break
            if ketemu >= 0:
                break
        if ketemu < 0:
            for _, alias_lain in ALIAS_KOLOM:
                for a in alias_lain:
                    for i, nama in enumerate(normal):
                        if a in nama:
                            ketemu = i
                            break
                    if ketemu >= 0:
                        break
                if ketemu >= 0:
                    break
        peta.append(ketemu)
    if peta[0] < 0:
        raise GalatData("kolom oid tidak ditemukan pada header: " + str(header))
    return peta


def _petakan_urutan():
    peta = []
    for i in range(len(URUTAN_KOLOM)):
        peta.append(i)
    return peta


class Jendela:
    def __init__(self, root, path):
        self.root = root
        self.path = path
        self.antrean = AntreanPesanan(path)
        self.rek_terpilih = None
        self.fokus = ""
        self.entri = []
        self.ms_muat = 0.0

        root.title(JUDUL)
        root.geometry("1200x780")
        root.minsize(1000, 640)

        self._bangun_status()
        self._bangun_command()
        self._bangun_menu()
        self._bangun_kanan()

        self.root.after(150, self.muat_awal)

    # -------------------------------------------------- bangun tata letak
    def _bangun_menu(self):
        self.bingkai = ttk.Frame(self.root, padding=6)
        self.bingkai.pack(side="top", fill="both", expand=True)

        kiri = ttk.LabelFrame(self.bingkai, text="MENU", padding=6)
        kiri.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        self.pohon = ttk.Treeview(kiri, show="tree", height=17, selectmode="browse")
        self.pohon.column("#0", width=300)
        self.pohon.grid(row=0, column=0, sticky="nsew")
        gulir = ttk.Scrollbar(kiri, orient="vertical", command=self.pohon.yview)
        gulir.grid(row=0, column=1, sticky="ns")
        self.pohon.configure(yscrollcommand=gulir.set)

        for grup, isi in MENU:
            self.pohon.insert("", "end", iid="G_" + grup, text=grup, open=True)
            for rek in isi:
                self.pohon.insert("G_" + grup, "end", iid=rek[0], text="  " + rek[1])
        self.pohon.bind("<<TreeviewSelect>>", self.pilih_menu)

        self.kanan = ttk.Frame(self.bingkai)
        self.kanan.grid(row=0, column=1, sticky="nsew")
        self.bingkai.columnconfigure(1, weight=1)
        self.bingkai.rowconfigure(0, weight=1)

    def _bangun_kanan(self):
        self.label_info = ttk.Label(self.kanan, text="Pilih menu di kiri untuk mulai.",
                                    wraplength=760, justify="left",
                                    foreground="#334")
        self.label_info.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.kanan.columnconfigure(0, weight=1)

        self.kotak_form = ttk.LabelFrame(self.kanan, text="PARAMETER", padding=8)
        self.kotak_form.grid(row=1, column=0, sticky="ew")

        self.kotak_hasil = ttk.LabelFrame(self.kanan, text="HASIL", padding=8)
        self.kotak_hasil.grid(row=2, column=0, sticky="nsew", pady=6)
        self.kanan.rowconfigure(2, weight=1)

        self.teks_hasil = tk.Text(self.kotak_hasil, height=10, wrap="none",
                                  font=("DejaVu Sans Mono", 10),
                                  background="#fbfbfb", relief="flat")
        self.teks_hasil.grid(row=0, column=0, sticky="nsew")
        gulir = ttk.Scrollbar(self.kotak_hasil, orient="vertical",
                              command=self.teks_hasil.yview)
        gulir.grid(row=0, column=1, sticky="ns")
        self.teks_hasil.configure(yscrollcommand=gulir.set)
        self.kotak_hasil.columnconfigure(0, weight=1)
        self.kotak_hasil.rowconfigure(0, weight=1)
        self.teks_hasil.tag_configure("kepala", font=("DejaVu Sans Mono", 10, "bold"))
        self.teks_hasil.tag_configure("array", foreground="#1a4fa0",
                                      font=("DejaVu Sans Mono", 10, "bold"))
        self.teks_hasil.tag_configure("link", foreground="#0a7a3d",
                                      font=("DejaVu Sans Mono", 10, "bold"))
        self.teks_hasil.configure(state="disabled")

        self.kotak_adu = ttk.LabelFrame(self.kanan, text="ADU PERFORMA", padding=8)
        self.kotak_adu.grid(row=3, column=0, sticky="ew")
        self.label_array = ttk.Label(self.kotak_adu, text="Array    -")
        self.label_array.grid(row=0, column=0, sticky="w")
        self.label_link = ttk.Label(self.kotak_adu, text="LinkList -")
        self.label_link.grid(row=1, column=0, sticky="w")

    def _bangun_command(self):
        kotak = ttk.LabelFrame(self.root, text="COMMAND", padding=6)
        kotak.pack(side="bottom", fill="x", padx=6, pady=(0, 4))
        self.teks_log = tk.Text(kotak, height=7, wrap="word",
                                font=("DejaVu Sans Mono", 9),
                                background="#1e1e1e", foreground="#dcdcdc",
                                relief="flat")
        self.teks_log.grid(row=0, column=0, sticky="nsew")
        gulir = ttk.Scrollbar(kotak, orient="vertical", command=self.teks_log.yview)
        gulir.grid(row=0, column=1, sticky="ns")
        self.teks_log.configure(yscrollcommand=gulir.set)
        self.teks_log.tag_configure("perintah", foreground="#6fd06f",
                                    font=("DejaVu Sans Mono", 9, "bold"))
        self.teks_log.tag_configure("modul", foreground="#7fb8ff")
        self.teks_log.tag_configure("galat", foreground="#ff7b7b")
        kotak.columnconfigure(0, weight=1)
        kotak.rowconfigure(0, weight=1)

    def _bangun_status(self):
        self.label_status = ttk.Label(self.root, text="Memuat ...", anchor="w",
                                      padding=(8, 3))
        self.label_status.pack(side="bottom", fill="x")

    # -------------------------------------------------- pemuatan data
    def muat_awal(self):
        self._ganti_status("Memuat data dari " + self.path + " ...")
        self.root.update_idletasks()
        try:
            jumlah, ms = self.antrean.muat_csv(self.path)
        except OSError:
            self._ganti_status("Berkas tidak ditemukan: " + self.path)
            self._catat("GAGAL memuat data: Berkas tidak ditemukan", "galat")
            return
        except GalatData as galat:
            self._ganti_status("Data tidak bisa dibaca: {0}".format(galat))
            self._catat("GAGAL memuat data: {0}".format(galat), "galat")
            return
        self.ms_muat = ms
        self._ganti_status(
            "dimuat {0} pesanan dalam {1} ms | array kapasitas {2} | linklist {3} simpul".format(
                format_angka(jumlah), format_angka(ms, 2),
                format_angka(self.antrean.array.kapasitas),
                format_angka(jumlah)))
        self._catat("MUAT {0} pesanan ke kedua struktur dari {1} [{2} ms]".format(
            format_angka(jumlah), self.path,
            format_angka(ms, 2)), "modul")

    # -------------------------------------------------- pilih menu
    def pilih_menu(self, _=None):
        pilihan = self.pohon.selection()
        if not pilihan:
            return
        rek = _cari_menu(pilihan[0])
        if rek is None:
            return
        self.rek_terpilih = rek
        self.fokus = rek[3]
        self.label_info.configure(text=rek[1] + "\n" + rek[5])
        self._bangun_form(rek)

    def _bangun_form(self, rek):
        for anak in self.kotak_form.winfo_children():
            anak.destroy()
        self.entri = []
        mode = rek[4]
        baris = 0
        if mode == "no":
            self._tambah_entri(baris, "no", "Nomor pesanan (1-based)", "100000")
            baris += 1
        elif mode:
            self._tambah_entri(baris, "pelanggan", "pelanggan", "Pelanggan Baru")
            self._tambah_entri(baris + 1, "resto", "resto", "warung-uji")
            self._tambah_entri(baris + 2, "menu", "menu", "nasi-goreng")
            self._tambah_entri(baris + 3, "harga", "harga", "22000")
            baris += 4
        ttk.Button(self.kotak_form, text="JALANKAN", command=self.jalankan).grid(
            row=baris, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.kotak_form.columnconfigure(1, weight=1)
        self.root.bind("<Return>", self._enter)

    def _tambah_entri(self, baris, nama, label, bawaan):
        ttk.Label(self.kotak_form, text=label).grid(row=baris, column=0,
                                                    sticky="w", padx=(0, 8), pady=2)
        w = ttk.Entry(self.kotak_form, width=40)
        w.insert(0, bawaan)
        w.grid(row=baris, column=1, sticky="ew", pady=2)
        self.entri.append((nama, w))

    def _enter(self, _):
        self.jalankan()

    # -------------------------------------------------- jalankan aksi
    def jalankan(self):
        if self.rek_terpilih is None:
            return
        kode, label, aksi, fokus, mode, _ = self.rek_terpilih
        try:
            catatan = self._lakukan(aksi, mode)
        except (GalatIndeks, GalatData) as galat:
            messagebox.showerror("Gagal", str(galat))
            self._catat(label + ": " + str(galat), "galat")
            return
        if catatan is not None:
            self._tampil(catatan)
            self._log_operasi(label, catatan)
        self._perbarui_status()

    def _lakukan(self, aksi, mode):
        if aksi == "muat":
            jumlah, ms = self.antrean.muat_csv(self.path)
            self.ms_muat = ms
            self._tampil_pesan("Data dibaca ulang: {0} pesanan dalam {1} ms".format(
                format_angka(jumlah), format_angka(ms, 2)))
            self._log_pesan("MUAT ULANG {0} pesanan [{1} ms]".format(
                format_angka(jumlah), format_angka(ms, 2)))
            return None
        if aksi == "cek":
            benar, pesan = self.antrean.verifikasi()
            self._tampil_pesan("CEK KONSISTENSI: {0}\n  {1}".format(
                "cocok" if benar else "TIDAK COCOK", pesan))
            self._log_pesan("CEK KONSISTENSI: " + pesan)
            return None
        if aksi == "stat":
            baris = []
            for nama, nilai in self.antrean.stat():
                baris.append("  {0:<28} {1}".format(nama, format_angka(nilai)))
            self._tampil_pesan("STATISTIK STRUKTUR\n" + "\n".join(baris))
            self._log_pesan("STATISTIK STRUKTUR")
            return None
        if aksi == "cuplik":
            daftar = self.antrean.potongan(0, 200)
            baris = ["  {0:>7}. {1}".format(i + 1, p.ringkas())
                     for i, p in enumerate(daftar)]
            self._tampil_pesan("200 PESANAN PERTAMA\n" + "\n".join(baris))
            self._log_pesan("CUPLIKAN 200 PESANAN")
            return None
        if mode == "no":
            no = self._nilai("no")
            if aksi == "lihat":
                return self.antrean.lihat(no)
            return self.antrean.hapus(no)
        pesanan = self._bentuk_pesanan(mode)
        if mode == "reguler":
            return self.antrean.tambah_reguler(pesanan)
        if mode == "vip":
            return self.antrean.tambah_vip(pesanan)
        return self.antrean.tambah_prioritas(pesanan)

    def _bentuk_pesanan(self, mode):
        prioritas = 3
        if mode == "vip":
            prioritas = 1
        elif mode == "prioritas":
            prioritas = 2
        harga_teks = self._nilai("harga")
        try:
            harga = int(harga_teks)
        except ValueError:
            harga = 0
        return Pesanan(
            self.antrean.oid_baru(), self._nilai("pelanggan"), self._nilai("resto"),
            self._nilai("menu"), harga, prioritas, 0, None, "ANTRE")

    def _nilai(self, nama):
        for n, w in self.entri:
            if n == nama:
                return w.get()
        return ""

    # -------------------------------------------------- tampilan hasil
    def _tampil(self, catatan):
        self.teks_hasil.configure(state="normal")
        self.teks_hasil.delete("1.0", "end")
        self.teks_hasil.insert("end", catatan.aksi + "\n", "kepala")
        if catatan.aksi.startswith("LIHAT") and catatan.nilai is not None:
            self.teks_hasil.insert("end", catatan.nilai.detail() + "\n")
        else:
            self.teks_hasil.insert("end", catatan.pesan + "\n")
            if catatan.nilai is not None:
                self.teks_hasil.insert("end", catatan.nilai.ringkas() + "\n")
        self.teks_hasil.insert("end", "\n")
        self.teks_hasil.insert("end", "Array     : {0} ms  (geser {1})\n".format(
            format_angka(catatan.ms_array, 2), format_angka(catatan.geseran)))
        self.teks_hasil.insert("end", "LinkList  : {0} ms  (telusur {1} simpul)\n".format(
            format_angka(catatan.ms_link, 2), format_angka(catatan.langkah)))
        self.teks_hasil.insert("end", "posisi    : ke-{0}\n".format(catatan.indeks + 1))
        self.teks_hasil.configure(state="disabled")
        self._perbarui_adu(catatan)

    def _tampil_pesan(self, teks):
        self.teks_hasil.configure(state="normal")
        self.teks_hasil.delete("1.0", "end")
        self.teks_hasil.insert("end", teks + "\n")
        self.teks_hasil.configure(state="disabled")

    def _perbarui_adu(self, catatan):
        t_array = "Array      {0} ms  (geser {1} elemen)".format(
            format_angka(catatan.ms_array, 2), format_angka(catatan.geseran))
        t_link = "LinkList   {0} ms  (telusur {1} simpul)".format(
            format_angka(catatan.ms_link, 2), format_angka(catatan.langkah))
        self.label_array.configure(text=("- " if self.fokus == "array" else "  ") + t_array)
        self.label_link.configure(text=("- " if self.fokus == "link" else "  ") + t_link)

    def _log_operasi(self, label, c):
        self._catat(label, "perintah")
        self._catat("  " + c.pesan, "modul")
        self._catat("  [M1 - array] {0} ms, geser {1} elemen   |   "
                    "[M1 - linklist] {2} ms, telusur {3} simpul".format(
                        format_angka(c.ms_array, 2), format_angka(c.geseran),
                        format_angka(c.ms_link, 2), format_angka(c.langkah)), "modul")

    def _log_pesan(self, teks):
        self._catat(teks, "modul")

    def _catat(self, teks, tag=None):
        self.teks_log.configure(state="normal")
        stempel = time.strftime("%H:%M:%S")
        self.teks_log.insert("end", stempel + "  " + teks + "\n", tag)
        self.teks_log.see("end")
        self.teks_log.configure(state="disabled")

    def _ganti_status(self, teks):
        self.label_status.configure(text=teks)

    def _perbarui_status(self):
        self._ganti_status(
            "{0} pesanan | array kapasitas {1} | linklist {2} simpul | data dimuat {3} ms".format(
                format_angka(self.antrean.array.size),
                format_angka(self.antrean.array.kapasitas),
                format_angka(self.antrean.link.size),
                format_angka(self.ms_muat, 2)))


def _cari_menu(kode):
    for _, isi in MENU:
        for rek in isi:
            if rek[0] == kode:
                return rek
    return None


def buka(jendela, path):
    app = Jendela(jendela, path)
    return app
