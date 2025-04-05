import random


class IdUtil:
    _instance = None
    _next_id = 1

    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def get_id():
        instance = IdUtil._get_instance()
        current_id = instance._next_id
        instance._next_id += 1
        return current_id
