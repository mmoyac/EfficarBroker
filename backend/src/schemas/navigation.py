from pydantic import BaseModel


class MenuItemOut(BaseModel):
    code: str
    label: str
    icon: str | None = None
    ruta: str


class MenuSectionOut(BaseModel):
    code: str
    label: str
    icon: str | None = None
    items: list[MenuItemOut]


class NavigationMenuOut(BaseModel):
    sections: list[MenuSectionOut]
