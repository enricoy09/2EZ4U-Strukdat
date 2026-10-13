"""M1 - Array vs LinkList pada data pesanan.

Dua struktur menyimpan data yang sama persis supaya performanya bisa diadu:
  Array     - petak memori bersambung, alamat ke-i dihitung langsung
  LinkList  - simpul bertaut, penunjuk tail supaya append tetap O(1)

Tiga jenis pesanan -> tiga letak penyisipan:
  REGULER  (3) -> belakang             Array O(1) amortized, LinkList O(1)
  PRIORITAS (2) -> tengah (size // 2)  Array O(n) geser,      LinkList O(n) telusur
  VIP      (1) -> depan                Array O(n) geser,      LinkList O(1)

Lima operasi yang sama dilayani kedua struktur:

  operasi                Array            LinkList
  lihat pesanan ke-i     O(1)             O(n) telusur
  tambah REGULER         O(1) amortized   O(1) pakai tail
  tambah PRIORITAS       O(n) geser       O(n) telusur
  tambah VIP             O(n) geser       O(1) ubah satu petunjuk
  hapus pesanan ke-i     O(n) geser       O(n) telusur

Aturan main: tanpa dict, set, sorted, .sort(), heapq, bisect, collections.*,
literal {}, dan comprehension dict/set. list hanya dipakai sebagai memori
primitif di dalam Array; CSV dibaca mengalir satu baris satu kali.
"""

import csv
import os
import sys
import time

KAPASITAS_AWAL = 4
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

    def __repr__(self):
        return "<Pesanan {0}>".format(self.oid)


class Catatan:
    """Hasil satu operasi: apa yang terjadi dan berapa ongkosnya di tiap struktur."""

    __slots__ = ("aksi", "pesan", "nilai", "indeks",
                 "ms_array", "ms_link", "geseran", "salin", "langkah")

    def __init__(self, aksi, pesan, nilai=None, indeks=-1,
                 ms_array=0.0, ms_link=0.0, geseran=0, salin=0, langkah=0):
        self.aksi = aksi
        self.pesan = pesan
        self.nilai = nilai
        self.indeks = indeks
        self.ms_array = ms_array
        self.ms_link = ms_link
        self.geseran = geseran
        self.salin = salin
        self.langkah = langkah


class Array:
    def __init__(self):
        self.kapasitas = KAPASITAS_AWAL
        self.size = 0
        self.data = [None] * self.kapasitas
        self.perluasan = 0
        self.geseran = 0
        self.salin = 0

    def _resize(self):
        # Saat penuh, alokasikan petak baru 2x lipat dan salin isi lama
        kapasitas_baru = self.kapasitas * 2
        data_baru = [None] * kapasitas_baru
        for i in range(self.size):
            data_baru[i] = self.data[i]
        self.data = data_baru
        self.kapasitas = kapasitas_baru
        self.perluasan += 1
        self.salin += self.size

    def get(self, i):
        # Lihat pesanan ke-i dengan biaya O(1)
        if 0 <= i < self.size:
            return self.data[i]
        return None

    def tambah_reguler(self, v):
        # Masuk barisan paling belakang, O(1) amortized
        if self.size == self.kapasitas:
            self._resize()
        self.data[self.size] = v
        self.size += 1
        return self.size - 1

    def tambah_vip(self, v):
        # Masuk urutan paling depan, butuh pergeseran seluruh isi, O(n)
        if self.size == self.kapasitas:
            self._resize()
        # Geser seluruh elemen ke kanan
        for i in range(self.size, 0, -1):
            self.data[i] = self.data[i - 1]
        self.geseran += self.size
        self.data[0] = v
        self.size += 1
        return 0

    def tambah_prioritas(self, v):
        # Menyerobot ke tengah barisan, butuh pergeseran separuh data, O(n)
        if self.size == self.kapasitas:
            self._resize()
        tengah = self.size // 2
        # Geser elemen dari ujung hingga titik tengah
        for i in range(self.size, tengah, -1):
            self.data[i] = self.data[i - 1]
        self.geseran += self.size - tengah
        self.data[tengah] = v
        self.size += 1
        return tengah

    def hapus(self, i):
        # Pesanan dicabut dari barisan, sisa elemen digeser, O(n)
        if 0 <= i < self.size:
            nilai = self.data[i]
            for j in range(i, self.size - 1):
                self.data[j] = self.data[j + 1]
                self.geseran += 1
            self.data[self.size - 1] = None
            self.size -= 1
            return nilai
        return None

    def stat(self):
        rerata = 0.0
        if self.size:
            rerata = float(self.salin) / float(self.size)
        return (("panjang", self.size),
                ("kapasitas", self.kapasitas),
                ("perluasan", self.perluasan),
                ("geseran", self.geseran),
                ("salin saat perluasan", self.salin),
                ("salin per elemen", round(rerata, 3)))


