import fs from "node:fs";
import { ESLint } from "eslint";

// We need to use the real project ESLint config (which uses typescript-eslint)!
const eslint = new ESLint();
const results = await eslint.lintFiles(["src/Components/Tables/BaseTable.tsx"]);
console.log("ESLint on BaseTable errors:", results[0].messages);
