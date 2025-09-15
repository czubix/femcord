"""
Copyright 2022-2025 czubix

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

from .enums import ComponentTypes, ButtonStyles, TextInputStyles, PaddingSizes, SelectDefaultValueTypes

from typing import Unpack, Union, Optional, Self, Sequence, TypedDict, NotRequired, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Emoji

class Components(list):
    def __init__(self, *, title: Optional[str] = None, custom_id: Optional[str] = None, components: Optional[Sequence["BaseComponent"]] = None) -> None:
        if title is not None:
            self.title = title
        if custom_id is not None:
            self.custom_id = custom_id
        if components is not None:
            self.extend(components)

    def add_component(self, component: "BaseComponent") -> Self:
        self.append(component)
        return self

class BaseComponentKwargs(TypedDict):
    id: NotRequired[Optional[int]]

class BaseComponent(dict):
    def __init__(self, **kwargs: Unpack[BaseComponentKwargs]) -> None:
        if (_id := kwargs.get("id")):
            self["id"] = _id

    def add_component(self, component: "BaseComponent") -> Self:
        self["components"].append(component)
        return self

class ActionRowKwargs(BaseComponentKwargs):
    components: NotRequired[list[BaseComponent]]

class ActionRow(BaseComponent):
    def __init__(self, **kwargs: Unpack[ActionRowKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.ACTION_ROW.value
        self["components"] = kwargs.get("components", [])

class ButtonKwargs(BaseComponentKwargs):
    style: NotRequired[ButtonStyles]
    label: NotRequired[str]
    emoji: NotRequired["Emoji"]
    custom_id: NotRequired[str]
    sku_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]

class Button(BaseComponent):
    def __init__(self, **kwargs: Unpack[ButtonKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.BUTTON.value
        if (style := kwargs.get("style")):
            self["style"] = style.value
        if (label := kwargs.get("label")):
            self["label"] = label
        if (emoji := kwargs.get("emoji")):
            self["emoji"] = {"id": emoji.id, "name": emoji.name, "animated": emoji.animated}
        if (custom_id := kwargs.get("custom_id")):
            self["custom_id"] = custom_id
        if (sku_id := kwargs.get("sku_id")):
            self["sku_id"] = sku_id
        if (url := kwargs.get("url")):
            self["url"] = url
        if (disabled := kwargs.get("disabled")):
            self["disabled"] = disabled

class StringSelectOptionKwargs(TypedDict):
    label: str
    value: str
    description: NotRequired[str]
    emoji: NotRequired["Emoji"]
    default: NotRequired[bool]

class StringSelectOption(dict):
    def __init__(self, **kwargs: Unpack[StringSelectOptionKwargs]) -> None:
        self["label"] = kwargs["label"]
        self["value"] = kwargs["value"]
        if (description := kwargs.get("description")):
            self["description"] = description
        if (emoji := kwargs.get("emoji")):
            self["emoji"] = {"id": emoji.id, "name": emoji.name, "animated": emoji.animated}
        if (default := kwargs.get("default")):
            self["default"] = default

class StringSelectKwargs(BaseComponentKwargs):
    custom_id: str
    options: NotRequired[list[StringSelectOption]]
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]

class StringSelect(BaseComponent):
    def __init__(self, **kwargs: Unpack[StringSelectKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.SELECT_MENU.value
        self["custom_id"] = kwargs["custom_id"]
        self["options"] = kwargs.get("options", [])
        if (placeholder := kwargs.get("placeholder")):
            self["placeholder"] = placeholder
        if (min_values := kwargs.get("min_values")):
            self["min_values"] = min_values
        if (max_values := kwargs.get("max_values")):
            self["max_values"] = max_values
        if (disabled := kwargs.get("disabled")):
            self["disabled"] = disabled

    def add_option(self, option: StringSelectOption) -> Self:
        self["options"].append(option)
        return self

class TextInputKwargs(BaseComponentKwargs):
    custom_id: str
    style: TextInputStyles
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    required: NotRequired[bool]
    value: NotRequired[str]
    placeholder: NotRequired[str]

class TextInput(BaseComponent):
    def __init__(self, **kwargs: Unpack[TextInputKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.TEXT_INPUT.value
        self["custom_id"] = kwargs["custom_id"]
        self["style"] = kwargs["style"].value
        if (min_length := kwargs.get("min_length")):
            self["min_length"] = min_length
        if (max_length := kwargs.get("max_length")):
            self["max_length"] = max_length
        if (required := kwargs.get("required")):
            self["required"] = required
        if (value := kwargs.get("value")):
            self["value"] = value
        if (placeholder := kwargs.get("placeholder")):
            self["placeholder"] = placeholder

class SelectDefaultValue(TypedDict):
    id: str
    type: SelectDefaultValueTypes

class SelectKwargs(BaseComponentKwargs):
    custom_id: str
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]

class Select(BaseComponent):
    def __init__(self, **kwargs: Unpack[SelectKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["custom_id"] = kwargs["custom_id"]
        if (placeholder := kwargs.get("placeholder")):
            self["placeholder"] = placeholder
        if (default_values := kwargs.get("default_values")):
            self["default_values"] = [default_value["type"].value for default_value in default_values]
        if (min_values := kwargs.get("min_values")):
            self["min_values"] = min_values
        if (max_values := kwargs.get("max_values")):
            self["max_values"] = max_values
        if (disabled := kwargs.get("disabled")):
            self["disabled"] = disabled

    def add_default_value(self, default_value: SelectDefaultValue) -> Self:
        if "default_values" not in self:
            self["default_values"] = []
        self["default_values"].append(default_value)
        return self

class UserSelect(Select):
    def __init__(self, **kwargs: Unpack[SelectKwargs]) -> None:
        super().__init__(**kwargs)

        self["type"] = ComponentTypes.USER_SELECT.value

class RoleSelect(Select):
    def __init__(self, **kwargs: Unpack[SelectKwargs]) -> None:
        super().__init__(**kwargs)

        self["type"] = ComponentTypes.ROLE_SELECT.value

class MentionableSelect(Select):
    def __init__(self, **kwargs: Unpack[SelectKwargs]) -> None:
        super().__init__(**kwargs)

        self["type"] = ComponentTypes.MENTIONABLE_SELECT.value

class ChannelSelect(Select):
    def __init__(self, **kwargs: Unpack[SelectKwargs]) -> None:
        super().__init__(**kwargs)

        self["type"] = ComponentTypes.CHANNEL_SELECT.value

class TextDisplayKwargs(BaseComponentKwargs):
    content: str

class TextDisplay(BaseComponent):
    def __init__(self, **kwargs: Unpack[TextDisplayKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.TEXT_DISPLAY.value
        self["content"] = kwargs["content"]

class UnfurledMediaItem(TypedDict):
    url: str
    proxy_url: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]
    content_type: NotRequired[str]

class MediaItemKwargs(BaseComponentKwargs):
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]

class MediaItem(BaseComponent):
    def __init__(self, **kwargs: Unpack[MediaItemKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["media"] = kwargs["media"]
        if (description := kwargs.get("description")):
            self["description"] = description
        if (spoiler := kwargs.get("spoiler")):
            self["spoiler"] = spoiler

class Thumbnail(MediaItem):
    def __init__(self, **kwargs: Unpack[MediaItemKwargs]) -> None:
        super().__init__(**kwargs)

        self["type"] = ComponentTypes.THUMBNAIL.value

class MediaGalleryKwargs(BaseComponentKwargs):
    items: NotRequired[list[MediaItem]]

class MediaGallery(BaseComponent):
    def __init__(self, **kwargs: Unpack[MediaGalleryKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.MEDIA_GALLERY.value
        self["items"] = kwargs.get("items", [])

    def add_item(self, media_gallery_item: MediaItem) -> Self:
        self["items"].append(media_gallery_item)
        return self

class FileKwargs(BaseComponentKwargs):
    file: UnfurledMediaItem
    spoiler: NotRequired[bool]

class File(BaseComponent):
    def __init__(self, **kwargs: Unpack[FileKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.FILE.value
        self["file"] = kwargs["file"]
        if (spoiler := kwargs.get("spoiler")):
            self["spoiler"] = spoiler

class SectionKwargs(BaseComponentKwargs):
    components: NotRequired[list[BaseComponent]]
    accessory: NotRequired[Union[Button, Thumbnail]]

class Section(BaseComponent):
    def __init__(self, **kwargs: Unpack[SectionKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.SECTION.value
        self["components"] = kwargs.get("components", [])
        self["accessory"] = kwargs.get("accessory", {})

    def set_accessory(self, accessory: BaseComponent) -> Self:
        self["accessory"] = accessory
        return self

class SeparatorKwargs(BaseComponentKwargs):
    divider: NotRequired[bool]
    spacing: NotRequired[PaddingSizes]

class Separator(BaseComponent):
    def __init__(self, **kwargs: Unpack[SeparatorKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.SEPARATOR.value
        if (divider := kwargs.get("divider")):
            self["divider"] = divider
        if (spacing := kwargs.get("spacing")):
            self["spacing"] = spacing.value

class ContainerKwargs(BaseComponentKwargs):
    components: NotRequired[list[BaseComponent]]
    accent_color: NotRequired[int]
    spoiler: NotRequired[bool]

class Container(BaseComponent):
    def __init__(self, **kwargs: Unpack[ContainerKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.CONTAINER.value
        self["components"] = kwargs.get("components", [])
        if (accent_color := kwargs.get("accent_color")):
            self["accent_color"] = accent_color
        if (spoiler := kwargs.get("spoiler")):
            self["spoiler"] = spoiler

class LabelKwargs(BaseComponentKwargs):
    label: str
    description: NotRequired[str]
    component: NotRequired[Union[UserSelect, RoleSelect, MentionableSelect, ChannelSelect, StringSelect, TextInput]]

class Label(BaseComponent):
    def __init__(self, **kwargs: Unpack[LabelKwargs]) -> None:
        super().__init__(id=kwargs.get("id"))

        self["type"] = ComponentTypes.LABEL.value
        self["label"] = kwargs["label"]
        if (description := kwargs.get("description")):
            self["description"] = description
        if (component := kwargs.get("component")):
            self["component"] = component