class Simpul:
    """Satu simpul rantai: nilai + penunjuk ke simpul berikutnya."""

    __slots__ = ("data", "next")

    def __init__(self, data, next=None):
        self.data = data
        self.next = next

    def __repr__(self):
        return "<Simpul {0}>".format(repr(self.data))


class LinkList:
    """Rantai tunggal dengan penunjuk head/tail dan pencacah langkah telusur."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        self.langkah = 0

    def get(self, i):
        # Tidak ada alamat yang bisa dihitung: harus menelusuri simpul, O(n)
        if i < 0 or i >= self.size:
            return None
        s = self.head
        for _ in range(i):
            s = s.next
            self.langkah += 1
        return s.data

    def tambah_reguler(self, v):
        # Cukup menempel di ujung belakang lewat penunjuk tail, O(1)
        baru = Simpul(v)
        if self.tail is None:
            self.head = baru
            self.tail = baru
        else:
            self.tail.next = baru
            self.tail = baru
        self.size += 1
        return self.size - 1

    def tambah_vip(self, v):
        # Hanya mengubah satu petunjuk, O(1)
        baru = Simpul(v, self.head)
        self.head = baru
        if self.tail is None:
            self.tail = baru
        self.size += 1
        return 0

    def tambah_prioritas(self, v):
        # Menelusuri sampai tengah lalu menyambung sekali, O(n)
        tengah = self.size // 2
        baru = Simpul(v)
        if self.size == 0:
            self.head = baru
            self.tail = baru
        elif tengah == 0:
            baru.next = self.head
            self.head = baru
        else:
            sblm = self._sebelum(tengah)
            baru.next = sblm.next
            sblm.next = baru
            if baru.next is None:
                self.tail = baru
        self.size += 1
        return tengah

    def hapus(self, i):
        # Telusuri sampai simpul sebelum i, lalu potong rantai, O(n)
        if i < 0 or i >= self.size:
            return None
        if i == 0:
            dicabut = self.head
            self.head = dicabut.next
            self.langkah += 1
            if self.size == 1:
                self.tail = None
        else:
            sblm = self._sebelum(i)
            dicabut = sblm.next
            sblm.next = dicabut.next
            if dicabut is self.tail:
                self.tail = sblm
        self.size -= 1
        return dicabut.data

    def stat(self):
        return (("panjang", self.size),
                ("simpul ditelusuri", self.langkah))

    def _sebelum(self, i):
        s = self.head
        for _ in range(i - 1):
            s = s.next
            self.langkah += 1
        return s


class AntreanPesanan:
    """Satu antrean, dua struktur: Array dan LinkList selalu dijaga identik.

    Antarmuka di sini 1-based (dipakai jendela Tkinter), sedangkan Array dan
    LinkList 0-based seperti biasa.
    """

    def __init__(self, path=None):
        self.array = Array()
        self.link = LinkList()
        self.path = path
        self.jumlah_muat = 0
        self.nomor_baru = 0

    def panjang(self):
        return self.array.size

    def tengah(self):
        return self.array.size // 2

    def muat_csv(self, path=None, lapor=BARIS_PER_LAPOR):
        if path is None:
            path = self.path
        if path is None:
            raise GalatData("path CSV belum diberikan")
        self.path = path
        awal = time.perf_counter()
        jumlah = 0
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
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
        a, b, ms_array, ms_link, geseran, salin, langkah = self._adu(
            lambda: self.array.get(i), lambda: self.link.get(i))
        if a is None or b is None or a.oid != b.oid:
            raise GalatData("struktur tidak sinkron di indeks {0}".format(i))
        return Catatan("LIHAT no " + str(no), "1 pesanan dibuka", a, i,
                       ms_array, ms_link, geseran, salin, langkah)

    def tambah_reguler(self, pesanan):
        return self._tambah(pesanan, "TAMBAH REGULER", "reguler")

    def tambah_prioritas(self, pesanan):
        return self._tambah(pesanan, "TAMBAH PRIORITAS", "prioritas")

    def tambah_vip(self, pesanan):
        return self._tambah(pesanan, "TAMBAH VIP", "vip")

    def hapus(self, no):
        i = self._ke_indeks(no)
        a, b, ms_array, ms_link, geseran, salin, langkah = self._adu(
            lambda: self.array.hapus(i), lambda: self.link.hapus(i))
        if a is None or b is None or a.oid != b.oid:
            raise GalatData("struktur tidak sinkron saat hapus indeks {0}".format(i))
        return Catatan("HAPUS no " + str(no), a.oid + " dicabut dari antrean",
                       a, i, ms_array, ms_link, geseran, salin, langkah)

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
        geser0, salin0, langkah0 = (self.array.geseran, self.array.salin,
                                    self.link.langkah)
        t0 = time.perf_counter()
        nilai_array = kerja_array()
        ms_array = (time.perf_counter() - t0) * 1000.0
        t0 = time.perf_counter()
        nilai_link = kerja_link()
        ms_link = (time.perf_counter() - t0) * 1000.0
        return (nilai_array, nilai_link, ms_array, ms_link,
                self.array.geseran - geser0, self.array.salin - salin0,
                self.link.langkah - langkah0)

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
        posisi, posisi_link, ms_array, ms_link, geseran, salin, langkah = hasil
        if posisi != posisi_link:
            raise GalatData("kedua struktur memakai posisi berbeda")
        if posisi == 0:
            pesan = pesanan.oid + " masuk di urutan pertama"
        else:
            pesan = pesanan.oid + " masuk di posisi ke-" + str(posisi + 1)
        return Catatan(aksi, pesan, pesanan, posisi,
                       ms_array, ms_link, geseran, salin, langkah)

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


def jalankan_demo(path):
    print("=" * 72)
    print("M1 - ARRAY vs LINKLIST")
    print("=" * 72)
    antrean = AntreanPesanan(path)
    try:
        jumlah, ms = antrean.muat_csv(path)
    except OSError:
        print("Berkas data tidak ditemukan:")
        print("   " + os.path.abspath(path))
        return 1
    except GalatData as galat:
        print("Data tidak bisa dibaca: {0}".format(galat))
        return 1
    print("Terbaca {0} pesanan dalam {1} ms".format(
        format_angka(jumlah), format_angka(ms, 2)))
    print("")

    print("--- 1. LIHAT PESANAN ---")
    for no in (1, jumlah // 2, jumlah):
        try:
            c = antrean.lihat(no)
        except (GalatIndeks, GalatData) as galat:
            print("  no {0} gagal: {1}".format(no, galat))
            continue
        print(_laporan(c))
        if no == 1:
            for baris in c.nilai.detail().split("\n"):
                print("      " + baris)
    print("")

    baru = (
        (antrean.tambah_reguler, Pesanan(antrean.oid_baru(), "Pelanggan Baru",
         "warung-uji", "nasi-goreng", 22000, 3, 0, None, "ANTRE")),
        (antrean.tambah_prioritas, Pesanan(antrean.oid_baru(), "Pelanggan Prioritas",
         "warung-uji", "ayam-bakar", 35000, 2, 0, None, "ANTRE")),
        (antrean.tambah_vip, Pesanan(antrean.oid_baru(), "Pelanggan VIP",
         "warung-uji", "sate-maranggi", 60000, 1, 0, None, "ANTRE")),
    )
    print("--- 2. TAMBAH ---")
    for aksi, pesanan in baru:
        c = aksi(pesanan)
        print(_laporan(c))
        print("      " + c.pesan)
    print("")

    print("--- 3. HAPUS ---")
    try:
        c = antrean.hapus(1)
        print(_laporan(c))
        print("      " + c.pesan)
    except (GalatIndeks, GalatData) as galat:
        print("  hapus gagal: {0}".format(galat))
    print("")

    print("--- 4. CEK KONSISTENSI ---")
    benar, pesan = antrean.verifikasi()
    print("  {0}: {1}".format("cocok" if benar else "TIDAK COCOK", pesan))
    print("")

    print("--- 5. STATISTIK STRUKTUR ---")
    for nama, nilai in antrean.stat():
        print("  {0:<28} {1}".format(nama, format_angka(nilai)))
    return 0


def _laporan(c):
    return "{0:<22} array {1} ms | linklist {2} ms | geser {3} | salin {4} | telusur {5}".format(
        c.aksi, format_angka(c.ms_array, 2), format_angka(c.ms_link, 2),
        format_angka(c.geseran), format_angka(c.salin), format_angka(c.langkah))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else CSV_BAWAAN
    return jalankan_demo(path)


if __name__ == "__main__":
    sys.exit(main())