import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: './openapi.json',
  output: 'src/features/datasets/api/generated',
  plugins: [
    '@hey-api/typescript',
    {
      name: '@hey-api/sdk',
      validator: { response: true },
    },
    {
      name: '@hey-api/client-fetch',
      runtimeConfigPath: './src/features/datasets/api/hey-api.ts',
    },
    '@tanstack/react-query',
    'zod',
  ],
})
