'use client'

import { useEffect, useState } from 'react'
import Particles from '@tsparticles/react'
import type { ISourceOptions } from '@tsparticles/engine'

export function ParticleBackground() {
  const [mounted, setMounted] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    setIsMobile(window.innerWidth < 768)
    setMounted(true)
  }, [])

  if (!mounted) return null

  const options: ISourceOptions = {
    fpsLimit: isMobile ? 30 : 60,
    particles: {
      number: {
        value: isMobile ? 30 : 80,
        density: { enable: true },
      },
      color: {
        value: ['#2563EB', '#1D4ED8', '#16A34A'],
      },
      opacity: {
        value: { min: 0.05, max: 0.2 },
      },
      size: {
        value: { min: 1, max: 3 },
      },
      move: {
        enable: true,
        speed: 0.3,
        direction: 'none',
        random: true,
        straight: false,
        outModes: { default: 'bounce' },
      },
      links: {
        enable: true,
        distance: 150,
        color: '#2563EB',
        opacity: 0.05,
        width: 0.5,
      },
      interactivity: {
        detectsOn: 'window',
        events: {
          onHover: {
            enable: true,
            mode: 'grab',
            parallax: { enable: true, force: 200, smooth: 10 },
          },
        },
        modes: {
          grab: {
            distance: 200,
            links: { opacity: 0.15, color: '#00F5FF' },
          },
        },
      },
    },
    detectRetina: true,
    smooth: true,
  }

  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Particles
        id="tsparticles"
        options={options}
        className="pointer-events-auto"
      />
    </div>
  )
}
