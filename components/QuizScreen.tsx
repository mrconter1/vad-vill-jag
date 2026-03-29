'use client'

import { useState } from 'react'
import type { Question, Language, UserAnswer, Party } from '@/lib/types'
import { PARTIES, PARTY_COLORS, PARTY_NAMES } from '@/lib/types'

interface Props {
  question: Question
  questionNumber: number
  totalQuestions: number
  existingAnswer: UserAnswer | null
  onAnswer: (answer: UserAnswer) => void
  onNext: () => void
  onOpenSettings: () => void
  lang: Language
}

const T = {
  sv: {
    questionLabel: 'Fråga',
    of: 'av',
    youAnswered: 'Du svarade',
    agreed: 'partier höll med',
    next: 'Nästa fråga',
    last: 'Se resultat',
    ja: 'JA',
    nej: 'NEJ',
    for: 'Ja',
    against: 'Nej',
    abstain: 'Avstår',
    source: 'Källa',
  },
  en: {
    questionLabel: 'Question',
    of: 'of',
    youAnswered: 'You answered',
    agreed: 'parties agreed',
    next: 'Next question',
    last: 'See results',
    ja: 'YES',
    nej: 'NO',
    for: 'Yes',
    against: 'No',
    abstain: 'Abstain',
    source: 'Source',
  },
}

export default function QuizScreen({
  question,
  questionNumber,
  totalQuestions,
  existingAnswer,
  onAnswer,
  onNext,
  onOpenSettings,
  lang,
}: Props) {
  const [answered, setAnswered] = useState<UserAnswer | null>(existingAnswer)
  const t = T[lang]

  const questionText = lang === 'sv' ? question.question_sv : question.question_en
  const category = (lang === 'sv' ? question.category_sv : question.category_en) || question.category_code
  const progress = questionNumber / totalQuestions
  const isLast = questionNumber === totalQuestions

  const handleAnswer = (ans: UserAnswer) => {
    if (answered) return
    setAnswered(ans)
    onAnswer(ans)
  }

  const partyResults = PARTIES.map((p) => {
    const stance = question.party_stances[p]
    const agrees = answered !== null && stance === answered
    const disagrees = answered !== null && stance !== 'abstain' && stance !== answered
    return { party: p, stance: stance ?? 'abstain', agrees, disagrees }
  })

  const agreeCount = partyResults.filter((p) => p.agrees).length

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
      <div className="flex-1 flex flex-col px-5 pt-5 pb-5">
        {/* Category */}
        <div className="mb-5">
          <span className="text-[11px] uppercase tracking-[0.12em] text-navy/40 border border-navy/15 px-2 py-1">
            {category}
          </span>
        </div>

        {/* Question text */}
        <div className="flex-1 mb-6">
          <p className="text-navy text-[1.2rem] font-semibold leading-snug">
            {questionText}
          </p>
        </div>

        {/* Revealed state */}
        {answered && (
          <div className="animate-fadeUp">
            {/* Summary line */}
            <div className="flex items-center gap-2 mb-4">
              <span
                className={`text-sm font-bold px-3 py-1 ${
                  answered === 'for'
                    ? 'bg-green-700 text-white'
                    : 'bg-red-700 text-white'
                }`}
              >
                {answered === 'for' ? t.ja : t.nej}
              </span>
              <span className="text-xs text-navy/50">
                {agreeCount} {t.agreed}
              </span>
            </div>

            {/* Party grid */}
            <div className="grid grid-cols-4 gap-[6px] mb-5">
              {partyResults.map(({ party, agrees, disagrees, stance }) => (
                <div
                  key={party}
                  className={`flex flex-col items-center justify-center py-3 border transition-all ${
                    agrees
                      ? 'border-green-500/50 bg-green-50'
                      : disagrees
                        ? 'border-red-400/40 bg-red-50'
                        : 'border-navy/10 bg-white/50'
                  }`}
                  title={PARTY_NAMES[party as Party]}
                >
                  <span
                    className="text-xs font-black mb-[3px]"
                    style={{ color: PARTY_COLORS[party as Party] }}
                  >
                    {party}
                  </span>
                  <span className="text-[11px] text-navy/50 font-medium">
                    {stance === 'for' ? t.for : stance === 'against' ? t.against : t.abstain}
                  </span>
                </div>
              ))}
            </div>

            {/* Source */}
            <a
              href={question.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-[11px] text-navy/25 hover:text-navy/50 mb-5 transition-colors"
            >
              {t.source}: {question.beteckning} {question.rm}
            </a>

            {/* Next button */}
            <button
              onClick={onNext}
              className="w-full py-4 bg-navy text-cream text-base font-bold tracking-wide hover:bg-navy/90 active:scale-95 transition-all"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              {isLast ? t.last : t.next} →
            </button>
          </div>
        )}

        {/* Answer buttons */}
        {!answered && (
          <div className="flex flex-col gap-3">
            <button
              onClick={() => handleAnswer('for')}
              className="w-full py-6 bg-green-700 text-white text-2xl font-black tracking-widest hover:bg-green-800 active:scale-95 transition-all"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              {t.ja}
            </button>
            <button
              onClick={() => handleAnswer('against')}
              className="w-full py-6 bg-red-700 text-white text-2xl font-black tracking-widest hover:bg-red-800 active:scale-95 transition-all"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              {t.nej}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
