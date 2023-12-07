from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QTransform, QImage
from PyQt5.QtWidgets import QFileDialog
import numpy as np


class MyWidget:

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transformation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rotation INTEGER,
                brightness INTEGER,
                sharpness INTEGER
            )
        ''')
        self.conn.commit()

    def open(self): #открытие картинки
        image_path, _ = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '', 'Картинка (*.jpg);;Картинка (*.png)')

        if image_path:
            self.original_image = QImage(image_path)
            pixmap = QPixmap.fromImage(self.original_image)

            # Scale the image to fit the label while maintaining its aspect ratio
            scaled_pixmap = pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.image.setPixmap(scaled_pixmap)
            self.image.setAlignment(Qt.AlignCenter)

    def export(self):  #экспорт картинки
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Image', '',
                                                   'PNG(*.png);; JPG(*.jpg *.jpeg)')  # открываем проводник для экспорта изображения
        if file_path:  # если выбран путь, сохраняем изображение, если нет ничего не происходит
            pixmap = self.image.pixmap()
            pixmap.save(file_path)

    def rotate_run(self): #поворот картинки
        if self.original_image is not None:
            # Поворачиваем оригинальное изображение
            transform = QTransform().rotate(self.rotation)
            rotated_image = self.original_image.transformed(transform, Qt.SmoothTransformation)

            # Сохраняем измененное изображение
            self.current_image = rotated_image

            # Конвертируем повернутое изображение в QPixmap и масштабируем его для соответствия QLabel
            rotated_pixmap = QPixmap.fromImage(rotated_image)
            scaled_pixmap = rotated_pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Отображаем повернутое и масштабированное изображение в QLabel
            self.image.setPixmap(scaled_pixmap)
            self.image.setAlignment(Qt.AlignCenter)

            # Обновляем значение поворота и добавляем его в историю
            self.rotation += self.rot
            self.add_to_history(rotation=self.rotation)

    def change_brightness(self, value): #общая функция изменения яркости
        if self.current_image is not None:
            # Применяем изменение яркости к текущему изображению
            adjusted_image = self.apply_brightness(self.current_image, value)

            # Отображаем откорректированное изображение в QLabel
            self.image.setPixmap(adjusted_image)

            # Добавляем изменение яркости в историю
            self.add_to_history(brightness=value)

    def apply_brightness(self, image, value): #изменение яркости
        # Применяем изменение яркости к изображению
        working_image = image.copy()
        width = working_image.width()
        height = working_image.height()
        ptr = working_image.bits()
        ptr.setsize(height * width * 4)
        image_array = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        # Convert QImage to NumPy array
        # image_array = np.array(working_image)

        if image_array.ndim == 3:  # Check if the array is 3-dimensional
            if value >= 0:
                # Extract RGB channels and apply brightness
                image_array[:, :, :3] = np.clip(image_array[:, :, :3] + value * (value / 255), 0, 255)
            else:
                image_array[:, :, :3] = np.clip(image_array[:, :, :3] + value, 0, 255)

        else:
            # If the array is not 3-dimensional, assume it is 1-dimensional
            image_array = np.clip(image_array + value, 0, 255)

        # Convert NumPy array back to QImage
        return self.image_from_array(image_array)

    def image_from_image(self, image):
        # Конвертируем изображение в QPixmap и масштабируем его для соответствия QLabel
        pixmap = QPixmap.fromImage(image)
        return pixmap.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def image_from_array(self, image_array):
        # Конвертируем NumPy массив в QImage
        height, width, channel = image_array.shape
        bytes_per_line = 4 * width
        q_image = QImage(image_array.data, width, height, bytes_per_line, QImage.Format_RGB32)
        return self.image_from_image(q_image)

    def add_to_history(self, rotation=None, brightness=None, sharpness=None, shortcut=None): # добалвение в бд
        if shortcut == "ctrl + z":
            # Add the transformation to the history with the specified shortcut
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO transformation_history (rotation, brightness, sharpness, shortcut)
                VALUES (?, ?, ?, ?)
            ''', (rotation, brightness, sharpness, shortcut))
            self.conn.commit()
        else:
            # Add the transformation to the history without a specified shortcut
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO transformation_history (rotation, brightness, sharpness)
                VALUES (?, ?, ?)
            ''', (rotation, brightness, sharpness))
            self.conn.commit()

    def get_last_transformation(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM transformation_history ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()

        if result:
            transformation_data = {
                'id': result[0],
                'rotation': result[1],
                'brightness': result[2],
                'sharpness': result[3]
            }

            return transformation_data
        else:
            return None

    def remove_last_transformation(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM transformation_history WHERE id = (SELECT MAX(id) FROM transformation_history)')
        self.conn.commit()
