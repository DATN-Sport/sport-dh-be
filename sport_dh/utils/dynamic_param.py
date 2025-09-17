from django.utils.datastructures import MultiValueDict


class DynamicQueryParams:
    def __init__(self, query_params: MultiValueDict):
        for key in query_params:
            value = query_params.getlist(key) if len(query_params.getlist(key)) > 1 else query_params.get(key)
            self.__setattr__(key, value)

    def __getattr__(self, name):
        return None

    def __repr__(self):
        return f"<DynamicQueryParams {self.__dict__}>"
    