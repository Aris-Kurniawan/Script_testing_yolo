# classifier.py
# Modul klasifikasi kepadatan (Low / Medium / High)
# Dipakai oleh: yolo_api.py

class DensityClassifier:
    """
    Mengklasifikasikan jumlah orang ke tiga level kepadatan.

    Parameter
    ---------
    n1 : int
        Batas atas level Low  (0 .. n1   orang → Low)
    n2 : int
        Batas atas level Medium (n1+1 .. n2 orang → Medium)
                               (> n2 orang → High)
    """

    def __init__(self, n1: int = 5, n2: int = 10):
        self.n1 = n1
        self.n2 = n2

    def classify(self, count: int) -> str:
        """Return 'Low', 'Medium', atau 'High'."""
        if count <= self.n1:
            return 'Low'
        elif count <= self.n2:
            return 'Medium'
        else:
            return 'High'
