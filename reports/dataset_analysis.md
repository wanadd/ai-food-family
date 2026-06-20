# RecipeNLG Dataset Analysis

## Source

- Input: `C:\Users\boss\Desktop\рецепты\dataset\dataset\full_dataset.csv`
- Report: `C:\Projects\ai-food-family\reports\dataset_analysis.md`
- Chunk size: `50000` rows

## Summary

- Total rows: `2231142`
- Columns: `7`

## Columns

- `Unnamed: 0`: filled `100.00%`, empty `0`
- `title`: filled `100.00%`, empty `3`
- `ingredients`: filled `100.00%`, empty `0`
- `directions`: filled `100.00%`, empty `0`
- `link`: filled `100.00%`, empty `0`
- `source`: filled `100.00%`, empty `0`
- `NER`: filled `99.97%`, empty `573`

## Text Lengths

- Average title length: `23.90` characters
- Average instruction length: `505.11` characters

## Ingredient Examples

- 1 c. firmly packed brown sugar
- 1/2 c. evaporated milk
- 1/2 tsp. vanilla
- 1/2 c. broken nuts (pecans)
- 2 Tbsp. butter or margarine
- 3 1/2 c. bite size shredded rice biscuits
- 1 small jar chipped beef, cut up
- 4 boned chicken breasts
- 1 can cream of mushroom soup
- 1 carton sour cream

## Cooking Step Examples

- In a heavy 2-quart saucepan, mix brown sugar, nuts, evaporated milk and butter or margarine.
- Stir over medium heat until mixture bubbles all over top.
- Boil and stir 5 minutes more. Take off heat.
- Stir in vanilla and cereal; mix well.
- Using 2 teaspoons, drop and shape into 30 clusters on wax paper.
- Let stand until firm, about 30 minutes.
- Place chipped beef on bottom of baking dish.
- Place chicken on top of beef.
- Mix soup and cream together; pour over chicken. Bake, uncovered, at 275° for 3 hours.
- In a slow cooker, combine all ingredients. Cover and cook on low for 4 hours or until heated through and cheese is melted. Stir well before serving. Yields 6 servings.

## Sample Records

