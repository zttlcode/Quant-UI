/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Docker 部署使用 standalone 模式，减小镜像体积
  output: 'standalone',
}

module.exports = nextConfig
