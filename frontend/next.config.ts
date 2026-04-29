import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["three"],
  async rewrites() {
    // Only proxy in local dev; production uses NEXT_PUBLIC_API_URL
    if (process.env.NEXT_PUBLIC_API_URL) return [];
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
