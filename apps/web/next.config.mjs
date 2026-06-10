/** @type {import('next').NextConfig} */

// NEXT_BUILD_LOW_MEM=1 — последовательная сборка для машин с малым объёмом
// свободной RAM (локальная разработка / небольшой VPS). На prod не влияет.
const lowMem = process.env.NEXT_BUILD_LOW_MEM === "1";

const nextConfig = {
  output: "standalone",
  ...(lowMem
    ? {
        experimental: {
          cpus: 1,
          workerThreads: false,
        },
      }
    : {}),
};

export default nextConfig;
