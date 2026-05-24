import type { RecipeQuery } from "@/lib/recipes/types";

export type RecipeCatalogSection = {
  id: string;
  title: string;
  query: RecipeQuery;
};

export const RECIPE_CATALOG_SECTIONS: RecipeCatalogSection[] = [
  { id: "for_you", title: "Для вас", query: {} },
  { id: "pantry", title: "Из запасов", query: { from_pantry: true } },
  { id: "lose", title: "Для похудения", query: { goal: "lose" } },
  { id: "protein", title: "Высокобелковые", query: { protein_only: true } },
  { id: "family", title: "Для семьи", query: { for_children: true } },
  { id: "drinks", title: "Напитки", query: { drinks_only: true, non_alcoholic: true } },
  { id: "cocktails", title: "Коктейли", query: { smoothie_only: true } },
];

export const RECIPE_SECTION_PAGE_SIZE = 10;
