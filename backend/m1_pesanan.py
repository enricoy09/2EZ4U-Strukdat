"""M1 - dua struktur data: Array dan LinkList.

Array     : petak bersambung, alamat ke-i dihitung langsung.
LinkList  : simpul bertaut dengan penunjuk head dan tail (Simpul = simpulnya).

Keduanya melayani operasi yang sama:
  get(i)              lihat nilai ke-i
  tambah_reguler(v)   sisip di belakang
  tambah_prioritas(v) sisip di tengah (size // 2)
  tambah_vip(v)       sisip di depan
  hapus(i)            cabut nilai ke-i

Tiap struktur mencatat ongkos kerjanya (geseran Array, langkah LinkList) supaya
bisa diadu.  File ini hanya berisi kelas struktur datanya.
"""


class Array:
    def __init__(self, kapasitas_awal=4):
        self.kapasitas = kapasitas_awal
        self.size = 0
        self.data = [None] * self.kapasitas
        self.perluasan = 0
        self.geseran = 0
        self.salin = 0

    def _resize(self):
        baru = [None] * (self.kapasitas * 2)
        for i in range(self.size):
            baru[i] = self.data[i]
        self.data = baru
        self.kapasitas *= 2
        self.perluasan += 1
        self.salin += self.size

    def get(self, i):
        if 0 <= i < self.size:
            return self.data[i]
        return None

    def tambah_reguler(self, v):
        if self.size == self.kapasitas:
            self._resize()
        self.data[self.size] = v
        self.size += 1
        return self.size - 1

    def tambah_vip(self, v):
        if self.size == self.kapasitas:
            self._resize()
        for i in range(self.size, 0, -1):
            self.data[i] = self.data[i - 1]
        self.geseran += self.size
        self.data[0] = v
        self.size += 1
        return 0

    def tambah_prioritas(self, v):
        if self.size == self.kapasitas:
            self._resize()
        tengah = self.size // 2
        for i in range(self.size, tengah, -1):
            self.data[i] = self.data[i - 1]
        self.geseran += self.size - tengah
        self.data[tengah] = v
        self.size += 1
        return tengah

    def hapus(self, i):
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
    __slots__ = ("data", "next")

    def __init__(self, data, next=None):
        self.data = data
        self.next = next


class LinkList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        self.langkah = 0

    def get(self, i):
        if i < 0 or i >= self.size:
            return None
        s = self.head
        for _ in range(i):
            s = s.next
            self.langkah += 1
        return s.data

    def tambah_reguler(self, v):
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
        baru = Simpul(v, self.head)
        self.head = baru
        if self.tail is None:
            self.tail = baru
        self.size += 1
        return 0

    def tambah_prioritas(self, v):
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
