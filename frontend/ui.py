"""Antarmuka Tkinter M1 - Array vs LinkList.

Tiga bagian seperti di dokumen: daftar menu di kiri, form parameter dan hasil
di kanan, panel COMMAND di bawah. Setiap aksi mengubah kedua struktur sekaligus
supaya datanya tetap sama, lalu waktu keduanya diperlihatkan agar bisa diadu.
"""

import time
import tkinter as tk
from tkinter import ttk, messagebox

from backend import m1_pesanan

JUDUL = "2EZ4U - M1 Array vs LinkList"

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


class Jendela:
    def __init__(self, root, path):
        self.root = root
        self.path = path
        self.antrean = m1_pesanan.AntreanPesanan(path)
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
        except m1_pesanan.GalatData as galat:
            self._ganti_status("Data tidak bisa dibaca: {0}".format(galat))
            self._catat("GAGAL memuat data: {0}".format(galat), "galat")
            return
        self.ms_muat = ms
        self._ganti_status(
            "dimuat {0} pesanan dalam {1} ms | array kapasitas {2} | linklist {3} simpul".format(
                m1_pesanan.format_angka(jumlah), m1_pesanan.format_angka(ms, 2),
                m1_pesanan.format_angka(self.antrean.array.kapasitas),
                m1_pesanan.format_angka(jumlah)))
        self._catat("MUAT {0} pesanan ke kedua struktur dari {1} [{2} ms]".format(
            m1_pesanan.format_angka(jumlah), self.path,
            m1_pesanan.format_angka(ms, 2)), "modul")

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
        except (m1_pesanan.GalatIndeks, m1_pesanan.GalatData) as galat:
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
                m1_pesanan.format_angka(jumlah), m1_pesanan.format_angka(ms, 2)))
            self._log_pesan("MUAT ULANG {0} pesanan [{1} ms]".format(
                m1_pesanan.format_angka(jumlah), m1_pesanan.format_angka(ms, 2)))
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
                baris.append("  {0:<28} {1}".format(nama, m1_pesanan.format_angka(nilai)))
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
        return m1_pesanan.Pesanan(
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
            m1_pesanan.format_angka(catatan.ms_array, 2),
            m1_pesanan.format_angka(catatan.geseran)))
        self.teks_hasil.insert("end", "LinkList  : {0} ms  (telusur {1} simpul)\n".format(
            m1_pesanan.format_angka(catatan.ms_link, 2),
            m1_pesanan.format_angka(catatan.langkah)))
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
            m1_pesanan.format_angka(catatan.ms_array, 2),
            m1_pesanan.format_angka(catatan.geseran))
        t_link = "LinkList   {0} ms  (telusur {1} simpul)".format(
            m1_pesanan.format_angka(catatan.ms_link, 2),
            m1_pesanan.format_angka(catatan.langkah))
        self.label_array.configure(text=("- " if self.fokus == "array" else "  ") + t_array)
        self.label_link.configure(text=("- " if self.fokus == "link" else "  ") + t_link)

    def _log_operasi(self, label, c):
        self._catat(label, "perintah")
        self._catat("  " + c.pesan, "modul")
        self._catat("  [M1 - array] {0} ms, geser {1} elemen   |   "
                    "[M1 - linklist] {2} ms, telusur {3} simpul".format(
                        m1_pesanan.format_angka(c.ms_array, 2),
                        m1_pesanan.format_angka(c.geseran),
                        m1_pesanan.format_angka(c.ms_link, 2),
                        m1_pesanan.format_angka(c.langkah)), "modul")

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
                m1_pesanan.format_angka(self.antrean.array.size),
                m1_pesanan.format_angka(self.antrean.array.kapasitas),
                m1_pesanan.format_angka(self.antrean.link.size),
                m1_pesanan.format_angka(self.ms_muat, 2)))


def _cari_menu(kode):
    for _, isi in MENU:
        for rek in isi:
            if rek[0] == kode:
                return rek
    return None


def buka(jendela, path):
    app = Jendela(jendela, path)
    return app
