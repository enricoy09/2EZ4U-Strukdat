"""M2 - Tumpukan (stack) dan Antrean (queue) di atas Larik milik M1.

Tumpukan (stack)  : LIFO. Dipakai kasir (konversi postfix + hitung) dan undo/redo.
AntreanNaif       : queue FIFO di atas Larik; dequeue mengambil indeks 0 sehingga
                    seluruh sisa isi harus digeser. Jumlah geserannya dicatat.
AntreanMelingkar  : queue FIFO berputar dengan penunjuk front/rear dan pencacah
                    count; dequeue hanya memajukan front, jadi O(1) tanpa geseran.

Keputusan kasus penuh: AntreanMelingkar TUMBUH (kapasitas digandakan) alih-alih
menolak, supaya jumlah pesanan yang dimuat tidak dibatasi ukuran awal.

File ini hanya berisi kelas struktur datanya; alur kasir postfix, undo/redo, dan
penyelarasan kedua antrean ada di frontend/ui.py.
"""

from backend.m1_pesanan import Array


class Tumpukan:
    """Stack LIFO di atas Array. push / pop / peek / kosong."""

    def __init__(self, kapasitas_awal=4):
        self.larik = Array(kapasitas_awal)

    def push(self, x):
        return self.larik.tambah_reguler(x)

    def pop(self):
        if self.larik.size == 0:
            return None
        return self.larik.hapus(self.larik.size - 1)

    def peek(self):
        if self.larik.size == 0:
            return None
        return self.larik.get(self.larik.size - 1)

    def kosong(self):
        return self.larik.size == 0

    def size(self):
        return self.larik.size

    def stat(self):
        return (("kedalaman", self.larik.size),
                ("kapasitas", self.larik.kapasitas))


class AntreanNaif:
    """Queue FIFO di atas Array. dequeue mengambil indeks 0 (geser sisa isi)."""

    def __init__(self, kapasitas_awal=4):
        self.larik = Array(kapasitas_awal)

    def enqueue(self, x):
        return self.larik.tambah_reguler(x)

    def dequeue(self):
        if self.larik.size == 0:
            return None
        return self.larik.hapus(0)

    def enqueue_front(self, x):
        return self.larik.tambah_vip(x)

    def dequeue_back(self):
        if self.larik.size == 0:
            return None
        return self.larik.hapus(self.larik.size - 1)

    def kosong(self):
        return self.larik.size == 0

    def size(self):
        return self.larik.size

    def stat(self):
        return (("panjang", self.larik.size),
                ("kapasitas", self.larik.kapasitas),
                ("total geseran", self.larik.geseran))


class AntreanMelingkar:
    """Queue FIFO melingkar: data, front, rear, count. dequeue O(1)."""

    def __init__(self, kapasitas=4):
        if kapasitas < 1:
            kapasitas = 1
        self.kapasitas = kapasitas
        self.data = [None] * self.kapasitas
        self.front = 0
        self.rear = 0
        self.count = 0
        self.tumbuh = 0

    def kosong(self):
        return self.count == 0

    def penuh(self):
        return self.count == self.kapasitas

    def enqueue(self, x):
        if self.count == self.kapasitas:
            self._tumbuh()
        self.data[self.rear] = x
        self.rear = (self.rear + 1) % self.kapasitas
        self.count += 1

    def dequeue(self):
        if self.count == 0:
            return None
        x = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % self.kapasitas
        self.count -= 1
        return x

    def enqueue_front(self, x):
        if self.count == self.kapasitas:
            self._tumbuh()
        self.front = (self.front - 1) % self.kapasitas
        self.data[self.front] = x
        self.count += 1

    def dequeue_back(self):
        if self.count == 0:
            return None
        self.rear = (self.rear - 1) % self.kapasitas
        x = self.data[self.rear]
        self.data[self.rear] = None
        self.count -= 1
        return x

    def size(self):
        return self.count

    def _tumbuh(self):
        baru = [None] * (self.kapasitas * 2)
        i = 0
        while i < self.count:
            baru[i] = self.data[(self.front + i) % self.kapasitas]
            i += 1
        self.data = baru
        self.kapasitas *= 2
        self.front = 0
        self.rear = self.count
        self.tumbuh += 1

    def stat(self):
        return (("panjang", self.count),
                ("kapasitas", self.kapasitas),
                ("tumbuh", self.tumbuh),
                ("front", self.front),
                ("rear", self.rear))
