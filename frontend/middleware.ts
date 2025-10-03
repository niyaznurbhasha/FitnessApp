import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  // Skip auth for health checks and API routes
  if (req.nextUrl.pathname.startsWith('/api') || req.nextUrl.pathname === '/health') {
    return NextResponse.next();
  }

  const auth = req.headers.get("authorization") || "";
  const [scheme, b64] = auth.split(" ");
  const [u, p] = scheme === "Basic" && b64 ? atob(b64).split(":") : ["",""];
  
  if (u === process.env.PREVIEW_USER && p === process.env.PREVIEW_PASS) {
    return NextResponse.next();
  }
  
  return new NextResponse("Authentication required", {
    status: 401,
    headers: { 
      "WWW-Authenticate": 'Basic realm="Preview Access"',
      "Content-Type": "text/plain"
    },
  });
}

export const config = { 
  matcher: ["/((?!_next|favicon.ico|.*\\.).*)"]
};
