export interface Question {
  id: string
  datum: string
  rm: string
  beteckning: string
  titel: string
  punkt: string
  rubrik: string
  type: string
  category_code: string
  category_sv: string
  category_en: string
  question_sv: string
  question_en: string
  url: string
  party_stances: Record<string, PartyStance>
}

export type Language = 'sv' | 'en'
export type UserAnswer = 'for' | 'against'
export type PartyStance = 'for' | 'against' | 'abstain'

export const PARTIES = ['S', 'SD', 'M', 'V', 'C', 'KD', 'MP', 'L'] as const
export type Party = (typeof PARTIES)[number]

export const PARTY_COLORS: Record<Party, string> = {
  S: '#E8112D',
  SD: '#0047A3',
  M: '#52BDEC',
  V: '#C50A0A',
  C: '#009933',
  KD: '#231F72',
  MP: '#83CF39',
  L: '#6BB7E0',
}

export const PARTY_NAMES: Record<Party, string> = {
  S: 'Socialdemokraterna',
  SD: 'Sverigedemokraterna',
  M: 'Moderaterna',
  V: 'Vänsterpartiet',
  C: 'Centerpartiet',
  KD: 'Kristdemokraterna',
  MP: 'Miljöpartiet',
  L: 'Liberalerna',
}
