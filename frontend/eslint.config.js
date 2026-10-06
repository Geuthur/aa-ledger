import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'
import importHeadingsRule from './eslint-rules/import-headings.js'

const importHeadingsPlugin = {
  rules: {
    'import-headings': importHeadingsRule,
  },
}

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    plugins: {
      'import-headings': importHeadingsPlugin,
    },
    rules: {
      'import-headings/import-headings': [
        'error',
        {
          groups: [
            // 1. React & Core-Frameworks
            { heading: '// React', pattern: '^react($|/)|^react-dom($|/)|^react-router' },

            // 2. Externe Bibliotheken / Third Party
            { heading: '// Third Party', pattern: '^@?\\w' },

            // 3. AA Example (Eigene Komponenten, Helpers, API)
            //{ heading: '// AA Example', pattern: '^@/' },
            //{ heading: '// AA Example', pattern: '^\\.(?!.*\\.s?css$)' },

            // 4. Stylesheets & CSS-Module
            { heading: '// Styles', pattern: '\\.s?css$' },
          ],
        },
      ],
    },
    languageOptions: {
      globals: globals.browser,
    },
  },
])
