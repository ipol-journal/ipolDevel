import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "{ } IPOL DDL Docs",
  description: "Demo Description Lines (DDL) for IPOL Demo System",
  base: '/cp2/guide/',
  outDir: '../../cp2/ControlPanel/static_cp/ddl_doc',
  mpa: true,
  vite: {
    build: {
      assetsInlineLimit: 16384, // inline assets < 16kb
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              return 'vendor';
            }
            if (id.includes('.md')) {
              return 'pages';
            }
          }
        }
      }
    }
  },
  
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      {
        text: 'Sections',
        items: [
          { text: 'General', link: '/general' },
          { text: 'Build', link: '/build' },
          { text: 'Inputs', link: '/inputs' },
          { text: 'Params', link: '/params' },
          { text: 'Run', link: '/run' },
          { text: 'Archive', link: '/archive' },
          { text: 'Results', link: '/results' }
        ]
      },
      { text: 'Back to CP', link: '../', target: '_self', rel: 'next' }
    ],
    
    sidebar: [
      {
        text: 'Introduction',
        items: [
          { text: 'What is DDL?', link: '/' }
        ]
      },
      {
        text: 'DDL Sections',
        items: [
          { text: 'General Section', link: '/general' },
          { text: 'Build Section', link: '/build' },
          { text: 'Inputs Section', link: '/inputs' },
          { text: 'Params Section', link: '/params' },
          { text: 'Run Section', link: '/run' },
          { text: 'Archive Section', link: '/archive' },
          { text: 'Results Section', link: '/results' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/ipol-journal/ipolDevel' }
    ],
    
    footer: {
      copyright: 'Copyright © 2026 IPOL'
    }
  }
})
