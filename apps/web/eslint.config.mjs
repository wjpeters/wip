import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import hooks from 'eslint-plugin-react-hooks';
export default tseslint.config({ignores:['dist/**','node_modules/**','test-results/**','playwright-report/**','src/generated.ts']},js.configs.recommended,...tseslint.configs.recommended,{files:['src/**/*.{ts,tsx}'],plugins:{'react-hooks':hooks},rules:{'react-hooks/rules-of-hooks':'error','react-hooks/exhaustive-deps':'error'}},{files:['**/*.mjs'],languageOptions:{globals:{process:'readonly'}}});
