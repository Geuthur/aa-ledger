// Third Party
import { Linter } from "eslint";
import { describe, expect, it } from "vitest";

import importHeadings from "./import-headings.js";

const linter = new Linter();

const config = [
  {
    files: ["**/*.js"],
    languageOptions: { ecmaVersion: "latest", sourceType: "module" },
    plugins: { "import-headings": { rules: { "import-headings": importHeadings } } },
    rules: {
      "import-headings/import-headings": [
        "error",
        {
          groups: [
            { heading: "// React", pattern: "^react($|/)" },
            { heading: "// Third Party", pattern: "^@?\\w" },
            { heading: "// Styles", pattern: "\\.s?css$" },
          ],
        },
      ],
    },
  },
];

const fix = (code) => linter.verifyAndFix(code, config, { filename: "file.js" });

describe("import-headings rule", () => {
  it("test_fix_should_group_imports_under_headings", () => {
    // Test Data
    const code = 'import b from "b";\nimport React from "react";\nimport "./a.css";\n';

    // Test Action
    const result = fix(code);

    // Expected Result
    expect(result.fixed).toBe(true);
    expect(result.output).toBe(
      '// React\nimport React from "react";\n\n// Third Party\nimport b from "b";\n\n// Styles\nimport "./a.css";\n',
    );
  });

  it("test_fix_should_be_idempotent", () => {
    // Test Data
    const once = fix('import b from "b";\nimport React from "react";\n').output;

    // Test Action
    const twice = fix(once);

    // Expected Result
    expect(twice.fixed).toBe(false);
    expect(twice.output).toBe(once);
    expect(twice.messages).toEqual([]);
  });

  it("test_fix_should_not_duplicate_unknown_comment_before_first_import", () => {
    // Test Data
    const code = '// Legacy Heading\nimport b from "b";\nimport c from "c";\n\nexport const x = b + c;\n';

    // Test Action
    const result = fix(code);

    // Expected Result
    expect(result.output.match(/\/\/ Legacy Heading/g)).toHaveLength(1);
    expect(result.output.split("\n").length).toBeLessThan(15);
    expect(fix(result.output).output).toBe(result.output);
  });

  it("test_fix_should_keep_comment_between_imports", () => {
    // Test Data
    const code = 'import b from "b";\n// keep me\nimport c from "c";\n';

    // Test Action
    const result = fix(code);

    // Expected Result
    expect(result.output.match(/\/\/ keep me/g)).toHaveLength(1);
    expect(fix(result.output).output).toBe(result.output);
  });
});
