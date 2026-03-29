'use client'

import { useState } from 'react'
import type { QuizStore } from '@/lib/store'
import type { Language } from '@/lib/types'

interface Props {
  store: QuizStore
  onStart: (count: number) => void
  onNewSeed: () => void
  onOpenSettings: () => void
  lang: Language
}

const COUNT_OPTIONS = [10, 20, 50]

const T = {
  sv: {
    title: 'VAD\nVILL\nJAG?',
    subtitle: 'Ta reda på vilket parti du egentligen håller med',
    how: 'Du svarar på frågor baserade på verkliga riksdagsomröstningar. Dina svar jämförs sedan med hur partierna faktiskt röstade – inga tolkningar, bara fakta från riksdagens öppna data.',
    fairTitle: 'Varför är det rättvist?',
    fair: 'Varje fråga är hämtad direkt ur riksdagsprotokollen. Din slumpkod avgör vilka frågor du får, och alla med samma kod ser exakt samma urval.',
    seedLabel: 'Din kod',
    newSeed: 'ny kod',
    countLabel: 'Antal frågor',
    start: 'Starta quiz',
    resumeNote: (n: number, total: number) => `Du har en pågående omgång (${n} av ${total} besvarade)`,
    resume: 'Fortsätt',
  },
  en: {
    title: 'WHAT\nDO I\nWANT?',
    subtitle: 'Find out which party you actually agree with',
    how: 'You answer questions based on real Riksdag votes. Your answers are compared to how parties actually voted — no interpretations, just facts from Sweden\'s open parliamentary data.',
    fairTitle: 'Why is it fair?',
    fair: 'Every question is sourced directly from parliamentary records. Your random code determines which questions you get — anyone with the same code sees the exact same selection.',
    seedLabel: 'Your code',
    newSeed: 'new code',
    countLabel: 'Number of questions',
    start: 'Start quiz',
    resumeNote: (n: number, total: number) => `You have an ongoing round (${n} of ${total} answered)`,
    resume: 'Continue',
  },
}

export default function LandingPage({ store, onStart, onNewSeed, onOpenSettings, lang }: Props) {
  const [count, setCount] = useState(store.questionCount)
  const t = T[lang]

  const answeredCount = Object.keys(store.answers).length
  const hasOngoing = store.sampledIds.length > 0 && answeredCount < store.sampledIds.length && answeredCount > 0

  return (
    <div className="min-h-screen flex flex-col max-w-sm mx-auto px-5">
      {/* Top bar */}
      <div className="flex justify-end pt-4 pb-2">
        <button
          onClick={onOpenSettings}
          aria-label="Inställningar"
          className="p-2 -mr-2 text-navy/40 hover:text-navy transition-colors"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
      </div>

      {/* Hero title */}
      <div className="pt-6 pb-8 animate-fadeUp">
        <h1
          className="font-bold text-navy leading-none mb-4"
          style={{ fontFamily: 'Syne, sans-serif', fontSize: 'clamp(3.5rem, 18vw, 5rem)', whiteSpace: 'pre-line' }}
        >
          {t.title}
        </h1>
        <div className="h-1 w-12 bg-gold mb-4" />
        <p className="text-navy/60 text-base leading-relaxed">
          {t.subtitle}
        </p>
      </div>

      {/* Explanation */}
      <div className="mb-8 animate-fadeUp" style={{ animationDelay: '80ms' }}>
        <div className="border-l-2 border-gold pl-4 space-y-3">
          <p className="text-navy/70 text-sm leading-relaxed">{t.how}</p>
          <p className="text-navy/70 text-sm leading-relaxed">{t.fair}</p>
        </div>
      </div>

      {/* Seed */}
      <div className="mb-6 animate-fadeUp" style={{ animationDelay: '120ms' }}>
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-2">{t.seedLabel}</p>
        <div className="flex items-baseline gap-3">
          <span
            className="font-mono font-bold text-navy tracking-[0.2em]"
            style={{ fontSize: '1.6rem' }}
          >
            {store.seed}
          </span>
          <button
            onClick={onNewSeed}
            className="text-xs text-navy/40 hover:text-navy underline underline-offset-2 transition-colors"
          >
            {t.newSeed}
          </button>
        </div>
      </div>

      {/* Count picker */}
      <div className="mb-8 animate-fadeUp" style={{ animationDelay: '160ms' }}>
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-3">{t.countLabel}</p>
        <div className="flex gap-2">
          {COUNT_OPTIONS.map((n) => (
            <button
              key={n}
              onClick={() => setCount(n)}
              className={`flex-1 py-4 text-lg font-bold border-2 transition-all active:scale-95 ${
                count === n
                  ? 'bg-navy text-cream border-navy'
                  : 'bg-transparent text-navy border-navy/20 hover:border-navy/60'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="pb-10 space-y-3 animate-fadeUp" style={{ animationDelay: '200ms' }}>
        <button
          onClick={() => onStart(count)}
          className="w-full py-5 bg-gold text-navy text-lg font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          {t.start} →
        </button>

        {hasOngoing && (
          <button
            onClick={() => onStart(store.questionCount)}
            className="w-full py-3 border border-navy/20 text-navy/60 text-sm hover:border-navy/40 hover:text-navy transition-all"
          >
            {t.resumeNote(answeredCount, store.sampledIds.length)}
          </button>
        )}
      </div>
    </div>
  )
}
