# frontend

Next.js interface for local-rag-mlx. One page: ask a question, watch the answer stream token by token, inspect the source cards it cites.

    npm install
    npm run dev

The dev server proxies `/api/*` and `/healthz` to `http://localhost:8000` (see `next.config.ts`), so start the backend first with `make api` from the repository root.
