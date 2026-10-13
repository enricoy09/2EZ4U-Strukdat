"""Titik masuk aplikasi 2EZ4U.

Perintah:
  python3 app.py                    membuka jendela Tkinter (M1)
  python3 app.py --terminal         menjalankan M1 di terminal
  python3 app.py --terminal <csv>   memakai berkas CSV lain

Modul m2..m6 menyusul pada milestone berikutnya.
"""

import sys
import tkinter as tk

from backend import m1_pesanan


def main():
    argumen = sys.argv[1:]
    path = m1_pesanan.CSV_BAWAAN
    mode_terminal = False
    for a in argumen:
        if a == "--terminal":
            mode_terminal = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            path = a

    if mode_terminal:
        return m1_pesanan.jalankan_demo(path)

    from frontend import ui
    jendela = tk.Tk()
    ui.buka(jendela, path)
    jendela.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())