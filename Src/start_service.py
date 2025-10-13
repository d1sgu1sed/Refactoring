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
    def __convert(self, data: dict, dict_key: str):
        validator.validate(dict_key, str)
        if dict_key not in self.__models_dict.keys():
            return False
        
        validator.validate(data, dict)
        if dict_key not in data.keys():
            return False

        for items in data[dict_key]:
            args = []
            model = self.__models_dict[dict_key]
            for item in items:
                value = None
                if item not in items.keys():
                    if item.find('id') == -1:
                        value = None
                    elif item.find('value') == -1:
                        value = 1
                    else:
                        value = ''
                else:
                    if item.find('id') != -1 and items[item] in self.__default_receipt_items:
                        value = self.__default_receipt_items[items[item]]
                    else:
                        value = items[item]
                args.append(value)

            id = None
            if 'id' in items.keys():
                id = args.pop(len(args) - 1)

            func_args = getfullargspec(model.create).args
            if len(args) != len(func_args):
                return False
            model = model.create(*args)

            if id is not None:
                model.unique_code = id
            self.__default_receipt_items.setdefault(model.unique_code, model)
            self.__repo.data[self.__repo_keys[dict_key]].append(model)
        
        return True

    # TODO: Внимание! Тут нужно проверки добавить и обработку исключений чтобы возвращать False

    # Обработать полученный словарь    
    def convert(self, data: dict) -> bool:
        validator.validate(data, dict)

        # 1 Созданим рецепт
        cooking_time = data.get('cooking_time', '')
        portions = int(data.get('portions', 0))
        name = data.get('name', 'НЕИЗВЕСТНО')
        self.__default_receipt = receipt_model.create(name, cooking_time, portions)

        # Загрузим шаги приготовления
        steps = data.get('steps', [])
        for step in steps:
            if step.strip() != "":
                self.__default_receipt.steps.append( step )

        # Загружаем данные для моделей из json  
        for key in self.__models_dict.keys():
            if not self.__convert(data, key):
                raise convertation_exception(f'Ошибка при конвертации модели {key}')

        # Добавляем в рецепт ингридиенты
        for item in self.__repo.data[reposity.composition_key()]:
            self.__default_receipt.composition.append(item)
            
        # Сохраняем рецепт
        self.__repo.data[reposity.receipt_key()].append(self.__default_receipt)
        return True

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
        


