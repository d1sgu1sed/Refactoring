from Src.reposity import reposity
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Core.validator import validator, argument_exception, operation_exception
import os
import json
from inspect import getfullargspec
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model

# Ошибка конвертации данных из json в класс
class convertation_exception(Exception):
    pass 

class start_service:
    __repo_keys= {
        'categories': reposity.group_key(),
        'ranges': reposity.range_key(),
        'nomenclatures': reposity.nomenclature_key(),
        'composition': reposity.composition_key()
    }
    __models_dict = {
        'categories': group_model,
        'ranges': range_model,
        'nomenclatures': nomenclature_model,
        'composition': receipt_item_model
    }
    __classes_property = {}

    # Репозиторий
    __repo: reposity = reposity()

    # Рецепт по умолчанию
    __default_receipt: receipt_model

    # Словарь который содержит загруженные и инициализованные инстансы нужных объектов
    # Ключ - id записи, значение - abstract_model
    __default_receipt_items = {}

    # Наименование файла (полный путь)
    __full_file_name:str = ""

    def __init__(self):
        self.__repo.initalize()
        for item in self.__models_dict.values():
            properties = []
            for name in dir(item):
                attribute = getattr(item, name)
                if isinstance(attribute, property):
                    properties.append(attribute)
            self.__classes_property[item] = [attr for attr in dir(item) if isinstance(getattr(item, attr), property)]

    # Singletone
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(start_service, cls).__new__(cls)
        return cls.instance 

    # Текущий файл
    @property
    def file_name(self) -> str:
        return self.__full_file_name

    # Полный путь к файлу настроек
    @file_name.setter
    def file_name(self, value:str):
        validator.validate(value, str)
        full_file_name = os.path.abspath(value)        
        if os.path.exists(full_file_name):
            self.__full_file_name = full_file_name.strip()
        else:
            raise argument_exception(f'Не найден файл настроек {full_file_name}')

    # Загрузить настройки из Json файла
    def load(self) -> bool:
        if self.__full_file_name == "":
            raise operation_exception("Не найден файл настроек!")

        try:
            with open( self.__full_file_name, 'r') as file_instance:
                settings = json.load(file_instance)

                if "default_receipt" in settings.keys():
                    data = settings["default_receipt"]
                    return self.convert(data)

            return False
        except:
            return False
        
    # TODO: Внимание! Все методы __convert можно сделать универсально
 
    """
    Конвертирует данные из JSON в объекты моделей
    """
    def __convert(self, data: dict, dict_key: str) -> bool:
        # Валидация входных параметров
        if not self.__validate_convert_inputs(data, dict_key):
            return False
        
        model_class = self.__models_dict[dict_key]
        items_data = data[dict_key]
        
        # Обрабатываем каждый элемент данных
        for item_data in items_data:
            if not self.__process_single_item(item_data, model_class, dict_key):
                return False
        
        return True

    """
    Проверяет корректность входных данных для конвертации
    """
    def __validate_convert_inputs(self, data: dict, dict_key: str) -> bool:
        if not isinstance(data, dict):
            return False
        
        if dict_key not in self.__models_dict:
            return False
        
        if dict_key not in data:
            return False
        
        return True

    """
    Обрабатывает один элемент данных и создает объект модели
    """
    def __process_single_item(self, item_data: dict, model_class: type, dict_key: str) -> bool:
        try:
            # Подготавливаем аргументы для создания модели
            args = self.__prepare_model_arguments(item_data)
            
            # Извлекаем ID если есть
            item_id = item_data.get('id')
            
            # Создаем модель
            model_instance = self.__create_model_instance(model_class, args, item_id)
            if not model_instance:
                return False
            
            # Сохраняем модель
            self.__store_model_instance(model_instance, dict_key)
            return True
            
        except Exception:
            return False

    """
    Подготавливает аргументы для создания модели
    """
    def __prepare_model_arguments(self, item_data: dict) -> list:
        args = []
        
        for key, value in item_data.items():
            if key == 'id':
                continue  # ID обрабатывается отдельно
                
            processed_value = self.__process_argument_value(key, value, item_data)
            args.append(processed_value)
        
        return args

    """
    Обрабатывает значение аргумента, подставляя ссылки на объекты при необходимости
    """
    def __process_argument_value(self, key: str, value: any, item_data: dict) -> any:
        if isinstance(value, str) and 'id' in key.lower() and value in self.__default_receipt_items:
            return self.__default_receipt_items[value]
        
        return value

    """
    Создает экземпляр модели с проверкой аргументов
    """
    def __create_model_instance(self, model_class: type, args: list, item_id: str = None):
        try:
            # Получаем ожидаемые аргументы конструктора
            expected_args = getfullargspec(model_class.create).args
            
            """
            Проверяем соответствие количества аргументов.
            
            Добавлено специально, чтобы обработать случай, когда 
            пользователь не добавил необходимый аргумент для создания объекта модели
            """
            if len(args) != len(expected_args):
                return None
            
            # Создаем модель
            model_instance = model_class.create(*args)
            
            # Устанавливаем ID если предоставлен
            if item_id is not None:
                model_instance.unique_code = item_id
                
            return model_instance
            
        except Exception:
            return None

    """
    Сохраняет созданный экземпляр модели в репозиторий
    """
    def __store_model_instance(self, model_instance, dict_key: str):

        self.__default_receipt_items[model_instance.unique_code] = model_instance
        
        # Добавляем в соответствующий репозиторий
        repo_key = self.__repo_keys[dict_key]
        self.__repo.data[repo_key].append(model_instance)

    # TODO: Внимание! Тут нужно проверки добавить и обработку исключений чтобы возвращать False

    """
    Конвертирует данные JSON в объекты моделей и создает рецепт
    """
    def convert(self, data: dict) -> bool:
        validator.validate(data, dict)
        
        try:
            # Основной поток конвертации
            return self.__perform_conversion_pipeline(data)
            
        except Exception as e:
            print(f"Ошибка при конвертации данных: {e}")
            raise convertation_exception(f"Ошибка конвертации: {e}")

    """
    Выполняет последовательность шагов конвертации
    """
    def __perform_conversion_pipeline(self, data: dict) -> bool:
        conversion_steps = [
            lambda: self.__create_receipt_from_data(data),
            lambda: self.__convert_model_data(data),
            lambda: self.__build_receipt_composition(),
            lambda: self.__store_final_receipt()
        ]
        
        for step in conversion_steps:
            if not step():
                return False
                
        return True

    """
    Создает рецепт из данных
    """
    def __create_receipt_from_data(self, data: dict) -> bool:
        try:
            self.__default_receipt = receipt_model.create(
                data.get('name', 'НЕИЗВЕСТНО'),
                data.get('cooking_time', ''),
                int(data.get('portions', 0))
            )
            
            # Добавляем шаги приготовления
            steps = [step.strip() for step in data.get('steps', []) if step.strip()]
            self.__default_receipt.steps.extend(steps)
            
            return True
        except Exception:
            return False

    """
    Конвертирует данные всех моделей
    """
    def __convert_model_data(self, data: dict) -> bool:
        for model_key in self.__models_dict.keys():
            if not self.__convert(data, model_key):
                return False
        return True

    """
    Добавляет ингредиенты в рецепт
    """
    def __build_receipt_composition(self) -> bool:
        try:
            composition = self.__repo.data[reposity.composition_key()]
            self.__default_receipt.composition.extend(composition)
            return True
        except Exception:
            return False

    """
    Сохраняет финальный рецепт
    """
    def __store_final_receipt(self) -> bool:
        try:
            receipt_key = reposity.receipt_key()
            self.__repo.data[receipt_key].append(self.__default_receipt)
            return True
        except Exception:
            return False

    """
    Стартовый набор данных
    """
    @property
    def data(self):
        return self.__repo.data   

    """
    Основной метод для генерации эталонных данных
    """
    def start(self):
        self.file_name = "settings.json"
        result = self.load()
        if result == False:
            raise operation_exception("Невозможно сформировать стартовый набор данных!")
        


