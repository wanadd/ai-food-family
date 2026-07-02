export function setNodeEnvForTest(value: NodeJS.ProcessEnv["NODE_ENV"]) {
  Object.defineProperty(process.env, "NODE_ENV", {
    value,
    configurable: true,
    enumerable: true,
    writable: true,
  });
}
