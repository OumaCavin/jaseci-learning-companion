/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment configuration
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
    WEBSOCKET_URL: process.env.WEBSOCKET_URL || 'ws://localhost:8001',
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8001',
  },

  // Experimental features
  experimental: {
    serverActions: true,
    serverComponentsExternalPackages: ['pg', 'redis'],
  },

  // Performance optimizations
  poweredByHeader: false,
  compress: true,
  swcMinify: true,

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          }
        ]
      }
    ];
  },

  // Image optimization
  images: {
    domains: [
      'localhost',
      'ghcr.io',
      'avatars.githubusercontent.com',
      'lh3.googleusercontent.com'
    ],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
  },

  // Webpack configuration
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Bundle analyzer in development
    if (process.env.ANALYZE) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'server',
          analyzerPort: 8888,
          openAnalyzer: true,
        })
      );
    }

    // Performance optimizations
    if (!dev && !isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        '@': './src',
      };
    }

    // Environment-specific optimizations
    if (!dev) {
      config.optimization.splitChunks.cacheGroups = {
        ...config.optimization.splitChunks.cacheGroups,
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      };
    }

    return config;
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },

  // Rewrites
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // Custom page extensions
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],

  // Output configuration for Docker
  output: 'standalone',

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    ignoreDuringBuilds: false,
    dirs: ['pages', 'utils', 'components', 'hooks', 'contexts'],
  },

  // Styling configuration
  compiler: {
    styledComponents: true,
  },

  // PWA configuration
  pwa: {
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
  },

  // Analytics
  analyticsId: process.env.VERCEL_ANALYTICS_ID,

  // Build configuration
  generateEtags: true,
  trailingSlash: false,

  // Error handling
  onError: 'continue',
  onWarning: 'warning',

  // Output directory
  distDir: '.next',

  // Asset optimization
  assetPrefix: process.env.ASSET_PREFIX || '',

  // Static optimization
  staticPageGenerationTimeout: 1000,

  // Machine learning and AI integration
  transpilePackages: ['@tensorflow/tfjs', '@tensorflow/tfjs-node'],

  // Monitoring and observability
  telemetry: {
    disabled: process.env.NEXT_TELEMETRY_DISABLED === '1',
  },
};

module.exports = nextConfig;
