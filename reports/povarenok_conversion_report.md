# Povarenok Conversion Report

## Source

- Input: `C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv`
- Output: `C:\Projects\ai-food-family\exports\povarenok_planam_raw.jsonl`
- Report: `C:\Projects\ai-food-family\reports\povarenok_conversion_report.md`
- Dry run: `True`
- Detected encoding: `utf-8`
- Encoding candidates: `utf-8, utf-8-sig, cp1251, windows-1251, latin1`

## Summary

- Total rows: `100`
- Converted: `100`
- Skipped: `0`
- Duplicates: `0`
- Ingredients parsed: `708`
- Ingredients unparsed: `160`

## JSONL Examples

### Example 1

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/80338/", "title": "Рулет мясной с крабовыми палочками", "ingredients": [{"name": "Фарш мясной", "quantity": "700", "unit": "г", "raw": "700 г"}, {"name": "Лук репчатый", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Чеснок", "quantity": "1", "unit": "зуб.", "raw": "1 зуб."}, {"name": "Специи", "quantity": "0.5", "unit": "ч. л.", "raw": "0,5 ч. л."}, {"name": "Крабовые палочки", "quantity": "250", "unit": "...
```

### Example 2

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/157553/", "title": "Постная дрожжевая лепёшка", "ingredients": [{"name": "Мука пшеничная", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Сахар", "quantity": "05", "unit": "ч. л.", "raw": "05 ч. л."}, {"name": "Соль", "quantity": "05", "unit": "ч. л.", "raw": "05 ч. л."}, {"name": "Дрожжи", "quantity": "05", "unit": "ч. л.", "raw": "05 ч. л."}, {"name": "Вода", "quantity": "100", "unit": "мл", "raw": ...
```

### Example 3

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/66825/", "title": "Черничный пирог", "ingredients": [{"name": "Мука пшеничная", "quantity": "250", "unit": "мл", "raw": "250 мл"}, {"name": "Желток яичный", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Сахар", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Масло сливочное", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Вода", "quantity": "2", "unit": "ст. л.", "raw": "2 ст. л."}, ...
```

### Example 4

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/157466/", "title": "Жареные пирожки с мясом", "ingredients": [{"name": "Вода", "quantity": "625", "unit": "мл", "raw": "625 мл"}, {"name": "Мука пшеничная", "quantity": "600", "unit": "г", "raw": "600 г"}, {"name": "Соль", "quantity": "2", "unit": "ч. л.", "raw": "2 ч. л."}, {"name": "Сахар", "quantity": "1", "unit": "ст. л.", "raw": "1 ст. л."}, {"name": "Масло растительное", "quantity": "2", "unit": "ст. л.", "raw"...
```

### Example 5

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/150260/", "title": "Картофельный салат по-американски", "ingredients": [{"name": "Картофель", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Яблоко", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Сельдерей черешковый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Тунец", "quantity": "1", "unit": "бан.", "raw": "1 бан."}, {"name": "Майонез", "quantity": null, "unit": null, "raw": "по в...
```

### Example 6

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/123901/", "title": "Суп \"Грибное лукошко\"", "ingredients": [{"name": "Масло растительное", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л."}, {"name": "Грибы", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Шампиньоны", "quantity": "150", "unit": "г", "raw": "150 г"}, {"name": "Картофель", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Морковь", "quantity": "1", "unit": "шт", "raw": "1 шт"...
```

### Example 7

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/140280/", "title": "Пасхальный кулич с творогом", "ingredients": [{"name": "Молоко", "quantity": "125", "unit": "мл", "raw": "125 мл"}, {"name": "Дрожжи", "quantity": "21", "unit": "г", "raw": "21 г"}, {"name": "Сахар", "quantity": "160", "unit": "г", "raw": "160 г"}, {"name": "Мука пшеничная", "quantity": "1/2", "unit": "ст. л.", "raw": "1/2 ст. л."}, {"name": "Яйцо куриное", "quantity": "1", "unit": "шт", "raw": "1...
```

### Example 8

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/171463/", "title": "Салат с морской капустой", "ingredients": [{"name": "Перец болгарский", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Тыква", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Капуста морская", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Зелень", "quantity": "1", "unit": "пуч.", "raw": "1 пуч."}, {"name": "Хлебцы", "quantity": null, "unit": null, "raw": null}], "...
```

