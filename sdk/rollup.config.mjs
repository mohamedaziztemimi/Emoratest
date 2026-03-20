import typescript from "@rollup/plugin-typescript";
import terser from "@rollup/plugin-terser";
import dts from "rollup-plugin-dts";

const input = "src/index.ts";

export default [
  // UMD build (for <script> tag embedding)
  {
    input,
    output: {
      file: "dist/conversiono.umd.js",
      format: "umd",
      name: "Conversiono",
      sourcemap: true,
    },
    plugins: [
      typescript({ tsconfig: "./tsconfig.json" }),
      terser(),
    ],
  },
  // ESM build (for bundler imports)
  {
    input,
    output: {
      file: "dist/conversiono.esm.js",
      format: "esm",
      sourcemap: true,
    },
    plugins: [
      typescript({ tsconfig: "./tsconfig.json" }),
      terser(),
    ],
  },
  // Type declarations
  {
    input,
    output: { file: "dist/index.d.ts", format: "esm" },
    plugins: [dts()],
  },
];
