import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from 'next-themes'
import { Navbar } from '@/components/navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Quant UI - 量化交易策略实盘展示平台',
  description: '专业的量化交易策略实盘展示平台，实时监控策略表现与市场行情',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-terminal-bg text-terminal-text min-h-screen`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 container mx-auto px-4 py-8">
              {children}
            </main>
            <Footer />
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}

function Footer() {
  return (
    <footer className="border-t border-terminal-border bg-terminal-card py-8 mt-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-4">数据透明度说明</h3>
            <p className="text-terminal-muted text-sm">
              本平台展示的所有策略数据均为模拟测试结果，仅供参考。实际交易可能因市场流动性、滑点等因素产生差异。
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">风险提示</h3>
            <p className="text-terminal-muted text-sm">
              量化交易存在风险，过往表现不代表未来收益。投资者应根据自身风险承受能力谨慎决策。
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-4">个人联系方式</h3>
            <div className="space-y-2">
              <a href="https://twitter.com/quant_trader" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-terminal-muted hover:text-primary transition-colors">
                <span>Twitter</span>
              </a>
              <div className="flex items-center gap-2 text-terminal-muted">
                <span>微信: quant_trader</span>
              </div>
              <a href="https://knowledge-planet.com/quant" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-terminal-muted hover:text-primary transition-colors">
                <span>知识星球</span>
              </a>
            </div>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-terminal-border text-center text-terminal-muted text-sm">
          <p>© {new Date().getFullYear()} Quant UI. 保留所有权利。</p>
        </div>
      </div>
    </footer>
  )
}