### Example 9

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/135926/", "title": "Гренки по-новому", "ingredients": [{"name": "Сливки", "quantity": "200", "unit": "мл", "raw": "200 мл"}, {"name": "Хлеб", "quantity": null, "unit": null, "raw": "по вкусу"}, {"name": "Яйцо куриное", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Сыр сливочный", "quantity": "150", "unit": "г", "raw": "150 г"}, {"name": "Сироп фруктовый", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л....
```

### Example 10

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/115122/", "title": "Кекс \"Воздушный шоколад\"", "ingredients": [{"name": "Белок яичный", "quantity": "5", "unit": "шт", "raw": "5 шт"}, {"name": "Сахарная пудра", "quantity": "75", "unit": "г", "raw": "75 г"}, {"name": "Сахар", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Мука пшеничная", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Какао-порошок", "quantity": "10", "unit": "г", "raw": "10 г"...
```

### Example 11

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/33306/", "title": "Утка в пиве", "ingredients": [{"name": "Утка", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Пиво светлое", "quantity": "0.5", "unit": "л", "raw": "0,5  л"}, {"name": "Лук репчатый", "quantity": "1-2", "unit": "шт", "raw": "1-2  шт"}, {"name": "Маргарин", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 12

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/23115/", "title": "Индийские лепешки \"Чапати\"", "ingredients": [{"name": "Мука пшеничная", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Вода", "quantity": "1/2", "unit": "стак.", "raw": "1/2 стак."}, {"name": "Соль", "quantity": "1/2", "unit": "ч. л.", "raw": "1/2 ч. л."}, {"name": "Масло сливочное", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 13

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/114130/", "title": "Суп из баранины с нутом", "ingredients": [{"name": "Баранина", "quantity": "1", "unit": "кг", "raw": "1 кг"}, {"name": "Нут", "quantity": "1/2", "unit": "стак.", "raw": "1\\2 стак."}, {"name": "Перец болгарский", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Лук репчатый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Чеснок", "quantity": "1", "unit": "зуб.", "raw": "1 зуб."}...
```

### Example 14

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/157733/", "title": "Макрурус на гриле", "ingredients": [{"name": "Рыба", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Соль", "quantity": null, "unit": null, "raw": "по вкусу"}, {"name": "Перец черный", "quantity": null, "unit": null, "raw": "по вкусу"}, {"name": "Масло растительное", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 15

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/73450/", "title": "Суп пюре из фасоли и моркови с красным перцем", "ingredients": [{"name": "Фасоль", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Морковь", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Лук красный", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Масло растительное", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л."}, {"name": "Помидор", "quantity": "3", "uni...
```

### Example 16

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/8956/", "title": "Чашка каппучино \"Сладкая причина\"", "ingredients": [{"name": "Кофе натуральный", "quantity": null, "unit": null, "raw": null}, {"name": "Молоко", "quantity": null, "unit": null, "raw": null}, {"name": "Сливки", "quantity": null, "unit": null, "raw": null}, {"name": "Ванилин", "quantity": null, "unit": null, "raw": null}, {"name": "Сахар", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 17

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/16188/", "title": "Салат \"Рыбацкий\"", "ingredients": [{"name": "Рыба", "quantity": "400", "unit": "г", "raw": "400 г"}, {"name": "Лук репчатый", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Огурец", "quantity": "2-3", "unit": "шт", "raw": "2-3 шт"}, {"name": "Майонез", "quantity": "100-150", "unit": "г", "raw": "100-150 г"}, {"name": "Кетчуп", "quantity": "100", "unit": null, "raw": "100"}], "steps": []}
```

### Example 18

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/124175/", "title": "Пирожки \"Малышки\"", "ingredients": [{"name": "Картофель", "quantity": "1", "unit": "кг", "raw": "1 кг"}, {"name": "Лук репчатый", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Масло сливочное", "quantity": "265", "unit": "г", "raw": "265 г"}, {"name": "Масло растительное", "quantity": "5", "unit": "ст. л.", "raw": "5 ст. л."}, {"name": "Соль", "quantity": "1", "unit": "ч. л.", "raw": ...
```

### Example 19

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/161389/", "title": "Индюшиный рулет с сухофруктами", "ingredients": [{"name": "Фарш индюшачий", "quantity": "800", "unit": "г", "raw": "800 г"}, {"name": "Изюм", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Курага", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Чернослив", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Яблоко", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "...
```

### Example 20

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/16766/", "title": "Трюфеля шоколадные", "ingredients": [{"name": "Шоколад молочный", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Сливки", "quantity": "200", "unit": "мл", "raw": "200 мл"}, {"name": "Масло сливочное", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Какао-порошок", "quantity": "20", "unit": "г", "raw": "20 г"}, {"name": "Миндаль", "quantity": "30", "unit": "г", "raw": "30 г"}]...
```
