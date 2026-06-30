import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 运行时将 /api/* 请求代理到 Python 后端（容器内 hostname=backend）
// 只在设置了 API_URL 环境变量时生效（Docker Compose 中已设置）
// 本地开发时无此变量，请求正常走 Next.js API Routes

export async function middleware(request: NextRequest) {
  const BACKEND = process.env.API_URL
  if (!BACKEND) return NextResponse.next()

  const { pathname, search } = request.nextUrl
  if (!pathname.startsWith('/api/')) return NextResponse.next()

  try {
    const res = await fetch(`${BACKEND}${pathname}${search}`, {
      method: request.method,
      headers: request.headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.text(),
    })

    const body = await res.text()
    return new NextResponse(body, {
      status: res.status,
      headers: {
        'content-type': res.headers.get('content-type') || 'application/json',
      },
    })
  } catch {
    // 后端不可达时放行，让 Next.js API Routes 处理
    return NextResponse.next()
  }
}

export const config = {
  matcher: '/api/:path*',
}
