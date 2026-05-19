import baseConfig from "@quant-os/eslint-config";

/** @type {import("eslint").Linter.FlatConfig[]} */
export default [
  ...baseConfig,
  {
    ignores: [".next/**", "node_modules/**"],
  },
];
