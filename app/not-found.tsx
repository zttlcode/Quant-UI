import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="text-6xl font-display font-bold text-gradient-cyan mb-4">404</div>
      <h2 className="text-xl font-display font-bold mb-2">Page Not Found</h2>
      <p className="text-terminal-muted text-sm mb-6">The page you are looking for does not exist.</p>
      <Link href="/"><Button variant="default">Back to Home</Button></Link>
    </div>
  )
}
