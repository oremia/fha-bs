const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 代理的目标，也就是您的FastAPI后端
        changeOrigin: true,
        // 可选：如果后端路径不是/api开头，可以重写路径
        // pathRewrite: { '^/api': '' },
      }
    }
  }
})