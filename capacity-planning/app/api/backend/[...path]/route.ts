import type { NextRequest } from 'next/server';

const DEFAULT_API_URL = 'http://127.0.0.1:8000/api/v1';

async function proxyRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const baseUrl = (process.env.CAPACITY_API_URL || DEFAULT_API_URL).replace(/\/$/, '');
  const target = new URL(`${baseUrl}/${path.map(encodeURIComponent).join('/')}`);
  target.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  const correlationId = request.headers.get('x-correlation-id');
  const incomingAuthorization = request.headers.get('authorization');
  const configuredToken = process.env.CAPACITY_API_TOKEN;

  if (contentType) headers.set('content-type', contentType);
  if (correlationId) headers.set('x-correlation-id', correlationId);
  if (incomingAuthorization) {
    headers.set('authorization', incomingAuthorization);
  } else if (configuredToken) {
    headers.set('authorization', `Bearer ${configuredToken}`);
  }

  const hasBody = !['GET', 'HEAD'].includes(request.method);

  try {
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: 'no-store',
    });
    const responseHeaders = new Headers();
    const responseContentType = response.headers.get('content-type');
    const responseCorrelationId = response.headers.get('x-correlation-id');

    if (responseContentType) responseHeaders.set('content-type', responseContentType);
    if (responseCorrelationId) responseHeaders.set('x-correlation-id', responseCorrelationId);

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown connection error';
    return Response.json(
      {
        type: 'about:blank',
        title: 'Capacity API unavailable',
        status: 502,
        detail: `Could not connect to ${target.origin}: ${message}`,
      },
      { status: 502 },
    );
  }
}

export const dynamic = 'force-dynamic';

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;

