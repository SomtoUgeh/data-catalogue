import eslint from '@eslint/js'
import oxlint from 'eslint-plugin-oxlint'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  {
    ignores: ['dist/**', 'src/features/datasets/api/generated/**', 'src/routeTree.gen.ts'],
  },
  eslint.configs.recommended,
  tseslint.configs.recommended,
  reactHooks.configs.flat.recommended,
  ...oxlint.buildFromOxlintConfigFile('./.oxlintrc.json'),
)
