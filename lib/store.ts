import { generateSeed } from './seed'
import type { Language, UserAnswer } from './types'

const STORE_KEY = 'vadvilljag_v1'

export interface QuizStore {
  seed: string
  questionCount: number
  sampledIds: string[]
  answers: Record<string, UserAnswer>
  currentIndex: number
  language: Language
}

function defaultStore(): QuizStore {
  return {
    seed: generateSeed(),
    questionCount: 50,
    sampledIds: [],
    answers: {},
    currentIndex: 0,
    language: 'sv',
  }
}

export function loadStore(): QuizStore {
  if (typeof window === 'undefined') return defaultStore()
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (!raw) {
      const s = defaultStore()
      saveStore(s)
      return s
    }
    return { ...defaultStore(), ...JSON.parse(raw) }
  } catch {
    return defaultStore()
  }
}

export function saveStore(store: QuizStore): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORE_KEY, JSON.stringify(store))
}
