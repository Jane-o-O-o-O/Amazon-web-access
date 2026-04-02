import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { hostname: "**.alicdn.com" },
      { hostname: "**.amazon.com" },
      { hostname: "**.ssl-images-amazon.com" },
      { hostname: "m.media-amazon.com" },
    ],
  },
};

export default nextConfig;
