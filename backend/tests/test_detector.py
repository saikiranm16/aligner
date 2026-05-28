from app.services.pdf_detector import PdfDetector


def test_estimate_columns_detects_two_column_layout() -> None:
    detector = PdfDetector()
    words = [{"x0": 10 + index, "x1": 30 + index} for index in range(20)] + [
        {"x0": 320 + index, "x1": 340 + index} for index in range(20)
    ]
    assert detector._estimate_columns(words, 600) == 2


def test_estimate_columns_detects_single_column_layout() -> None:
    detector = PdfDetector()
    words = [{"x0": 10 + index * 5, "x1": 30 + index * 5} for index in range(30)]
    assert detector._estimate_columns(words, 600) == 1
