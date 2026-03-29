'use client'

import { useState } from 'react'
import type { QuizStore } from '@/lib/store'
import type { Language } from '@/lib/types'

interface Props {
  store: QuizStore
  totalQuestionCount: number
  onStart: (count: number) => void
  onResume: () => void
  onSeeResults: () => void
  onReset: () => void
  onOpenSettings: () => void
  lang: Language
}

const COUNT_OPTIONS = [25, 50, 100]

const T = {
  sv: {
    title: 'VILKET\nPARTI\nTILLHÖR\nJAG?',
    subtitle: 'Ta reda på vilket parti du egentligen håller med',
    how: (n: number, total: number) => `När du startar slumpas ${n} frågor ut från ca ${total} frågeställningar som riksdagen röstat om de senaste fem åren. Dina svar jämförs sedan med hur partierna faktiskt röstade.`,
    fairTitle: 'Varför är det rättvist?',
    fair: 'Alla frågor är hämtade direkt ur riksdagens öppna data utan egna tolkningar. Urvalet är slumpmässigt och baseras enbart på verkliga voteringar.',
    countLabel: 'Antal frågor',
    custom: 'Eget',
    start: 'Starta quiz',
    resumeNote: (n: number, total: number) => `${n} av ${total} besvarade`,
    resume: 'Fortsätt',
    seeResults: 'Se resultat från förra omgången',
    reset: 'Återställ',
    resetConfirm: 'Säker? Tryck igen för att återställa.',
  },
  en: {
    title: 'WHICH\nPARTY\nDO I\nBELONG\nTO?',
    subtitle: 'Find out which party you actually agree with',
    how: (n: number, total: number) => `When you start, ${n} questions are randomly drawn from around ${total} issues the Riksdag has voted on in the last five years. Your answers are then compared to how parties actually voted.`,
    fairTitle: 'Why is it fair?',
    fair: 'All questions are sourced directly from Sweden\'s open parliamentary data with no editorial interpretation. The selection is random and based solely on real recorded votes.',
    countLabel: 'Number of questions',
    custom: 'Custom',
    start: 'Start quiz',
    resumeNote: (n: number, total: number) => `${n} of ${total} answered`,
    resume: 'Continue',
    seeResults: 'See results from last round',
    reset: 'Reset',
    resetConfirm: 'Sure? Tap again to reset.',
  },
}

