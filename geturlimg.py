import aiohttp
from main import *
import config



# Client ID от Imgur
#CLIENT_ID = 'c610f40746a3ef8'
last_folder_name = os.path.basename(os.path.normpath(config.IMAGE_PATH))
parent_directory = os.path.dirname(os.path.normpath(config.IMAGE_PATH))


# Определение списка имен классов
CLASS_LIST = sorted(os.listdir(config.IMAGE_PATH))

# Определение количества классов
CLASS_COUNT = len(CLASS_LIST)

async def upload_image_to_imgur(session, image_path):
    headers = {
        'Authorization': f'Client-ID {config.CLIENT_ID}',
    }

    with open(image_path, 'rb') as image_file:
        files = {
            'image': image_file.read(),
        }

        async with session.post('https://api.imgur.com/3/upload', headers=headers, data=files) as response:
            if response.status == 200:
                json_response = await response.json()
                image_url = json_response['data']['link']
                return image_url
            else:
                raise Exception(f"Failed to upload image: {response.status}, {response.text}")

async def main(image_paths):
    async with aiohttp.ClientSession() as session:
        tasks = [upload_image_to_imgur(session, image_path) for image_path in image_paths]
        image_urls = await asyncio.gather(*tasks)
        return image_urls
def create_directory(path):
    # Проверка, существует ли папка
    if os.path.exists(path):
        suffix = 1
        new_directory_name = f"{last_folder_name}_{suffix}"
        new_directory_path = os.path.join(parent_directory, new_directory_name)

        # Увеличиваем суффикс, пока не найдем свободное имя
        while os.path.exists(new_directory_path):
            suffix += 1
            new_directory_name = f"{last_folder_name}_{suffix}"
            new_directory_path = os.path.join(parent_directory, new_directory_name)

        # Создаем новую директорию
        os.makedirs(new_directory_path)
        print(f"Директория '{new_directory_path}' успешно создана.")
    else:
        # Если папка не существует, создаем её
        os.makedirs(path)
        print(f"Директория '{path}' успешно создана.")
    return new_directory_path

TARGET_FOLDER = create_directory(os.path.join(parent_directory, last_folder_name))
config.TARGET_FOLDER = TARGET_FOLDER
def copy_directory_structure(source_dir, target_dir):
    # Проход по содержимому исходной папки
    for item in os.listdir(source_dir):
        source_item_path = os.path.join(source_dir, item)

        # Если это папка, создаем такую же папку в целевой директории
        if os.path.isdir(source_item_path):
            target_item_path = os.path.join(target_dir, item)
            if not os.path.exists(target_item_path):
                os.makedirs(target_item_path)
                print(f"Директория '{target_item_path}' успешно создана.")
            else:
                print(f"Директория '{target_item_path}' уже существует.")


copy_directory_structure(config.IMAGE_PATH, TARGET_FOLDER)

# Пример использования


image_paths = []
image_urls =[]


for cls in CLASS_LIST:
    class_path = os.path.join(config.IMAGE_PATH, cls)
    if os.path.exists(class_path) and os.path.isdir(class_path):
        for file_name in os.listdir(class_path):
            file_path = os.path.join(class_path, file_name)
            image_paths.append(file_path)

image_urls = asyncio.run(main(image_paths))
image_dict = dict(zip(image_paths, image_urls))


async def process_images(image_dict, target_folder):
    for linkpath, linkurl in image_dict.items():
        url = f"https://yandex.ru/images/search?source=collections&rpt=imageview&url={linkurl}"
        relative_path = os.path.relpath(linkpath, config.IMAGE_PATH)
        directory_name, file_name = os.path.split(relative_path)
        without_extension = os.path.splitext(file_name)[0]

        # Создание пути
        _path = os.path.join(target_folder, directory_name, without_extension)
        if not os.path.exists(_path):
            os.makedirs(_path)

        await download_images(url, _path, config.MAX_COUNT)
        #print(url)