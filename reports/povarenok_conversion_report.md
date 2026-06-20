# Povarenok Conversion Report

## Source

- Input: `C:\Users\boss\Desktop\рецепты\povarenok_recipes_2021_06_16.csv`
- Output: `C:\Projects\ai-food-family\exports\povarenok_planam_raw.jsonl`
- Report: `C:\Projects\ai-food-family\reports\povarenok_conversion_report.md`
- Dry run: `False`
- Detected encoding: `utf-8`
- Encoding candidates: `utf-8, utf-8-sig, cp1251, windows-1251, latin1`

## Summary

- Total rows: `88930`
- Converted: `80000`
- Skipped: `8930`
- Duplicates: `8921`
- Ingredients parsed: `587063`
- Ingredients unparsed: `117015`

## JSONL Examples

### Example 1

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/94373/", "title": "Домашний абсент, по рецепту из Понтарлье, Франция (1855)", "ingredients": [{"name": "Цветки", "quantity": "25", "unit": "г", "raw": "25 г"}, {"name": "Анис", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Фенхель", "quantity": "50", "unit": "г", "raw": "50 г"}, {"name": "Спирт", "quantity": "950", "unit": "мл", "raw": "950 мл"}, {"name": "Мята", "quantity": "1", "unit": "г", "raw": "1 г"}...
```

### Example 2

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/27297/", "title": "Пирог \"Семейный\"", "ingredients": [{"name": "Яйцо куриное", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Дрожжи", "quantity": "40", "unit": "г", "raw": "40  г"}, {"name": "Маргарин", "quantity": "150", "unit": "г", "raw": "150 г"}, {"name": "Соль", "quantity": null, "unit": null, "raw": null}, {"name": "Сахар", "quantity": null, "unit": null, "raw": null}, {"name": "Молоко", "quantity...
```

### Example 3

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/387/", "title": "Уха рыбацкая с картофелем", "ingredients": [{"name": "Зелень", "quantity": "1", "unit": "пуч.", "raw": "1 пуч."}, {"name": "Картофель", "quantity": "6", "unit": "шт", "raw": "6 шт"}, {"name": "Лист лавровый", "quantity": "2", "unit": "шт", "raw": "2 шт"}, {"name": "Перец черный", "quantity": "5", "unit": "шт", "raw": "5 шт"}, {"name": "Масло сливочное", "quantity": "1", "unit": "ст. л.", "raw": "1 ст...
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
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/164259/", "title": "Овсяное печенье \"Рыбки\"", "ingredients": [{"name": "Хлопья овсяные", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Банан", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Орехи", "quantity": "0.3", "unit": "стак.", "raw": "0,3 стак."}, {"name": "Изюм", "quantity": "3", "unit": "ст. л.", "raw": "3 ст. л."}, {"name": "Ванилин", "quantity": "1", "unit": "пакет.", "raw": "1...
```

### Example 7

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/79660/", "title": "Универсальный салат из свеклы с орехами", "ingredients": [{"name": "Свекла", "quantity": "160", "unit": "г", "raw": "160 г"}, {"name": "Орехи грецкие", "quantity": "7", "unit": "шт", "raw": "7 шт"}, {"name": "Сок лимонный", "quantity": "1", "unit": "ст. л.", "raw": "1 ст. л."}, {"name": "Масло оливковое", "quantity": "1", "unit": "ст. л.", "raw": "1 ст. л."}, {"name": "Чернослив", "quantity": "7", ...
```

### Example 8

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/29511/", "title": "Мясо без забот", "ingredients": [{"name": "Говядина", "quantity": null, "unit": null, "raw": null}, {"name": "Лук репчатый", "quantity": null, "unit": null, "raw": null}, {"name": "Специи", "quantity": null, "unit": null, "raw": null}, {"name": "Соль", "quantity": null, "unit": null, "raw": null}, {"name": "Масло растительное", "quantity": null, "unit": null, "raw": null}], "steps": []}
```

### Example 9

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/12527/", "title": "Мороженое из персиков", "ingredients": [{"name": "Персик", "quantity": "250", "unit": "г", "raw": "250 г"}, {"name": "Сметана", "quantity": "120", "unit": "г", "raw": "120 г"}, {"name": "Сахарная пудра", "quantity": "2", "unit": "ст. л.", "raw": "2 ст. л."}, {"name": "Яйцо куриное", "quantity": "1", "unit": "шт", "raw": "1 шт"}], "steps": []}
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
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/114340/", "title": "Печеночное суфле \"Нежность\" с гречневыми хлопьями", "ingredients": [{"name": "Хлопья гречневые", "quantity": "1/2", "unit": "стак.", "raw": "1/2 стак."}, {"name": "Печень куриная", "quantity": "400", "unit": "г", "raw": "400 г"}, {"name": "Молоко", "quantity": "1", "unit": "стак.", "raw": "1 стак."}, {"name": "Лук репчатый", "quantity": "1", "unit": "шт", "raw": "1 шт"}, {"name": "Морковь", "qua...
```

### Example 17

```json
{"source": "povarenok", "source_url": "https://www.povarenok.ru/recipes/show/16679/", "title": "Пюре из фасоли", "ingredients": [{"name": "Фасоль", "quantity": null, "unit": null, "raw": null}, {"name": "Чеснок", "quantity": null, "unit": null, "raw": null}, {"name": "Лук репчатый", "quantity": null, "unit": null, "raw": null}, {"name": "Масло растительное", "quantity": null, "unit": null, "raw": null}], "steps": []}
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
