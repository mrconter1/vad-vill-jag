'use client'

import type { Question, Language, UserAnswer, Party } from '@/lib/types'
import { PARTIES, PARTY_COLORS, PARTY_NAMES } from '@/lib/types'

interface Props {
  questions: Question[]
  answers: Record<string, UserAnswer>
  onPlayAgain: () => void
  onNewRound: () => void
  onOpenSettings: () => void
  lang: Language
}

const T = {
  sv: {
    done: 'Klart!',
    answered: (n: number) => `Du svarade på ${n} frågor`,
    alignment: 'Partiöverensstämmelse',
    mostAligned: (party: string) => `Du är mest ense med ${party}`,
    playAgain: 'Spela igen (samma frågor)',
    newRound: 'Ny omgång',
    agreeLabel: 'av frågorna',
  },
  en: {
    done: 'Done!',
    answered: (n: number) => `You answered ${n} questions`,
    alignment: 'Party alignment',
    mostAligned: (party: string) => `You agree most with ${party}`,
    playAgain: 'Play again (same questions)',
    newRound: 'New round',
    agreeLabel: 'of questions',
  },
}

export default function ResultScreen({
  questions,
  answers,
  onPlayAgain,
  onNewRound,
  onOpenSettings,
  lang,
}: Props) {
  const t = T[lang]

  const partyStats = PARTIES.reduce(
    (acc, party) => {
      acc[party] = { agreed: 0, total: 0 }
      return acc
    },
    {} as Record<Party, { agreed: number; total: number }>,
  )

  questions.forEach((q) => {
    const userAnswer = answers[q.id]
    if (!userAnswer) return
    PARTIES.forEach((party) => {
      const stance = q.party_stances[party]
      if (stance && stance !== 'abstain') {
        partyStats[party].total++
        if (stance === userAnswer) {
          partyStats[party].agreed++
        }
      }
    })
  })

  const alignments = PARTIES.map((party) => ({
    party,
    pct: partyStats[party].total > 0
      ? Math.round((partyStats[party].agreed / partyStats[party].total) * 100)
      : 0,
    agreed: partyStats[party].agreed,
    total: partyStats[party].total,
  })).sort((a, b) => b.pct - a.pct)

  const top = alignments[0]
  const maxPct = alignments[0]?.pct ?? 100

  return (
    <div className="min-h-screen flex flex-col max-w-sm mx-auto px-5">
      {/* Header */}
      <div className="flex justify-end pt-4 pb-2">
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

      {/* Title */}
      <div className="pt-4 pb-6 animate-fadeUp">
        <h1
          className="font-black text-navy leading-none mb-2"
          style={{ fontFamily: 'Syne, sans-serif', fontSize: '3.5rem' }}
        >
          {t.done}
        </h1>
        <p className="text-navy/50 text-sm">{t.answered(questions.length)}</p>
      </div>

      {/* Top match */}
      {top && (
        <div className="mb-8 animate-fadeUp" style={{ animationDelay: '60ms' }}>
          <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-2">
            {t.mostAligned(PARTY_NAMES[top.party as Party] || top.party)}
          </p>
          <div className="flex items-end gap-3">
            <span
              className="font-black leading-none"
              style={{
                fontFamily: 'Syne, sans-serif',
                fontSize: '4rem',
                color: PARTY_COLORS[top.party as Party],
              }}
            >
              {top.pct}%
            </span>
            <span
              className="text-2xl font-black mb-2"
              style={{ color: PARTY_COLORS[top.party as Party] }}
            >
              {top.party}
            </span>
          </div>
        </div>
      )}

      {/* All party bars */}
      <div className="mb-10 animate-fadeUp" style={{ animationDelay: '120ms' }}>
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-4">
          {t.alignment}
        </p>
        <div className="space-y-3">
          {alignments.map(({ party, pct, agreed, total }, i) => (
            <div key={party} className="flex items-center gap-3">
              <span
                className="text-xs font-black w-7 shrink-0 text-right"
                style={{ color: PARTY_COLORS[party as Party] }}
              >
                {party}
              </span>
              <div className="flex-1 h-7 bg-navy/8 overflow-hidden">
                <div
                  className="h-7 flex items-center justify-end pr-2 transition-all"
                  style={{
                    width: maxPct > 0 ? `${(pct / maxPct) * 100}%` : '0%',
                    backgroundColor: PARTY_COLORS[party as Party] + (i === 0 ? 'dd' : '88'),
                    animationDelay: `${120 + i * 50}ms`,
                  }}
                >
                  {pct > 20 && (
                    <span className="text-[11px] font-bold text-white">{pct}%</span>
                  )}
                </div>
              </div>
              {pct <= 20 && (
                <span className="text-[11px] text-navy/40 w-8 shrink-0">{pct}%</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Buttons */}
      <div className="pb-10 flex flex-col gap-3 animate-fadeUp" style={{ animationDelay: '200ms' }}>
        <button
          onClick={onNewRound}
          className="w-full py-5 bg-gold text-navy text-base font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          {t.newRound} →
        </button>
        <button
          onClick={onPlayAgain}
          className="w-full py-4 border-2 border-navy/20 text-navy/60 text-sm hover:border-navy hover:text-navy transition-all"
        >
          {t.playAgain}
        </button>
      </div>
    </div>
  )
}
