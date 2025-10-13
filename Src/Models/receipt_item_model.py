from Src.Core.abstract_model import abstact_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Core.validator import validator

# Модель элемента рецепта
class receipt_item_model(abstact_model):
    __nomenclature:nomenclature_model
    __range:range_model
    __value:int

    # Фабричный метод
    def create(nomenclature:nomenclature_model, range:range_model,  value:int):
        item = receipt_item_model()
        item.__nomenclature = nomenclature
        item.__range = range
        item.__value = value
        return item


    # TODO: Внимание! Тут нужно добавить свойства
    @property
    def nomenclature(self):
        return self.__nomenclature
    
    @property
    def range(self):
        return self.__range
    
    @property
    def value(self):
        return self.__value
    
    @nomenclature.setter
    def nomeclature(self, value:nomenclature_model):
        validator.validate(value, nomenclature_model)
        self.__nomenclature = value

    @value.setter
    def value(self, other_value:int):
        validator.validate(other_value, int)
        self.__value = other_value

    @range.setter
    def range(self, value: range_model):
        validator.validate(value, range_model)
        self.__range = value