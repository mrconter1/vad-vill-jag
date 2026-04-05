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
    skipRows: ['Vet inte', 'Ingen åsikt'] as const,
    skip: 'Vet inte / Ingen åsikt',
    alignment: 'Partiöverensstämmelse',
    mostAligned: (party: string) => `Mest ense med ${party}`,
    playAgain: 'Spela igen (samma frågor)',
    newRound: 'Ny omgång',
    breakdown: 'Fråga för fråga',
    yourAnswer: 'Du',
    for: 'Ja',
    against: 'Nej',
    source: 'Källa',
    agreed: 'höll med',
    disagreed: 'höll inte med',
  },
  en: {
    done: 'Done!',
    answered: (n: number) => `You answered ${n} questions`,
    skip: 'No opinion',
    alignment: 'Party alignment',
    mostAligned: (party: string) => `Most aligned with ${party}`,
    playAgain: 'Play again (same questions)',
    newRound: 'New round',
    breakdown: 'Question by question',
    yourAnswer: 'You',
    for: 'Yes',
    against: 'No',
    source: 'Source',
    agreed: 'agreed',
    disagreed: 'disagreed',
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
    if (!userAnswer || userAnswer === 'skip') return
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
      <div className="pt-2 pb-6 animate-fadeUp">
        <h1
          className="font-black text-navy leading-none mb-2"
          style={{ fontFamily: 'var(--font-syne), sans-serif', fontSize: '3.5rem' }}
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
                fontFamily: 'var(--font-syne), sans-serif',
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

      {/* Party alignment bars */}
      <div className="mb-8 animate-fadeUp" style={{ animationDelay: '120ms' }}>
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-4">
          {t.alignment}
        </p>
        <div className="space-y-3">
          {alignments.map(({ party, pct }, i) => (
            <div key={party} className="flex items-center gap-3">
              <span
                className="text-xs font-black w-7 shrink-0 text-right"
                style={{ color: PARTY_COLORS[party as Party] }}
              >
                {party}
              </span>
              <div className="flex-1 h-7 bg-navy/8 overflow-hidden">
                <div
                  className="h-7 flex items-center justify-end pr-2"
                  style={{
                    width: maxPct > 0 ? `${(pct / maxPct) * 100}%` : '0%',
                    backgroundColor: PARTY_COLORS[party as Party] + (i === 0 ? 'dd' : '88'),
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

      {/* Action buttons */}
      <div className="flex flex-col gap-3 mb-12 animate-fadeUp" style={{ animationDelay: '180ms' }}>
        <button
          onClick={onNewRound}
          className="w-full py-5 bg-gold text-navy text-base font-bold tracking-wide hover:bg-amber-400 active:scale-95 transition-all"
          style={{ fontFamily: 'var(--font-syne), sans-serif' }}
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

      {/* Per-question breakdown */}
      <div className="pb-16 animate-fadeUp" style={{ animationDelay: '220ms' }}>
        <div className="h-px bg-navy/10 mb-8" />
        <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-6">
          {t.breakdown}
        </p>
        <div className="space-y-6">
          {questions.map((q, idx) => {
            const userAnswer = answers[q.id]
            if (!userAnswer) return null
            if (userAnswer === 'skip') return (
              <div key={q.id} className="border-l-2 border-navy/10 pl-4 opacity-50">
                <p className="text-[11px] font-mono text-navy/30 mb-1">{idx + 1}. {q.beteckning}</p>
                <p className="text-navy/60 text-sm leading-snug mb-1">{lang === 'sv' ? q.question_sv : q.question_en}</p>
                <span className="text-[11px] text-navy/40 italic flex flex-col items-start gap-0 leading-tight">
                  {lang === 'sv' ? (
                    <>
                      <span>{T.sv.skipRows[0]}</span>
                      <span className="text-navy/30 not-italic">/</span>
                      <span>{T.sv.skipRows[1]}</span>
                    </>
                  ) : (
                    t.skip
                  )}
                </span>
              </div>
            )
            const questionText = lang === 'sv' ? q.question_sv : q.question_en

            const partyResults = PARTIES.map((p) => {
              const stance = q.party_stances[p]
              const agrees = stance === userAnswer
              const abstains = stance === 'abstain' || !stance
              return { party: p, agrees, abstains }
            })

            const agreeParties = partyResults.filter((p) => !p.abstains && p.agrees).map((p) => p.party)
            const disagreeParties = partyResults.filter((p) => !p.abstains && !p.agrees).map((p) => p.party)

            return (
              <div key={q.id} className="border-l-2 border-navy/10 pl-4">
                <p className="text-[11px] font-mono text-navy/30 mb-1">
                  {idx + 1}. {q.beteckning}
                </p>
                <p className="text-navy/80 text-sm leading-snug mb-3">{questionText}</p>

                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 ${
                      userAnswer === 'for'
                        ? 'bg-green-700 text-white'
                        : 'bg-red-700 text-white'
                    }`}
                  >
                    {t.yourAnswer}: {userAnswer === 'for' ? t.for : t.against}
                  </span>
                </div>

                <div className="flex gap-3 flex-wrap">
                  {agreeParties.length > 0 && (
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] text-green-700 font-semibold">{t.agreed}:</span>
                      {agreeParties.map((p) => (
                        <span
                          key={p}
                          className="text-[10px] font-black"
                          style={{ color: PARTY_COLORS[p as Party] }}
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                  {disagreeParties.length > 0 && (
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] text-red-700/70 font-semibold">{t.disagreed}:</span>
                      {disagreeParties.map((p) => (
                        <span
                          key={p}
                          className="text-[10px] font-black opacity-50"
                          style={{ color: PARTY_COLORS[p as Party] }}
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
