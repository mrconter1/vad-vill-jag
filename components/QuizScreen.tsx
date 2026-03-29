'use client'

import { useEffect } from 'react'
import type { Question, Language, UserAnswer } from '@/lib/types'

interface Props {
  question: Question
  questionNumber: number
  totalQuestions: number
  existingAnswer: UserAnswer | null
  onAnswer: (answer: UserAnswer) => void
  onPrev: (() => void) | null
  onNextNav: (() => void) | null
  onOpenSettings: () => void
  lang: Language
}

const T = {
  sv: {
    questionLabel: 'Fråga',
    of: 'av',
    ja: 'JA',
    nej: 'NEJ',
    skip: 'Ingen åsikt',
    source: 'Källa',
  },
  en: {
    questionLabel: 'Question',
    of: 'of',
    ja: 'YES',
    nej: 'NO',
    skip: 'No opinion',
    source: 'Source',
  },
}

export default function QuizScreen({
  question,
  questionNumber,
  totalQuestions,
  existingAnswer,
  onAnswer,
  onPrev,
  onNextNav,
  onOpenSettings,
  lang,
}: Props) {
  const t = T[lang]
  const questionText = lang === 'sv' ? question.question_sv : question.question_en
  const category = (lang === 'sv' ? question.category_sv : question.category_en) || question.category_code
  const progress = questionNumber / totalQuestions

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') onNextNav ? onNextNav() : onAnswer('for')
      if (e.key === 'ArrowLeft') onPrev ? onPrev() : onAnswer('against')
      if (e.key === 'ArrowDown') onAnswer('skip')
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onAnswer, onPrev, onNextNav])

  const btnBase = 'flex-1 py-5 border-2 transition-all active:scale-95'

  return (
    <div className="min-h-screen flex flex-col max-w-sm mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-4 pb-2">
        <span className="text-xs font-mono text-navy/40">
          {t.questionLabel} {questionNumber} {t.of} {totalQuestions}
        </span>
        <button
          onClick={onOpenSettings}
          aria-label="Inställningar"
          className="p-2 -mr-2 text-navy/30 hover:text-navy transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-[3px] bg-navy/10 mx-5">
        <div
          className="h-[3px] bg-gold transition-all duration-500 ease-out"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col px-5 pt-6 pb-6">
        {/* Category */}
        <div className="mb-6">
          <span className="text-[11px] uppercase tracking-[0.12em] text-navy/40 border border-navy/15 px-2 py-1">
            {category}
          </span>
        </div>

        {/* Question text */}
        <div className="flex-1">
          <p className="text-navy text-[1.25rem] font-semibold leading-snug">
            {questionText}
          </p>
        </div>

        {/* Answer buttons */}
        <div className="flex gap-2 pt-6">
          <button
            onClick={() => onAnswer('against')}
            className={`${btnBase} text-lg font-black ${
              existingAnswer === 'against'
                ? 'border-red-600 bg-red-600 text-white'
                : 'border-navy/15 text-navy/60 hover:border-red-400/60 hover:text-red-600'
            }`}
            style={{ fontFamily: 'var(--font-syne), sans-serif' }}
          >
            {t.nej}
          </button>
          <button
            onClick={() => onAnswer('skip')}
            className={`${btnBase} text-xs font-semibold ${
              existingAnswer === 'skip'
                ? 'border-navy bg-navy text-cream'
                : 'border-navy/15 text-navy/40 hover:border-navy/40 hover:text-navy/60'
            }`}
          >
            {t.skip}
          </button>
          <button
            onClick={() => onAnswer('for')}
            className={`${btnBase} text-lg font-black ${
              existingAnswer === 'for'
                ? 'border-green-600 bg-green-600 text-white'
                : 'border-navy/15 text-navy/60 hover:border-green-500/60 hover:text-green-700'
            }`}
            style={{ fontFamily: 'var(--font-syne), sans-serif' }}
          >
            {t.ja}
          </button>
        </div>

        {/* Nav buttons */}
        <div className="flex gap-2 mt-2">
          <button
            onClick={onPrev ?? undefined}
            disabled={!onPrev}
            className="flex-1 py-2 border border-navy/10 text-navy/25 hover:border-navy/25 hover:text-navy/50 transition-all text-sm disabled:opacity-20 disabled:cursor-not-allowed"
          >
            ←
          </button>
          <div className="flex-1" />
          <button
            onClick={onNextNav ?? undefined}
            disabled={!onNextNav}
            className="flex-1 py-2 border border-navy/10 text-navy/25 hover:border-navy/25 hover:text-navy/50 transition-all text-sm disabled:opacity-20 disabled:cursor-not-allowed"
          >
            →
          </button>
        </div>

        {/* Vote reference */}
        <div className="pt-4 flex items-start justify-between gap-3">
          <div>
            <span className="text-[11px] font-mono text-navy/30">{question.beteckning} · {question.rm}</span>
            {question.rubrik && (
              <p className="text-[11px] text-navy/30 mt-0.5 leading-snug">{question.rubrik}</p>
            )}
          </div>
          <a
            href={question.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-navy/25 hover:text-navy/50 underline underline-offset-2 transition-colors shrink-0"
          >
            {t.source}
          </a>
        </div>
      </div>
    </div>
  )
}