### Sample 1
- **Unnamed: 0**: 0
- **title**: No-Bake Nut Cookies
- **ingredients**: ["1 c. firmly packed brown sugar", "1/2 c. evaporated milk", "1/2 tsp. vanilla", "1/2 c. broken nuts (pecans)", "2 Tbsp. butter or margarine", "3 1/2 c. bite size shredded rice biscuits"]
- **directions**: ["In a heavy 2-quart saucepan, mix brown sugar, nuts, evaporated milk and butter or margarine.", "Stir over medium heat until mixture bubbles all over top.", "Boil and stir 5 minutes more. Take off heat.", "Stir in va...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=44874
- **source**: Gathered
- **NER**: ["brown sugar", "milk", "vanilla", "nuts", "butter", "bite size shredded rice biscuits"]

### Sample 2
- **Unnamed: 0**: 1
- **title**: Jewell Ball'S Chicken
- **ingredients**: ["1 small jar chipped beef, cut up", "4 boned chicken breasts", "1 can cream of mushroom soup", "1 carton sour cream"]
- **directions**: ["Place chipped beef on bottom of baking dish.", "Place chicken on top of beef.", "Mix soup and cream together; pour over chicken. Bake, uncovered, at 275\u00b0 for 3 hours."]
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=699419
- **source**: Gathered
- **NER**: ["beef", "chicken breasts", "cream of mushroom soup", "sour cream"]

### Sample 3
- **Unnamed: 0**: 2
- **title**: Creamy Corn
- **ingredients**: ["2 (16 oz.) pkg. frozen corn", "1 (8 oz.) pkg. cream cheese, cubed", "1/3 c. butter, cubed", "1/2 tsp. garlic powder", "1/2 tsp. salt", "1/4 tsp. pepper"]
- **directions**: ["In a slow cooker, combine all ingredients. Cover and cook on low for 4 hours or until heated through and cheese is melted. Stir well before serving. Yields 6 servings."]
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=10570
- **source**: Gathered
- **NER**: ["frozen corn", "cream cheese", "butter", "garlic powder", "salt", "pepper"]

### Sample 4
- **Unnamed: 0**: 3
- **title**: Chicken Funny
- **ingredients**: ["1 large whole chicken", "2 (10 1/2 oz.) cans chicken gravy", "1 (10 1/2 oz.) can cream of mushroom soup", "1 (6 oz.) box Stove Top stuffing", "4 oz. shredded cheese"]
- **directions**: ["Boil and debone chicken.", "Put bite size pieces in average size square casserole dish.", "Pour gravy and cream of mushroom soup over chicken; level.", "Make stuffing according to instructions on box (do not make to...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=897570
- **source**: Gathered
- **NER**: ["chicken", "chicken gravy", "cream of mushroom soup", "shredded cheese"]

### Sample 5
- **Unnamed: 0**: 4
- **title**: Reeses Cups(Candy)
- **ingredients**: ["1 c. peanut butter", "3/4 c. graham cracker crumbs", "1 c. melted butter", "1 lb. (3 1/2 c.) powdered sugar", "1 large pkg. chocolate chips"]
- **directions**: ["Combine first four ingredients and press in 13 x 9-inch ungreased pan.", "Melt chocolate chips and spread over mixture. Refrigerate for about 20 minutes and cut into pieces before chocolate gets hard.", "Keep in ref...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=659239
- **source**: Gathered
- **NER**: ["peanut butter", "graham cracker crumbs", "butter", "powdered sugar", "chocolate chips"]

### Sample 6
- **Unnamed: 0**: 5
- **title**: Cheeseburger Potato Soup
- **ingredients**: ["6 baking potatoes", "1 lb. of extra lean ground beef", "2/3 c. butter or margarine", "6 c. milk", "3/4 tsp. salt", "1/2 tsp. pepper", "1 1/2 c (6 oz.) shredded Cheddar cheese, divided", "12 sliced bacon, cooked, cru...
- **directions**: ["Wash potatoes; prick several times with a fork.", "Microwave them with a wet paper towel covering the potatoes on high for 6-8 minutes.", "The potatoes should be soft, ready to eat.", "Let them cool enough to handle...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=20115
- **source**: Gathered
- **NER**: ["baking potatoes", "extra lean ground beef", "butter", "milk", "salt", "pepper", "Cheddar cheese", "bacon", "green onion", "sour cream"]

### Sample 7
- **Unnamed: 0**: 6
- **title**: Rhubarb Coffee Cake
- **ingredients**: ["1 1/2 c. sugar", "1/2 c. butter", "1 egg", "1 c. buttermilk", "2 c. flour", "1/2 tsp. salt", "1 tsp. soda", "1 c. buttermilk", "2 c. rhubarb, finely cut", "1 tsp. vanilla"]
- **directions**: ["Cream sugar and butter.", "Add egg and beat well.", "To creamed butter, sugar and egg, add alternately buttermilk with mixture of flour, salt and soda.", "Mix well.", "Add rhubarb and vanilla.", "Pour into greased 9...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=210288
- **source**: Gathered
- **NER**: ["sugar", "butter", "egg", "buttermilk", "flour", "salt", "soda", "buttermilk", "rhubarb", "vanilla"]

### Sample 8
- **Unnamed: 0**: 7
- **title**: Scalloped Corn
- **ingredients**: ["1 can cream-style corn", "1 can whole kernel corn", "1/2 pkg. (approximately 20) saltine crackers, crushed", "1 egg, beaten", "6 tsp. butter, divided", "pepper to taste"]
- **directions**: ["Mix together both cans of corn, crackers, egg, 2 teaspoons of melted butter and pepper and place in a buttered baking dish.", "Dot with remaining 4 teaspoons of butter.", "Bake at 350\u00b0 for 1 hour."]
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=876969
- **source**: Gathered
- **NER**: ["cream-style corn", "whole kernel corn", "crackers", "egg", "butter", "pepper"]

### Sample 9
- **Unnamed: 0**: 8
- **title**: Nolan'S Pepper Steak
- **ingredients**: ["1 1/2 lb. round steak (1-inch thick), cut into strips", "1 can drained tomatoes, cut up (save liquid)", "1 3/4 c. water", "1/2 c. onions", "1 1/2 Tbsp. Worcestershire sauce", "2 green peppers, diced", "1/4 c. oil"]
- **directions**: ["Roll steak strips in flour.", "Brown in skillet.", "Salt and pepper.", "Combine tomato liquid, water, onions and browned steak. Cover and simmer for one and a quarter hours.", "Uncover and stir in Worcestershire sau...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=375254
- **source**: Gathered
- **NER**: ["tomatoes", "water", "onions", "Worcestershire sauce", "green peppers", "oil"]

### Sample 10
- **Unnamed: 0**: 9
- **title**: Millionaire Pie
- **ingredients**: ["1 large container Cool Whip", "1 large can crushed pineapple", "1 can condensed milk", "3 lemons", "1 c. pecans", "2 graham cracker crusts"]
- **directions**: ["Empty Cool Whip into a bowl.", "Drain juice from pineapple.", "Mix Cool Whip and pineapple.", "Add condensed milk.", "Squeeze lemons, remove seeds and add to Cool Whip and pineapple.", "Chop nuts into small pieces a...
- **link**: www.cookbooks.com/Recipe-Details.aspx?id=794547
- **source**: Gathered
- **NER**: ["pineapple", "condensed milk", "lemons", "pecans", "graham cracker crusts"]
