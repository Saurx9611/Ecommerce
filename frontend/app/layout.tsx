import type {Metadata} from 'next';
import './globals.css';
import { Sidebar } from '@/components/Sidebar';
import { Header } from '@/components/Header';
import { WishlistProvider } from '@/context/WishlistContext';
import { AuthProvider } from '@/context/AuthContext';
import { CartProvider } from '@/context/CartContext';
import { StockWebSocketProvider } from '@/context/StockWebSocketContext';
import { CartDrawer } from '@/components/CartDrawer';

export const metadata: Metadata = {
  title: 'Podcast Explorer — AI Intelligence Platform & High-Concurrency Engine',
  description: 'AI-powered podcast intelligence with timestamped transcripts, deep-linked playback, and pgvector semantic search.',
  openGraph: {
    title: 'Podcast Explorer — AI Intelligence Platform',
    description: 'AI-powered podcast intelligence with timestamped transcripts, deep-linked playback, and pgvector semantic search.',
    type: 'website',
  },
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body className="bg-[#F9FAFB] text-[#111827] flex h-screen overflow-hidden antialiased selection:bg-[#F0F9FF] selection:text-[#0EA5E9]" suppressHydrationWarning>
        <AuthProvider>
          <WishlistProvider>
            <CartProvider>
              <StockWebSocketProvider>
                <Sidebar />
                <div className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
                  <Header />
                  <main className="flex-1 overflow-y-auto">
                    {children}
                  </main>
                </div>
                <CartDrawer />
              </StockWebSocketProvider>
            </CartProvider>
          </WishlistProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
