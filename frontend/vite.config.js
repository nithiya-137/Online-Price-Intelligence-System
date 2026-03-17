import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    const cdnBase = (env.VITE_CDN_BASE || '').trim();

    return {
    // If you deploy static assets behind a CDN, set `VITE_CDN_BASE` to that origin/path.
    // Example: https://cdn.example.com/price-intel/
    base: mode === 'production' && cdnBase ? cdnBase : '/',
    plugins: [react()],
    
    // ============================================================================
    // BUILD OPTIMIZATION
    // ============================================================================
    build: {
        // Target modern browsers
        target: 'esnext',
        
        // Output minified bundle
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: true, // Remove console.logs in production
                drop_debugger: true
            },
            format: {
                comments: false
            }
        },
        
        // Optimize code splitting
        rollupOptions: {
            output: {
                // Manual chunk configuration for better control
                manualChunks: {
                    // Vendor chunks - framework and large dependencies
                    'vendors-react': ['react', 'react-dom', 'react-router-dom'],
                    'vendors-ui': ['@mui/material', '@emotion/react'],
                    'vendors-chart': ['chart.js', 'react-chartjs-2', 'chartjs-plugin-datalabels'],
                    
                    // Feature chunks
                    'auth': ['./src/pages/AuthPage.jsx', './src/pages/ResetPasswordPage.jsx'],
                    'dashboard': ['./src/pages/DashboardPage.jsx'],
                    'comparison': ['./src/pages/ComparisonPage.jsx', './src/pages/ResultsPage.jsx'],
                    'profiles': ['./src/pages/ProfilePage.jsx', './src/pages/WishlistPage.jsx'],
                },
                
                // Generate entry points for each chunk
                entryFileNames: 'js/[name]-[hash].js',
                chunkFileNames: 'js/[name]-[hash].js',
                assetFileNames: (assetInfo) => {
                    const info = assetInfo.name.split('.');
                    const ext = info[info.length - 1];
                    
                    if (/png|jpe?g|gif|svg/.test(ext)) {
                        return `images/[name]-[hash][extname]`;
                    } else if (/woff|woff2|eot|ttf|otf/.test(ext)) {
                        return `fonts/[name]-[hash][extname]`;
                    } else if (ext === 'css') {
                        return `css/[name]-[hash][extname]`;
                    }
                    return `[name]-[hash][extname]`;
                }
            }
        },
        
        // Disable CSS code split for small builds
        cssCodeSplit: true,
        
        // Source maps for production debugging (optional)
        sourcemap: false, // Set to 'hidden' for production security
        
        // Asset inlining threshold (bytes)
        assetsInlineLimit: 4096, // Inline assets < 4KB
        
        // Reporting compressed size
        reportCompressedSize: true,
        
        // Chunk size warnings
        chunkSizeWarningLimit: 1000, // 1MB warning
    },
    
    // ============================================================================
    // OPTIMIZATION
    // ============================================================================
    server: {
        // Enable gzip compression
        middlewareMode: false,
        
        // File change detection
        watch: {
            usePolling: false,
        },
        
        proxy: {
            // Express backend (auth, wishlist, history, alerts, user profile)
            '/api/auth': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            '/api/user': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            '/api/wishlist': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            '/api/search-history': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            '/api/price-alert': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            '/api/analytics': {
                target: 'http://localhost:5001',
                changeOrigin: true,
            },
            // Flask backend (price scraping, image upload, search)
            '/api': {
                target: 'http://localhost:8001',
                proxyTimeout: 60000,
                timeout: 60000,
                changeOrigin: true,
            },
            '/static': {
                target: 'http://localhost:8001',
                proxyTimeout: 60000,
                timeout: 60000,
                changeOrigin: true,
            },
        },
    },
    
    // ============================================================================
    // DEPENDENCY OPTIMIZATION
    // ============================================================================
    optimize: {
        // Preload frequently used dependencies
        esbuild: {
            exclude: ['@tanstack/query']
        }
    }
    }
})

