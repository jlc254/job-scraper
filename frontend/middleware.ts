// Next.js 15 uses middleware.ts. From Next.js 16 the file is proxy.ts (see doc 14, O10).
import { NextRequest, NextResponse } from "next/server";
import { checkBasicAuth } from "./lib/auth";

export function middleware(req: NextRequest) {
  if (checkBasicAuth(req.headers.get("authorization"), process.env.DASH_USER, process.env.DASH_PASS)) {
    return NextResponse.next();
  }
  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="jobs"',
      "X-Robots-Tag": "noindex, nofollow",
    },
  });
}

// Everything except static assets and robots.txt (which only says "disallow all").
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt).*)"],
};
