/**
 * Purpose: ESLint rules for the web app, including the hard size limits of CODING_STANDARDS.md.
 * Layer:   web tooling
 */
import js from '@eslint/js';
import vue from 'eslint-plugin-vue';
import tseslint from 'typescript-eslint';
import vueParser from 'vue-eslint-parser';

const limits = {
  'max-lines': ['error', { max: 300, skipBlankLines: false, skipComments: false }],
  'max-lines-per-function': ['error', { max: 20, skipBlankLines: true, skipComments: true }],
  'max-params': ['error', 4],
  'max-depth': ['error', 3],
  complexity: ['error', 8],
  'max-len': ['error', { code: 100, ignoreUrls: true }],
  'vue/max-len': ['error', { code: 100, template: 100, ignoreUrls: true }],
};

export default tseslint.config(
  { ignores: ['dist/**', 'node_modules/**', 'src/api/schema.d.ts'] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
        sourceType: 'module',
      },
    },
  },
  {
    rules: {
      ...limits,
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      'vue/multi-word-component-names': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
    },
  },
);
