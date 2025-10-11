import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import svgr from 'vite-plugin-svgr';
import compression from 'vite-plugin-compression';
import { viteSingleFile } from 'vite-plugin-singlefile'

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [preact(), svgr(), viteSingleFile(), compression({
		verbose: true,      // 打印压缩信息
		disable: false,     // 是否启用
		threshold: 0,       // 文件大小 >= threshold 才压缩 (字节)
		algorithm: 'gzip',  // 'gzip' | 'brotliCompress'
		ext: '.gz'          // 输出扩展名
	})],
});
