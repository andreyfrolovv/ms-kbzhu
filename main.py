import openfoodfacts
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

app = FastAPI(title="Nutrients API with Full Annotations")

# --- PYDANTIC МОДЕЛИ ДЛЯ АННОТАЦИИ ВСЕЙ СТРУКТУРЫ ОТВЕТА ---

# Разрешаем принимать любые дополнительные поля во вложенных структурах
allow_extra = ConfigDict(extra="allow")


class DataQualityAccuracy(BaseModel):
    model_config = allow_extra
    overall: Optional[str] = None


class DataQualityCompleteness(BaseModel):
    model_config = allow_extra
    general_information: Optional[str] = None
    ingredients: Optional[str] = None
    nutrition: Optional[str] = None
    overall: Optional[str] = None
    packaging: Optional[str] = None


class DataQualityDimensions(BaseModel):
    model_config = allow_extra
    accuracy: Optional[DataQualityAccuracy] = None
    completeness: Optional[DataQualityCompleteness] = None


class AggregatedOrigin(BaseModel):
    model_config = allow_extra
    epi_score: Optional[int] = None
    origin: Optional[str] = None
    percent: Optional[int] = None
    transportation_score: Optional[int] = None


class OriginsOfIngredients(BaseModel):
    model_config = allow_extra
    aggregated_origins: Optional[List[AggregatedOrigin]] = None
    epi_score: Optional[int] = None
    epi_value: Optional[int] = None
    origins_from_categories: Optional[List[str]] = None
    origins_from_origins_field: Optional[List[str]] = None
    transportation_score: Optional[int] = None
    transportation_scores: Optional[Dict[str, int]] = None


class EcoScoreAdjustments(BaseModel):
    model_config = allow_extra
    origins_of_ingredients: Optional[OriginsOfIngredients] = None


class EcoScoreData(BaseModel):
    model_config = allow_extra
    adjustments: Optional[EcoScoreAdjustments] = None


class CategoriesProperties(BaseModel):
    model_config = allow_extra
    agribalyse_proxy_food_code_en: Optional[str] = Field(None, alias="agribalyse_proxy_food_code:en")


# Модель самого продукта из вашего JSON
class OpenFoodFactsProduct(BaseModel):
    model_config = allow_extra

    id: str = Field(..., alias="_id", description="Штрих-код продукта")
    keywords: List[str] = Field(..., alias="_keywords", description="Ключевые слова для поиска")

    brands: Optional[str] = Field(None, description="Бренд товара")
    brands_tags: Optional[List[str]] = None

    categories: Optional[str] = Field(None, description="Категории товара")
    categories_hierarchy: Optional[List[str]] = None
    categories_lc: Optional[str] = None
    categories_tags: Optional[List[str]] = None
    categories_properties: Optional[CategoriesProperties] = None
    category_properties: Optional[Dict[str, Any]] = None

    allergens: Optional[str] = Field(None, description="Аллергены")
    allergens_from_ingredients: Optional[str] = None
    allergens_from_user: Optional[str] = None
    allergens_hierarchy: Optional[List[str]] = None
    allergens_lc: Optional[str] = None
    allergens_tags: Optional[List[str]] = None

    code: str = Field(..., description="Штрих-код")
    codes_tags: Optional[List[str]] = None
    compared_to_category: Optional[str] = None

    complete: Optional[int] = None
    completeness: Optional[float] = None

    countries: Optional[str] = None
    countries_hierarchy: Optional[List[str]] = None
    countries_lc: Optional[str] = None
    countries_tags: Optional[List[str]] = None

    created_t: Optional[int] = None
    creator: Optional[str] = None

    data_quality_bugs_tags: Optional[List[Any]] = None
    data_quality_errors_tags: Optional[List[Any]] = None
    data_quality_info_tags: Optional[List[str]] = None
    data_quality_tags: Optional[List[str]] = None
    data_quality_warnings_tags: Optional[List[str]] = None
    data_quality_completeness_tags: Optional[List[str]] = None
    data_quality_dimensions: Optional[DataQualityDimensions] = None

    data_sources: Optional[str] = None
    data_sources_tags: Optional[List[str]] = None
    debug_param_sorted_langs: Optional[List[str]] = None

    ecoscore_data: Optional[EcoScoreData] = None


# Финальный ответ API
class FoodSearchResponse(BaseModel):
    result: bool = Field(..., description="Статус успешности")
    search_type: str = Field(..., description="Тип произведенного поиска")
    count: int = Field(..., description="Количество найденных элементов")
    data: List[OpenFoodFactsProduct] = Field(..., description="Массив найденных продуктов")


# --- ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ С АННОТАЦИЕЙ ОТВЕТА ---

@app.get("/search-kbzhu", response_model=FoodSearchResponse)
async def search_kbzhu(
        barcode: Optional[str] = Query(None, description="Штрих-код товара"),
        name: Optional[str] = Query(None, description="Название продукта для текстового поиска"),
        page_size: int = Query(2, description="Количество выводимых товаров")
):
    api = openfoodfacts.API(user_agent="MyNutriApp/1.0")

    # ВАРИАНТ 1: Поиск по штрих-коду
    if barcode:
        code_info = api.product.get(barcode)

        if code_info and code_info.get("status"):
            product_raw = code_info.get("product", code_info)
            # Приводим к формату массива для совместимости с моделью FoodSearchResponse
            return FoodSearchResponse(
                result=True,
                search_type="barcode",
                count=1,
                data=[product_raw]
            )

    # ВАРИАНТ 2: Поиск по названию
    elif name:
        search_result = api.product.text_search(name, page_size=page_size)

        if search_result and search_result.get("products"):
            products_list = search_result["products"]
            return FoodSearchResponse(
                result=True,
                search_type="text_name",
                count=search_result.get("count", len(products_list)),
                data=products_list
            )

    # Защитный ответ, если ничего не найдено (возвращает пустой список согласно схеме)
    return FoodSearchResponse(
        result=False,
        search_type="none",
        count=0,
        data=[]
    )