export default function LandingPage({ store, totalQuestionCount, onStart, onResume, onSeeResults, onReset, onOpenSettings, lang }: Props) {
  const [count, setCount] = useState(store.questionCount)
  const [customInput, setCustomInput] = useState('')
  const [confirmReset, setConfirmReset] = useState(false)
  const t = T[lang]
  const roundedTotal = Math.round(totalQuestionCount / 100) * 100

  const answeredCount = Object.keys(store.answers).length
  const hasOngoing = store.sampledIds.length > 0 && answeredCount > 0 && answeredCount < store.sampledIds.length
  const hasCompleted = store.sampledIds.length > 0 && answeredCount >= store.sampledIds.length
  const hasAny = hasOngoing || hasCompleted

  const handleResetClick = () => {
    if (confirmReset) {
      onReset()
    } else {
      setConfirmReset(true)
    }
  }

  return (
    <div className="min-h-screen flex flex-col max-w-sm mx-auto px-5">
      {/* Hero title + cog on same row */}
      <div className="pt-6 pb-8 animate-fadeUp">
        <div className="flex items-start justify-between mb-4">
          <h1
            className="font-bold text-navy leading-none"
            style={{ fontFamily: 'Syne, sans-serif', fontSize: 'clamp(3.5rem, 18vw, 5rem)', whiteSpace: 'pre-line' }}
          >
            {t.title}
          </h1>
          <button
            onClick={onOpenSettings}
            aria-label="Inställningar"
            className="p-2 -mr-2 mt-1 text-navy/40 hover:text-navy transition-colors shrink-0"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </div>
        <div className="h-1 w-12 bg-gold mb-4" />
        <p className="text-navy/60 text-base leading-relaxed">
          {t.subtitle}
        </p>
      </div>

      {/* Explanation */}
      <div className="mb-8 animate-fadeUp" style={{ animationDelay: '80ms' }}>
        <div className="border-l-2 border-gold pl-4 space-y-3">
          <p className="text-navy/70 text-sm leading-relaxed">{t.how(count, roundedTotal)}</p>
          <p className="text-navy/70 text-sm leading-relaxed">{t.fair}</p>
          <a
            href="https://github.com/mrconter1/vad-vill-jag"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-navy/35 hover:text-navy/60 underline underline-offset-2 transition-colors inline-block"
          >
            Källkod
          </a>
        </div>
      </div>

      {/* Count picker */}
      <div className="mb-8 animate-fadeUp" style={{ animationDelay: '160ms' }}>
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-3">{t.countLabel}</p>
        <div className="flex gap-2">
          {COUNT_OPTIONS.map((n) => (
            <button
              key={n}
              onClick={() => { setCount(n); setCustomInput('') }}
              className={`flex-1 py-4 text-lg font-bold border-2 transition-all active:scale-95 ${
                count === n && customInput === ''
                  ? 'bg-navy text-cream border-navy'
                  : 'bg-transparent text-navy border-navy/20 hover:border-navy/60'
              }`}
            >
              {n}
            </button>
          ))}
          <input
            type="number"
            min={1}
            max={500}
            placeholder={t.custom}
            value={customInput}
            onChange={(e) => {
              const raw = e.target.value
              setCustomInput(raw)
              const v = parseInt(raw)
              if (!isNaN(v) && v >= 1) setCount(Math.min(500, v))
            }}
            className={`w-20 py-4 text-lg font-bold border-2 text-center transition-all bg-transparent outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${
              customInput !== ''
                ? 'bg-navy text-cream border-navy placeholder:text-cream/40'
                : 'text-navy border-navy/20 hover:border-navy/60'
            }`}
          />
        </div>
      </div>

      {/* CTA */}
      <div className="pb-10 space-y-3 animate-fadeUp" style={{ animationDelay: '200ms' }}>
        {hasOngoing ? (
          <>
            <button
              onClick={onResume}
              className="w-full py-5 bg-gold text-navy text-lg font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
              style={{ fontFamily: 'var(--font-syne), sans-serif' }}
            >
              {t.resume} ({t.resumeNote(answeredCount, store.sampledIds.length)}) →
            </button>
            <button
              onClick={handleResetClick}
              onBlur={() => setConfirmReset(false)}
              className="w-full py-3 border border-navy/20 text-navy/50 text-sm hover:border-red-400/50 hover:text-red-600 transition-all"
            >
              {confirmReset ? t.resetConfirm : t.reset}
            </button>
          </>
        ) : hasCompleted ? (
          <>
            <button
              onClick={onSeeResults}
              className="w-full py-5 bg-gold text-navy text-lg font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
              style={{ fontFamily: 'var(--font-syne), sans-serif' }}
            >
              {t.seeResults} →
            </button>
            <button
              onClick={() => onStart(count)}
              className="w-full py-3 border border-navy/20 text-navy/60 text-sm hover:border-navy/40 hover:text-navy transition-all"
            >
              {t.start}
            </button>
            <button
              onClick={handleResetClick}
              onBlur={() => setConfirmReset(false)}
              className="w-full py-3 border border-navy/20 text-navy/50 text-sm hover:border-red-400/50 hover:text-red-600 transition-all"
            >
              {confirmReset ? t.resetConfirm : t.reset}
            </button>
          </>
        ) : (
          <button
            onClick={() => onStart(count)}
            className="w-full py-5 bg-gold text-navy text-lg font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
            style={{ fontFamily: 'var(--font-syne), sans-serif' }}
          >
            {t.start} →
          </button>
        )}
      </div>
    </div>
  )
}
