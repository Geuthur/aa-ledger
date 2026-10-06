/**
 * Custom ESLint rule to sort imports into groups with section heading comments,
 * modeled after isort's `import_heading_*` feature.
 */
export default {
  meta: {
    type: 'layout',
    fixable: 'code',
    schema: [
      {
        type: 'object',
        properties: {
          groups: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                heading: { type: 'string' },
                pattern: { type: 'string' },
              },
              required: ['heading', 'pattern'],
            },
          },
        },
        additionalProperties: false,
      },
    ],
  },
  create(context) {
    const options = context.options[0] || {};
    const configuredGroups = (options.groups || []).map((g) => ({
      heading: g.heading,
      regex: new RegExp(g.pattern, 'u'),
    }));

    // Set of known heading comments to identify and strip them when re-generating
    const headingSet = new Set(configuredGroups.map((g) => g.heading.trim()));

    return {
      Program(node) {
        const sourceCode = context.sourceCode || context.getSourceCode();
        const importNodes = [];

        // Collect continuous block of top-level imports
        for (const stmt of node.body) {
          if (stmt.type === 'ImportDeclaration') {
            importNodes.push(stmt);
          } else if (importNodes.length > 0) {
            break;
          }
        }

        if (importNodes.length === 0) return;

        const firstImport = importNodes[0];
        const lastImport = importNodes[importNodes.length - 1];

        // Map of group heading -> array of items
        const groupMap = new Map();
        for (const g of configuredGroups) {
          if (!groupMap.has(g.heading)) {
            groupMap.set(g.heading, []);
          }
        }
        const unclassified = [];

        for (const imp of importNodes) {
          // Check comments before this import
          const commentsBefore = sourceCode.getCommentsBefore(imp);
          const customComments = [];

          for (const c of commentsBefore) {
            const trimmed = `// ${c.value.trim()}`;
            // If it's a known heading comment, skip it so we can re-generate freshly
            if (!headingSet.has(trimmed) && !headingSet.has(`/* ${c.value.trim()} */`)) {
              customComments.push(sourceCode.getText(c));
            }
          }

          const impText = sourceCode.getText(imp);
          const fullText = customComments.length > 0
            ? `${customComments.join('\n')}\n${impText}`
            : impText;

          const sourceVal = imp.source.value;
          let matched = false;
          for (const g of configuredGroups) {
            if (g.regex.test(sourceVal)) {
              groupMap.get(g.heading).push({
                source: sourceVal,
                fullText,
              });
              matched = true;
              break;
            }
          }

          if (!matched) {
            unclassified.push({
              source: sourceVal,
              fullText,
            });
          }
        }

        // Sort within each group
        for (const [, items] of groupMap) {
          items.sort((a, b) => {
            const sA = a.source.toLowerCase();
            const sB = b.source.toLowerCase();
            if (sA < sB) return -1;
            if (sA > sB) return 1;
            return a.fullText.localeCompare(b.fullText);
          });
        }
        unclassified.sort((a, b) => a.source.toLowerCase().localeCompare(b.source.toLowerCase()));

        // Assemble new import blocks
        const blocks = [];
        const seenHeadings = new Set();
        for (const g of configuredGroups) {
          if (seenHeadings.has(g.heading)) continue;
          seenHeadings.add(g.heading);
          const items = groupMap.get(g.heading);
          if (items && items.length > 0) {
            blocks.push(`${g.heading}\n${items.map((i) => i.fullText).join('\n')}`);
          }
        }
        if (unclassified.length > 0) {
          blocks.push(unclassified.map((i) => i.fullText).join('\n'));
        }

        const newText = blocks.join('\n\n');

        // Determine range to replace:
        // Check if there is a heading comment before firstImport
        let start = firstImport.range[0];
        const commentsBeforeFirst = sourceCode.getCommentsBefore(firstImport);
        for (let i = commentsBeforeFirst.length - 1; i >= 0; i--) {
          const c = commentsBeforeFirst[i];
          const trimmed = `// ${c.value.trim()}`;
          if (headingSet.has(trimmed)) {
            start = c.range[0];
            break;
          }
        }
        const end = lastImport.range[1];

        const originalText = sourceCode.text.slice(start, end);
        if (originalText !== newText) {
          context.report({
            loc: {
              start: sourceCode.getLocFromIndex(start),
              end: sourceCode.getLocFromIndex(end),
            },
            message: 'Imports must be grouped with section headings (like isort).',
            fix(fixer) {
              return fixer.replaceTextRange([start, end], newText);
            },
          });
        }
      },
    };
  },
};
