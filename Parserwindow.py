import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np
import cv2
import config
import asyncio
import os
import threading
class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yandex Image Downloader")

        # Путь к папке с изображениями
        self.image_path = tk.StringVar(value=config.IMAGE_PATH)
        self.max_count = tk.IntVar(value=config.MAX_COUNT)
        self.desired_size = tk.IntVar(value=config.DESIRED_SIZE)

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Путь к папке с изображениями
        tk.Label(self.root, text="Путь к папке с изображениями:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.image_path, width=50).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self.root, text="Выбрать папку", command=self.select_image_path).grid(row=0, column=2, padx=10, pady=5)

        # Максимальное количество изображений
        tk.Label(self.root, text="Максимальное количество изображений:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.max_count, width=10).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Размер выходных изображений
        tk.Label(self.root, text="Размер выходных изображений:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.desired_size, width=10).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Кнопка запуска
        tk.Button(self.root, text="Начать загрузку", command=self.start_download).grid(row=3, column=0, columnspan=3, padx=10, pady=20)

        # Кнопка форматирования
        tk.Button(self.root, text="Форматировать изображения", command=self.format_images).grid(row=4, column=0, columnspan=3, padx=10, pady=20)

        # Кнопка закрытия
        tk.Button(self.root, text="Закрыть", command=self.root.quit).grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Ожидание запуска...")
        self.status_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    def select_image_path(self):
        path = filedialog.askdirectory(title="Выберите папку с изображениями")
        if path:
            self.image_path.set(path)
        return path

    def update_status(self, message):
        self.status_label.config(text=f"Статус: {message}")
        self.root.update_idletasks()

    def start_download(self):
        image_path = self.image_path.get()
        config.IMAGE_PATH = image_path
        max_count = self.max_count.get()
        config.MAX_COUNT = max_count
        desired_size = self.desired_size.get()
        config.DESIRED_SIZE = desired_size

        self.update_status("Загрузка изображений...")

        # Запуск обработки изображений в отдельном потоке
        threading.Thread(target=self.run_async_tasks, daemon=True).start()

    def run_async_tasks(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        import parser

        try:
            # Запуск основной функции обработки изображений
            asyncio.run(parser.process_images(parser.image_dict, parser.TARGET_FOLDER))
            self.update_status("Загрузка завершена")
            messagebox.showinfo("Информация", f"Загрузка завершена\nПуть: {config.TARGET_FOLDER}\n")
        except Exception as e:
            self.update_status("Ошибка загрузки")
            messagebox.showerror("Ошибка", f"Произошла ошибка при загрузке изображений: {e}")
        finally:
            loop.close()

    def format_images(self):
        image_path = self.image_path.get()
        config.IMAGE_PATH = image_path

        # Создание целевой папки с префиксом
        target_folder = self.create_target_folder()
        config.TARGET_FOLDER = target_folder

        # Копирование структуры директорий
        self.copy_directory_structure(config.IMAGE_PATH, config.TARGET_FOLDER)

        self.update_status("Форматирование изображений...")

        # Запуск обработки изображений в отдельном потоке
        threading.Thread(target=self.process_format, args=(config.IMAGE_PATH, config.TARGET_FOLDER), daemon=True).start()

    def create_target_folder(self):
        last_folder_name = os.path.basename(os.path.normpath(config.IMAGE_PATH))
        parent_directory = os.path.dirname(os.path.normpath(config.IMAGE_PATH))

        suffix = 1
        new_directory_name = f"{last_folder_name}_formatted_{suffix}"
        new_directory_path = os.path.join(parent_directory, new_directory_name)

        while os.path.exists(new_directory_path):
            suffix += 1
            new_directory_name = f"{last_folder_name}_formatted_{suffix}"
            new_directory_path = os.path.join(parent_directory, new_directory_name)

        os.makedirs(new_directory_path)
        print(f"Директория '{new_directory_path}' успешно создана.")
        return new_directory_path

    def copy_directory_structure(self, source_dir, target_dir):
        for root_dir, dirs, _ in os.walk(source_dir):
            # Относительный путь к папке
            rel_path = os.path.relpath(root_dir, source_dir)
            target_path = os.path.join(target_dir, rel_path)

            # Создаем соответствующую папку в целевой директории
            if not os.path.exists(target_path):
                os.makedirs(target_path)

    def process_format(self, source_dir, target_dir):
        try:
            for root_dir, _, files in os.walk(source_dir):
                # Относительный путь к папке
                rel_path = os.path.relpath(root_dir, source_dir)
                target_path = os.path.join(target_dir, rel_path)

                # Создаем соответствующую папку в целевой директории
                if not os.path.exists(target_path):
                    os.makedirs(target_path)

                for file in files:
                    if file.lower().endswith('.jpg'):
                        source_file_path = os.path.join(root_dir, file)
                        target_file_path = os.path.join(target_path, file)

                        self.resize_and_format_image(source_file_path, target_file_path)

            self.update_status("Форматирование завершено")
            messagebox.showinfo("Информация", f"Форматирование завершено\nПуть: {target_dir}\n")
        except Exception as e:
            self.update_status("Ошибка форматирования")
            messagebox.showerror("Ошибка", f"Произошла ошибка при форматировании: {e}")

    def resize_and_format_image(self, source_path, target_path):
        try:
            desired_size = self.desired_size.get()
            image = Image.open(source_path)
            image = image.convert("RGB")  # Убеждаемся, что изображение в RGB

            # Определяем старый и новый размеры изображения
            old_size = image.size  # (ширина, высота)
            ratio = float(desired_size) / max(old_size)
            new_size = tuple([int(x * ratio) for x in old_size])
            image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Создаем новое изображение с указанным размером и заполняем его
            delta_w = desired_size - new_size[0]
            delta_h = desired_size - new_size[1]
            left, right = delta_w // 2, delta_w - (delta_w // 2)
            top, bottom = delta_h // 2, delta_h - (delta_h // 2)

            new_image = Image.new("RGB", (desired_size, desired_size))
            new_image.paste(image, (left, top))

            # Заполнение крайними пикселями
            pixels = np.array(new_image)
            if top > 0:
                pixels[:top, :] = pixels[top:top+1, :]
            if bottom > 0:
                pixels[-bottom:, :] = pixels[-bottom-1:-bottom, :]
            if left > 0:
                pixels[:, :left] = pixels[:, left:left+1]
            if right > 0:
                pixels[:, -right:] = pixels[:, -right-1:-right]

            # Сохраняем результат
            new_image = Image.fromarray(pixels)
            new_image.save(target_path)
        except Exception as e:
            print(f"Ошибка при обработке изображения {source_path}: {e}")

# Основная функция запуска Tkinter
def main():
    root = tk.Tk()
    app = ImageDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()