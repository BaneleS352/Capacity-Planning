This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## API connection

The frontend calls FastAPI through the same-origin route at `/api/backend/*`. The route
defaults to `http://127.0.0.1:8000/api/v1` and avoids browser CORS configuration. No
`.env` file is needed. In local development, the API grants system-admin access to the
first active organization when no bearer token is supplied. Deployed environments still
forward the signed-in user's `Authorization` header and can set `CAPACITY_API_URL` in the
process environment when the API is hosted elsewhere.

In one terminal, start the backend:

```powershell
Set-Location ..\CapacityPlanningAPI
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m app.cli seed-demo
uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```powershell
npm run dev
```

The team and sprint selectors load from the API. Selecting either one reloads the live
dashboard, timeline, employee, planning, reporting, and freshness views.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
