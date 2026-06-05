# Povarenok Conversion Report

## Source

- Input: `C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv`
- Output: `C:\Projects\ai-food-family\exports\povarenok_planam_raw.jsonl`
- Report: `C:\Projects\ai-food-family\reports\povarenok_conversion_report.md`
- Dry run: `False`
- Detected encoding: `utf-8`
- Encoding candidates: `utf-8, utf-8-sig, cp1251, windows-1251, latin1`

## Summary

- Total rows: `146582`
- Converted: `128196`
- Skipped: `18386`
- Duplicates: `18368`
- Ingredients parsed: `941402`
- Ingredients unparsed: `187787`

## JSONL Examples

### Example 1

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/94373/", "title": "Домашний абсент, по рецепту из Понтарлье, Франция (1855)", "ingredients": [{"name": "Цветки", "quantity": "25", "unit": "г", "raw": "25 г"}, {"name": "Анис", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Фенхель", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Спирт", "quantity": "950", "unit": "мл", "raw": "950 мл"}, {"name": "Мята", "quantity": "1", "unit": "г", "raw": "1 г"}...
```

### Example 2

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/88486/", "title": "Мороженое ананасовое", "ingredients": [{"name": "Ананас", "quantity": "400", "unit": "г", "raw": "400 г"}, {"name": "Молоко", "quantity": "50", "unit": "мл", "raw": "50 мл"}, {"name": "Сахар", "quantity": "2", "unit": "ст. л.", "raw": "2 ст. л."}], "steps": []}
```

