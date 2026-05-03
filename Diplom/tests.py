
import io
import json
import os
import time
import unittest
from unittest.mock import MagicMock

os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/audio", exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Тесты хэширования паролей
# ─────────────────────────────────────────────────────────────────────────────

class TestPasswordUtils(unittest.TestCase):

    def setUp(self):
        from utils import get_password_hash, verify_password
        self.hash_fn = get_password_hash
        self.verify_fn = verify_password

    def test_hash_differs_from_plain(self):
        """Хэш не равен исходному паролю."""
        self.assertNotEqual(self.hash_fn("secret"), "secret")

    def test_verify_correct_password(self):
        """Верный пароль проходит проверку."""
        h = self.hash_fn("correctpass")
        self.assertTrue(self.verify_fn("correctpass", h))

    def test_verify_wrong_password(self):
        """Неверный пароль не проходит проверку."""
        h = self.hash_fn("correctpass")
        self.assertFalse(self.verify_fn("wrongpass", h))

    def test_hash_is_string(self):
        """Хэш является строкой."""
        self.assertIsInstance(self.hash_fn("pass"), str)

    def test_hash_is_long_enough(self):
        """Хэш bcrypt длиннее 20 символов."""
        self.assertGreater(len(self.hash_fn("pass123")), 20)

    def test_same_password_different_hashes(self):
        """Два хэша одного пароля отличаются (bcrypt salt)."""
        h1 = self.hash_fn("password")
        h2 = self.hash_fn("password")
        self.assertNotEqual(h1, h2)

    def test_empty_password_hashes(self):
        """Пустая строка тоже хэшируется без ошибок."""
        h = self.hash_fn("")
        self.assertTrue(self.verify_fn("", h))

    def test_unicode_password(self):
        """Юникодный пароль хэшируется корректно."""
        h = self.hash_fn("пароль123")
        self.assertTrue(self.verify_fn("пароль123", h))


# ─────────────────────────────────────────────────────────────────────────────
# Тесты сохранения файлов
# ─────────────────────────────────────────────────────────────────────────────

class TestSaveFile(unittest.TestCase):

    def setUp(self):
        from utils import save_file
        self.save = save_file

    def test_none_returns_none(self):
        """None вместо файла → None."""
        self.assertIsNone(self.save(None, "images"))

    def test_empty_filename_returns_none(self):
        """Файл с пустым именем → None."""
        mock = MagicMock()
        mock.filename = ""
        self.assertIsNone(self.save(mock, "images"))

    def test_valid_image_returns_path(self):
        """Валидный файл возвращает путь /uploads/images/..."""
        mock = MagicMock()
        mock.filename = "photo.jpg"
        mock.file = io.BytesIO(b"fake image data")
        result = self.save(mock, "images")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("/uploads/images/"))

    def test_extension_preserved(self):
        """Расширение файла сохраняется."""
        mock = MagicMock()
        mock.filename = "clip.mp3"
        mock.file = io.BytesIO(b"audio bytes")
        result = self.save(mock, "audio")
        self.assertTrue(result.endswith(".mp3"))

    def test_audio_folder_in_path(self):
        """Аудио-файл попадает в папку audio."""
        mock = MagicMock()
        mock.filename = "sound.wav"
        mock.file = io.BytesIO(b"wave data")
        result = self.save(mock, "audio")
        self.assertIn("/uploads/audio/", result)

    def test_unique_filenames(self):
        """Два одинаковых файла получают разные имена (UUID)."""
        def make_mock():
            m = MagicMock()
            m.filename = "image.png"
            m.file = io.BytesIO(b"data")
            return m
        r1 = self.save(make_mock(), "images")
        r2 = self.save(make_mock(), "images")
        self.assertNotEqual(r1, r2)


# ─────────────────────────────────────────────────────────────────────────────
# Запуск и запись результатов в JSON
# ─────────────────────────────────────────────────────────────────────────────

def run_tests_to_json(output_path: str = "test_results.json"):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))

    results_list = []
    total_start = time.time()

    for test_case in suite:
        for test in test_case:
            start = time.time()
            result = unittest.TestResult()
            test.run(result)
            elapsed = round(time.time() - start, 4)

            test_id = test.id()
            class_name = test_id.split(".")[-2]
            method_name = test_id.split(".")[-1]
            doc = (getattr(test, "_testMethodDoc") or "").strip()

            if result.wasSuccessful():
                status, error = "PASSED", None
            elif result.failures:
                status, error = "FAILED", result.failures[0][1]
            else:
                status, error = "ERROR", result.errors[0][1]

            results_list.append({
                "class": class_name,
                "test": method_name,
                "description": doc,
                "status": status,
                "duration_sec": elapsed,
                "error": error,
            })

    total_time = round(time.time() - total_start, 4)
    passed = sum(1 for r in results_list if r["status"] == "PASSED")
    failed = sum(1 for r in results_list if r["status"] == "FAILED")
    errors = sum(1 for r in results_list if r["status"] == "ERROR")

    report = {
        "summary": {
            "total": len(results_list),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total_duration_sec": total_time,
        },
        "tests": results_list,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Вывод в консоль
    print(f"\n{'='*52}")
    print(f"  Результаты тестирования")
    print(f"{'='*52}")
    for r in results_list:
        icon = "✅" if r["status"] == "PASSED" else "❌"
        print(f"  {icon} {r['class']}.{r['test']}  ({r['duration_sec']}s)")
        if r["error"]:
            first_line = r["error"].strip().splitlines()[-1]
            print(f"       → {first_line}")
    print(f"{'='*52}")
    print(f"  Итого: {passed} пройдено / {failed + errors} провалено"
          f"  [{total_time}s]")
    print(f"  Результаты сохранены: {output_path}")
    print(f"{'='*52}\n")

    return report


if __name__ == "__main__":
    run_tests_to_json()
