"""
Copyright 2022-2026 czubix

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Any, _SpecialForm

class AppCommandAttribute:
    def __init__(self, _type: Any, field: str, value: Any) -> None:
        self.fields = {field: value}
        if isinstance(_type, AppCommandAttribute):
            self.type = _type.type
            self.fields |= _type.fields
        else:
            self.type = _type

@_SpecialForm
def Min(self, params: tuple[AppCommandAttribute | str | int | float, int | float]) -> AppCommandAttribute:
    _type, _min = params
    if isinstance(_type, AppCommandAttribute):
        if _type.type is str:
            field = "min_length"
        elif _type.type is int or _type.type is float:
            field = "min_value"
    elif _type is str:
            field = "min_length"
    elif _type is int or _type is float:
        field = "min_value"
    return AppCommandAttribute(_type, field, _min)

@_SpecialForm
def Max(self, params: tuple[AppCommandAttribute | str | int | float, int | float]) -> AppCommandAttribute:
    _type, _max = params
    if isinstance(_type, AppCommandAttribute):
        if _type.type is str:
            field = "max_length"
        elif _type.type is int or _type.type is float:
            field = "max_value"
    elif _type is str:
            field = "max_length"
    elif _type is int or _type is float:
        field = "max_value"
    return AppCommandAttribute(_type, field, _max)

@_SpecialForm
def Autocomplete(self, _type: Any) -> AppCommandAttribute:
    return AppCommandAttribute(_type, "autocomplete", True)