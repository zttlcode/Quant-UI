import type { Metadata } from 'next'
import { cookies } from 'next/headers'
import { Inter } from 'next/font/google'
import { Space_Grotesk, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from 'next-themes'
import { I18nProvider } from '@/lib/i18n'
import { Navbar } from '@/components/navbar'
import { ParticleBackground } from '@/components/particle-background'
import { Footer } from '@/components/footer'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  weight: ['400', '500', '600', '700'],
})
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  weight: ['400', '500', '600', '700'],
})

function getLocale(): 'zh' | 'en' {
  const cookieStore = cookies()
  const localeCookie = cookieStore.get('NEXT_LOCALE')?.value
  return localeCookie === 'en' ? 'en' : 'zh'
}

export async function generateMetadata(): Promise<Metadata> {
  const locale = getLocale()
  const messages = (await import(`../messages/${locale}.json`)).default
  return {
    title: messages.metadata.title,
    description: messages.metadata.description,
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const locale = getLocale()
  const messages = (await import(`../messages/${locale}.json`)).default

  return (
    <html lang={locale === 'zh' ? 'zh-CN' : 'en'} suppressHydrationWarning>
      <body className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} font-sans bg-background text-foreground min-h-screen`}>
        <I18nProvider locale={locale} messages={messages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
          >
            <div className="min-h-screen flex flex-col relative">
              <ParticleBackground />
              <Navbar />
              <main className="flex-1 relative z-10">
                {children}
              </main>
              <Footer />
            </div>
          </ThemeProvider>
        </I18nProvider>
      </body>
    </html>
  )
}
