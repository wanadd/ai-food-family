/** Heuristic category slug from product name (Russian). */

import {
  DEFAULT_CATEGORY_SLUG,
  FORBIDDEN_CATEGORY_SLUG,
  mapLegacyCategorySlug,
} from "@/lib/shopping/categories-v1";

const RULES: { slug: string; patterns: RegExp[] }[] = [
  { slug: "яйца", patterns: [/яйц/i] },
  {
    slug: "специи_соусы",
    patterns: [
      /соус|кетчуп|майонез|паста\s*томат|томатн\w*\s*паст/i,
      /паприк|куркум|кориандр|лавров|приправ|ванил|сунел|шафран|хмели|корица|гвоздик/i,
      /(черн|чёрн|молот).{0,6}перец|перец.{0,6}(черн|чёрн|молот|горош)/i,
    ],
  },
  {
    slug: "овощи_зелень",
    patterns: [
      /капуст|огурц|помидор|морков|лук|чеснок|перец|салат|зелень|укроп|петрушк|брокколи|кабач|баклаж|свекл|редис|картоф/i,
    ],
  },
  {
    slug: "фрукты_ягоды",
    patterns: [
      /яблок|груш|банан|апельсин|мандарин|лимон|ягод|малин|виноград|персик|слив|арбуз|дын|черник|клубник|смородин/i,
    ],
  },
  {
    // Бульоны — бакалея, даже «куриный»: проверяем до правила мясо_птица.
    slug: "бакалея",
    patterns: [/бульон/i],
  },
  {
    slug: "мясо_птица",
    patterns: [
      /колбас|сосиск|ветчин|бекон|свинин|говядин|телят|баран|курин|куриц|индейк|фарш|мяс|стейк|ребр|окорок|грудк/i,
    ],
  },
  {
    slug: "рыба_морепродукты",
    patterns: [/рыб|лосос|форел|треск|минтай|сельд|кревет|кальмар|мидии|икра/i],
  },
  {
    slug: "молочные",
    patterns: [/молок|кефир|йогурт|творог|сыр|сметан|ряженк|простокваш|сливк/i],
  },
  {
    slug: "хлеб_выпечка",
    patterns: [/хлеб|батон|булк|лаваш|выпеч|печень|торт|пирог|круасс/i],
  },
  {
    slug: "крупы_макароны",
    patterns: [/рис|греч|овсян|макарон|спагетти|паста|перлов|пшено|булгур|киноа/i],
  },
  {
    slug: "бакалея",
    patterns: [
      /мук|сахар|соль|уксус|масло\s*раст|бульон|орех|фундук|миндал|кешью|фисташ|грецк/i,
    ],
  },
  {
    slug: "напитки",
    patterns: [/сок|вода|чай|кофе|компот|лимонад|квас/i],
  },
  {
    slug: "быт_уборка",
    patterns: [/лампоч|батарей|салфет|мыло|порошок|шампун|средство|губк|пакет|пленк|уборк/i],
  },
  {
    slug: "детские_товары",
    patterns: [/подгуз|соск|пюре\s*дет|детск/i],
  },
  {
    slug: "для_питомцев",
    patterns: [/корм|наполнител|для\s*кот|для\s*соб|питомц/i],
  },
];

export function suggestCategorySlug(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) {
    return DEFAULT_CATEGORY_SLUG;
  }
  for (const rule of RULES) {
    if (rule.patterns.some((p) => p.test(trimmed))) {
      return rule.slug;
    }
  }
  return DEFAULT_CATEGORY_SLUG;
}

export { DEFAULT_CATEGORY_SLUG };

export function normalizeCategorySlug(
  slug: string | null | undefined,
  itemName?: string,
): string {
  const mapped = slug ? mapLegacyCategorySlug(slug) : null;
  if (mapped) {
    return mapped;
  }
  if (itemName?.trim()) {
    return suggestCategorySlug(itemName);
  }
  return DEFAULT_CATEGORY_SLUG;
}
