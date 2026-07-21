import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow connections from Docker network (backend calls to frontend)
  allowedDevOrigins: ["http://localhost:3000", "http://frontend:3000"],
};

export default nextConfig;
