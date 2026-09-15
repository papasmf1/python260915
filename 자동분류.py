from pathlib import Path
import shutil


DOWNLOADS_DIR = Path(r"C:\Users\student\Downloads")

FILE_CATEGORIES = {
    "images": {".jpg", ".jpeg", ".png"},
    "data": {".csv", ".xlsx"},
    "docs": {".txt", ".doc", ".pdf"},
    "archive": {".zip", ".exe"},
}


def organize_downloads() -> None:
    """다운로드 폴더의 파일을 확장자별 하위 폴더로 이동한다."""
    for folder_name in FILE_CATEGORIES:
        (DOWNLOADS_DIR / folder_name).mkdir(exist_ok=True)

    for file_path in DOWNLOADS_DIR.iterdir():
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()
        for folder_name, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                destination = DOWNLOADS_DIR / folder_name / file_path.name
                shutil.move(str(file_path), str(destination))
                print(f"이동: {file_path.name} -> {folder_name}")
                break


if __name__ == "__main__":
    organize_downloads()