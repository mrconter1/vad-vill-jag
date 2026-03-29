'use client'

import type { Language } from '@/lib/types'

interface Props {
  lang: Language
  onSetLang: (lang: Language) => void
  onReset: () => void
  onNewRound: () => void
  onClose: () => void
}

const T = {
  sv: {
    title: 'Inställningar',
    language: 'Språk',
    sv: '🇸🇪 Svenska',
    en: '🇬🇧 English',
    reset: 'Återställ',
    resetDesc: 'Börja om med nya frågor',
    newRound: 'Ny omgång',
    newRoundDesc: 'Ny slumpkod och nya frågor',
    close: 'Stäng',
  },
  en: {
    title: 'Settings',
    language: 'Language',
    sv: '🇸🇪 Swedish',
    en: '🇬🇧 English',
    reset: 'Reset',
    resetDesc: 'Start over with new questions',
    newRound: 'New round',
    newRoundDesc: 'New random code and new questions',
    close: 'Close',
  },
}

export default function SettingsModal({ lang, onSetLang, onReset, onNewRound, onClose }: Props) {
  const t = T[lang]

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-navy/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Bottom sheet */}
      <div className="relative w-full max-w-sm bg-cream border-t-4 border-navy animate-slideUp">
        <div className="px-6 pt-6 pb-10">
          {/* Header */}
          <div className="flex items-center justify-between mb-7">
            <h2
              className="font-black text-navy text-xl"
              style={{ fontFamily: 'Syne, sans-serif' }}
            >
              {t.title}
            </h2>
            <button
              onClick={onClose}
              className="p-1 text-navy/40 hover:text-navy transition-colors text-lg leading-none"
              aria-label="Stäng"
            >
              ✕
            </button>
          </div>

          {/* Language */}
          <div className="mb-6">
            <p className="text-[11px] uppercase tracking-[0.15em] text-navy/40 mb-3">
              {t.language}
            </p>
            <div className="flex gap-2">
              {(['sv', 'en'] as Language[]).map((l) => (
                <button
                  key={l}
                  onClick={() => onSetLang(l)}
                  className={`flex-1 py-3 text-sm font-bold border-2 transition-all ${
                    lang === l
                      ? 'bg-navy text-cream border-navy'
                      : 'border-navy/20 text-navy hover:border-navy/50'
                  }`}
                >
                  {t[l]}
                </button>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-navy/8 mb-4" />

          {/* Reset */}
          <button
            onClick={onReset}
            className="w-full py-4 mb-2 border border-navy/15 text-left px-4 hover:bg-navy/4 transition-all group"
          >
            <div className="font-semibold text-navy text-sm group-hover:text-navy">
              {t.reset}
            </div>
            <div className="text-navy/40 text-xs mt-0.5">{t.resetDesc}</div>
          </button>

          {/* New round */}
          <button
            onClick={onNewRound}
            className="w-full py-4 border border-navy/15 text-left px-4 hover:bg-navy/4 transition-all group"
          >
            <div className="font-semibold text-navy text-sm">{t.newRound}</div>
            <div className="text-navy/40 text-xs mt-0.5">{t.newRoundDesc}</div>
          </button>
        </div>
      </div>
    </div>
  )
}
