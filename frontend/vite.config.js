import path from 'path';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
    plugins: [vue()],
    base: '/',
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src')
        }
    },
    server: {
        port: 5173,
        host: '0.0.0.0',
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:9910',
                changeOrigin: true,
                secure: false
            }
        }
    },
    build: {
        assetsDir: 'assets', // 确保资源文件放在 assets 目录
        outDir: 'dist' // 确保输出到 dist 目录
    }
});