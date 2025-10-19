from Src.Core.entity_model import entity_model
from Src.Core.validator import validator

"""
Модель группы номенклатуры
"""
class group_model(entity_model):
    @staticmethod
    def create(name: str):
        validator.validate(name, str, 50)
        item = group_model()
        item.name = name
        return item

    
    

    


    
