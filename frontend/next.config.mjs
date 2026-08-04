/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for the multi-stage Docker production build (node server.js)
  output: "standalone",

  // Allow react-pdf's pdfjs worker to be loaded from the same origin
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
