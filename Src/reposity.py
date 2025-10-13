
"""
Репозиторий данных
"""
class reposity:
    __data = {}

    @property
    def data(self):
        return self.__data
    
    """
    Ключ для единц измерений
    """
    @staticmethod
    def range_key():
        return "range_model"
    

    """
    Ключ для категорий
    """
    @staticmethod
    def group_key():
        return "group_model"
    

    """
    Ключ для номенклатуры
    """
    @staticmethod
    def nomenclature_key():
        return "nomenclature_model"
    

    """
    Ключ для рецептов
    """
    @staticmethod
    def receipt_key():
        return "receipt_model"
    
    """
    Ключ для рецептов
    """
    @staticmethod
    def composition_key():
        return "receipt_item_model"
    

    # TODO: Внимание! Тут можно сделать универсально

    """
    Инициализация
    """
    def initalize(self):
        keys = [key for key in self.__dir__() if key.endswith('_key')]
        for key in keys:
            key_method = getattr(self, key)
            self.__data[ key_method() ] = []
        
    
    
