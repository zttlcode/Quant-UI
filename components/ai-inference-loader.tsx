'use client'

import { useEffect, useState } from 'react'

interface InferenceStep {
  label: string
  duration: number    // ms
}

const INFERENCE_STEPS: InferenceStep[] = [
  { label: 'Extracting Features', duration: 60 },
  { label: 'Embedding Sequences', duration: 50 },
  { label: 'Temporal Block Processing', duration: 80 },
  { label: 'Attention Computing', duration: 70 },
  { label: 'Generating Prediction', duration: 100 },
]

interface AIInferenceLoaderProps {
  onComplete?: (result: 'BUY' | 'SELL' | 'HOLD') => void
  className?: string
}

export function AIInferenceLoader({ onComplete, className }: AIInferenceLoaderProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [complete, setComplete] = useState(false)
  const [result] = useState<'BUY' | 'SELL' | 'HOLD'>(() => {
    const r = Math.random()
    if (r > 0.5) return 'BUY'
    if (r > 0.2) return 'SELL'
    return 'HOLD'
  })

  useEffect(() => {
    if (complete) return

    const totalDuration = INFERENCE_STEPS.reduce((sum, s) => sum + s.duration, 0)
    const stepBoundaries = INFERENCE_STEPS.reduce<number[]>((arr, _, i) => {
      const prev = i === 0 ? 0 : arr[i - 1]
      const prevStepsDuration = INFERENCE_STEPS.slice(0, i).reduce((s, st) => s + st.duration, 0)
      arr.push(prevStepsDuration / totalDuration * 100 + INFERENCE_STEPS[i].duration / totalDuration * 100)
      return arr
    }, [])

    const interval = setInterval(() => {
      setProgress(prev => {
        const next = prev + (Math.random() * 15 + 5)
        if (next >= 100) {
          clearInterval(interval)
          setCurrentStep(INFERENCE_STEPS.length)
          setTimeout(() => {
            setComplete(true)
            onComplete?.(result)
          }, 200)
          return 100
        }

        // Determine current step
        const stepIdx = stepBoundaries.findIndex(boundary => next <= boundary)
        setCurrentStep(stepIdx === -1 ? INFERENCE_STEPS.length - 1 : stepIdx)
        return next
      })
    }, 80)

    return () => clearInterval(interval)
  }, [complete, onComplete, result])

  const barColor =
    result === 'BUY' ? 'bg-quant-green' :
    result === 'SELL' ? 'bg-quant-red' :
    'bg-quant-amber'

  const resultColor =
    result === 'BUY' ? 'text-quant-green' :
    result === 'SELL' ? 'text-quant-red' :
    'text-quant-amber'

  const resultBg =
    result === 'BUY' ? 'bg-quant-green/10 border-quant-green/30' :
    result === 'SELL' ? 'bg-quant-red/10 border-quant-red/30' :
    'bg-quant-amber/10 border-quant-amber/30'

  return (
    <div className={`glass-card-variant p-5 ${className || ''}`}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 bg-quant-cyan rounded-full animate-neural-pulse" />
        <span className="text-xs font-mono text-quant-cyan tracking-wider uppercase">
          AI Inference Engine
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-4">
        <div
          className={`h-full rounded-full transition-all duration-100 ${barColor}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2 mb-4">
        {INFERENCE_STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center justify-between text-xs">
            <span
              className={`font-mono transition-colors ${
                i < currentStep
                  ? 'text-quant-cyan'
                  : i === currentStep
                  ? 'text-quant-cyan animate-pulse'
                  : 'text-terminal-muted'
              }`}
            >
              {step.label}
            </span>
            <span className="font-mono text-terminal-muted">
              {i < currentStep
                ? '████████████'
                : i === currentStep
                ? '████░░░░░░░░'
                : '░░░░░░░░░░░░'}
            </span>
          </div>
        ))}
      </div>

      {/* Result */}
      {complete && (
        <div className={`animate-count-up border rounded-lg p-3 text-center ${resultBg}`}>
          <span className={`text-lg font-bold font-mono ${resultColor}`}>
            → {result} Signal
          </span>
          <p className="text-xs text-terminal-muted mt-1">
            Confidence: {(Math.random() * 20 + 75).toFixed(1)}%
          </p>
        </div>
      )}
    </div>
  )
}
