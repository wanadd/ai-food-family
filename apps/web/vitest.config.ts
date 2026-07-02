import { fileURLToPath } from "node:url";

// Plain object config: vitest may run via npx without a local install,
// so we avoid importing "vitest/config" here.
export default {
  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },
  test: {
    pool: "threads",
    fileParallelism: false,
  },
};