### Example 3

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/157022/", "title": "Ягодные конфеты \"Невесомые\"", "ingredients": [{"name": "Ягода", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Сахар", "quantity": "90", "unit": "г", "raw": "90 г"}, {"name": "Сок лимонный", "quantity": "1", "unit": "ст. л.", "raw": "1 ст. л."}, {"name": "Желатин", "quantity": "2", "unit": "пач.", "raw": "2 пач."}], "steps": []}
```

### Example 4

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/172026/", "title": "Салат из печёных овощей", "ingredients": [{"name": "Свекла", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Морковь", "quantity": "70", "unit": "г", "raw": "70 г"}, {"name": "Яблоко", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Лук красный", "quantity": "25", "unit": "г", "raw": "25 г"}, {"name": "Огурец", "quantity": "70", "unit": "г", "raw": "70 г"}, {"name": "Оливки зел...
```

### Example 5

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/147528/", "title": "Коктейль из авокадо с креветками", "ingredients": [{"name": "Авокадо", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Чеснок", "quantity": "1", "unit": "зуб.", "raw": "1 зуб."}, {"name": "Сок апельсиновый", "quantity": "100", "unit": "мл", "raw": "100 мл"}, {"name": "Креветки", "quantity": "14", "unit": "шт", "raw": "14 шт"}, {"name": "Кинза", "quantity": "5", "unit": "веточ.", "raw": "5...
```

### Example 6

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/122118/", "title": "Трубочки творожные, запеченные с сыром", "ingredients": [{"name": "Блин", "quantity": "9", "unit": "шт", "raw": "9 шт"}, {"name": "Творог", "quantity": "350", "unit": "г", "raw": "350 г"}, {"name": "Яйцо куриное", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Мука пшеничная", "quantity": "35", "unit": "г", "raw": "35 г"}, {"name": "Соль", "quantity": null, "unit": null, "raw": null}, {"...
```

### Example 7

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/140700/", "title": "Экспресс-маринад для свиных ребер", "ingredients": [{"name": "Ребра свиные", "quantity": "1", "unit": "кг", "raw": "1 кг"}, {"name": "Горчица", "quantity": "3", "unit": "ч. л.", "raw": "3 ч. л."}, {"name": "Соевый соус", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л."}, {"name": "Хмели-сунели", "quantity": "1", "unit": "ч. л.", "raw": "1 ч. л."}, {"name": "Перец черный", "quantity": "2", "uni...
```

### Example 8

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/29511/", "title": "Мясо без забот", "ingredients": [{"name": "Говядина", "quantity": null, "unit": null, "raw": null}, {"name": "Лук репчатый", "quantity": null, "unit": null, "raw": null}, {"name": "Специи", "quantity": null, "unit": null, "raw": null}, {"name": "Соль", "quantity": null, "unit": null, "raw": null}, {"name": "Масло растительное", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 9

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/93357/", "title": "Соус с крыжовником на зиму", "ingredients": [{"name": "Крыжовник", "quantity": "500", "unit": "г", "raw": "500 г"}, {"name": "Помидор", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Перец болгарский", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Лук репчатый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Чеснок", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"na...
```

### Example 10

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/115851/", "title": "Тарталетки с апельсиновым кремом", "ingredients": [{"name": "Мука пшеничная", "quantity": "175", "unit": "г", "raw": "175 г"}, {"name": "Масло сливочное", "quantity": "60", "unit": "г", "raw": "60 г"}, {"name": "Желток яичный", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Сахар", "quantity": "5", "unit": "ст. л.", "raw": "5 ст. л."}, {"name": "Соль", "quantity": "1", "unit": "щепот.", ...
```

### Example 11

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/25633/", "title": "Закуска \"Дыхание дракона\"", "ingredients": [{"name": "Крабовые палочки", "quantity": "1", "unit": "упак.", "raw": "1 упак."}, {"name": "Сыр плавленый", "quantity": "1", "unit": "упак.", "raw": "1 упак."}, {"name": "Яйцо куриное", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Соус", "quantity": "1", "unit": "упак.", "raw": "1 упак."}, {"name": "Чеснок", "quantity": "1", "unit": "зуб.", ...
```

### Example 12

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/158405/", "title": "Сладкие треугольники с начинкой \"Моментальные\"", "ingredients": [{"name": "Тесто слоеное дрожжевое", "quantity": "450", "unit": "г", "raw": "450 г"}, {"name": "Молоко сгущенное", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л."}, {"name": "Яйцо куриное", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Стружка кокосовая", "quantity": "2", "unit": "ст. л.", "raw": "2 ст. л."}], "steps...
```

### Example 13

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/162754/", "title": "Лаваш в электрогриле", "ingredients": [{"name": "Мука пшеничная", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Вода", "quantity": "335", "unit": "мл", "raw": "335 мл"}, {"name": "Сахар", "quantity": "1", "unit": "ч. л.", "raw": "1 ч. л."}, {"name": "Соль", "quantity": null, "unit": null, "raw": "по вкусу"}, {"name": "Масло растительное", "quantity": "3", "unit": "ст. л.", "raw": "3 ст....
```

### Example 14

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/41444/", "title": "Маффины из сметаны, белого шоколада и ягод", "ingredients": [{"name": "Сметана", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Яйцо куриное", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Масло сливочное", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Масло растительное", "quantity": "2", "unit": "ст. л.", "raw": "2 ст. л."}, {"name": "Мука пшеничная", "quantity...
```

### Example 15

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/81536/", "title": "Курица наивкуснейшая в карамели", "ingredients": [{"name": "Бедро куриное", "quantity": "1", "unit": "кг", "raw": "1 кг"}, {"name": "Вода", "quantity": "0.5", "unit": "стак.", "raw": "0.5 стак."}, {"name": "Сахар", "quantity": "4", "unit": "ст. л.", "raw": "4 ст. л."}, {"name": "Соль", "quantity": "1", "unit": "ч. л.", "raw": "1 ч. л."}, {"name": "Паприка сладкая", "quantity": "1", "unit": "ч. л.",...
```

### Example 16

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/97198/", "title": "Омлет с кальмарами, рыбой и зеленью", "ingredients": [{"name": "Рыба", "quantity": "150", "unit": "г", "raw": "150 г"}, {"name": "Кальмар", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Яйцо куриное", "quantity": "4", "unit": "шт", "raw": "4 шт"}, {"name": "Сливки", "quantity": "140", "unit": "мл", "raw": "140 мл"}, {"name": "Лук репчатый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, ...
```

### Example 17

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/149267/", "title": "Суп с потрошками индейки «Уютный»", "ingredients": [{"name": "Желудок индюшачий", "quantity": "450", "unit": "г", "raw": "450 г"}, {"name": "Рис", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Вода", "quantity": "1.5", "unit": "л", "raw": "1,5 л"}, {"name": "Лук-порей", "quantity": "1/2", "unit": "шт", "raw": "1/2 шт"}, {"name": "Морковь", "quantity": "1/2", "unit": "шт", "raw": "...
```

### Example 18

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/24312/", "title": "Фаршированные помидоры \"Коктейль\"", "ingredients": [{"name": "Коктейль морской", "quantity": "250-300", "unit": "г", "raw": "250-300 г"}, {"name": "Лук репчатый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Майонез", "quantity": "100", "unit": "г", "raw": "100 г"}, {"name": "Помидор", "quantity": "4", "unit": "шт", "raw": "4 шт"}, {"name": "Соль", "quantity": null, "unit": null, "raw...
```

### Example 19

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/54142/", "title": "Пирог \"Шоколадная зебра с вишней\"", "ingredients": [{"name": "Яйцо куриное", "quantity": "3", "unit": "шт", "raw": "3 шт"}, {"name": "Сахар", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Мука пшеничная", "quantity": "200", "unit": "г", "raw": "200 г"}, {"name": "Молоко", "quantity": "200", "unit": "мл", "raw": "200 мл"}, {"name": "Масло подсолнечное", "quantity": "130", "unit": "мл"...
```

### Example 20

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/60741/", "title": "Улитки шоколадно-ореховые и маковые", "ingredients": [{"name": "Молоко", "quantity": "200", "unit": "мл", "raw": "200 мл"}, {"name": "Дрожжи", "quantity": "6", "unit": "г", "raw": "6 г"}, {"name": "Мука пшеничная", "quantity": "2.5-3", "unit": "стак.", "raw": "2,5-3 стак."}, {"name": "Яйцо куриное", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Сахар", "quantity": "15", "unit": "ст. л.",...
```
