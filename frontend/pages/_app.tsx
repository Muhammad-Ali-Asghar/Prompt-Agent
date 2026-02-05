import type { AppProps } from 'next/app'
import Head from 'next/head'
import Link from 'next/link'
import { useRouter } from 'next/router'
import '@/styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
    const router = useRouter()

    return (
        <>
            <Head>
                <title>Prompt RAG Agent</title>
                <meta name="description" content="Generate high-quality prompts with RAG-powered security and best practices" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
            </Head>

            <nav className="nav">
                <div className="container nav-content">
                    <Link href="/" className="nav-brand">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M2 17L12 22L22 17" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M2 12L12 17L22 12" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <defs>
                                <linearGradient id="gradient" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                                    <stop stopColor="#6366f1" />
                                    <stop offset="1" stopColor="#8b5cf6" />
                                </linearGradient>
                            </defs>
                        </svg>
                        Prompt RAG Agent
                    </Link>

                    <div className="nav-links">
                        <Link href="/" className={`nav-link ${router.pathname === '/' ? 'active' : ''}`}>
                            Generate
                        </Link>
                        <Link href="/admin" className={`nav-link ${router.pathname === '/admin' ? 'active' : ''}`}>
                            Admin
                        </Link>
                        <a href="/api/docs" target="_blank" rel="noopener noreferrer" className="nav-link">
                            API Docs
                        </a>
                    </div>
                </div>
            </nav>

            <main style={{ padding: '40px 0' }}>
                <Component {...pageProps} />
            </main>
        </>
    )
}
