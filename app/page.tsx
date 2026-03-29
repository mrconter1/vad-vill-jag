'use client'

import { useState, useEffect, useCallback } from 'react'
import { loadStore, saveStore, type QuizStore } from '@/lib/store'
import { sampleQuestions, generateSeed } from '@/lib/seed'
import type { Question, Language, UserAnswer } from '@/lib/types'
import LandingPage from '@/components/LandingPage'
import QuizScreen from '@/components/QuizScreen'
import ResultScreen from '@/components/ResultScreen'
import SettingsModal from '@/components/SettingsModal'

type View = 'landing' | 'quiz' | 'results'

export default function Page() {
  const [allQuestions, setAllQuestions] = useState<Question[]>([])
  const [store, setStore] = useState<QuizStore | null>(null)
  const [view, setView] = useState<View>('landing')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/questions.json')
      .then((r) => r.json())
      .then((data: Question[]) => {
        setAllQuestions(data)
        const s = loadStore()
        setStore(s)
        // Always start at landing — resume/results accessible via buttons
        setLoading(false)
      })
  }, [])

  const updateStore = useCallback((updates: Partial<QuizStore>) => {
    setStore((prev) => {
      if (!prev) return prev
      const next = { ...prev, ...updates }
      saveStore(next)
      return next
    })
  }, [])

  const handleStart = (count: number) => {
    if (!store || allQuestions.length === 0) return
    const sampled = sampleQuestions(allQuestions, store.seed, count)
    updateStore({
      questionCount: count,
      sampledIds: sampled.map((q) => q.id),
      answers: {},
      currentIndex: 0,
    })
    setView('quiz')
  }

  const handleAnswer = (answer: UserAnswer) => {
    if (!store) return
    const questionId = store.sampledIds[store.currentIndex]
    const newAnswers = { ...store.answers, [questionId]: answer }
    const nextIndex = store.currentIndex + 1
    if (nextIndex >= store.sampledIds.length) {
      updateStore({ answers: newAnswers })
      setView('results')
    } else {
      updateStore({ answers: newAnswers, currentIndex: nextIndex })
    }
  }

  const handlePrev = () => {
    if (!store || store.currentIndex === 0) return
    updateStore({ currentIndex: store.currentIndex - 1 })
  }

  const handleNextNav = () => {
    if (!store) return
    const nextIndex = store.currentIndex + 1
    if (nextIndex >= store.sampledIds.length) {
      setView('results')
    } else {
      updateStore({ currentIndex: nextIndex })
    }
  }

  const handleNewSeed = () => {
    updateStore({ seed: generateSeed(), sampledIds: [], answers: {}, currentIndex: 0 })
  }

  const handleReset = () => {
    updateStore({ answers: {}, currentIndex: 0 })
    setView('quiz')
    setSettingsOpen(false)
  }

  const handleFullReset = () => {
    updateStore({ sampledIds: [], answers: {}, currentIndex: 0 })
    setView('landing')
  }

  const handleNewRound = () => {
    updateStore({ seed: generateSeed(), sampledIds: [], answers: {}, currentIndex: 0 })
    setView('landing')
    setSettingsOpen(false)
  }

  const handleSetLang = (language: Language) => {
    updateStore({ language })
  }

  if (loading || !store) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="text-navy/30 text-sm font-mono tracking-widest">Laddar…</span>
      </div>
    )
  }

  const sampledQuestions = store.sampledIds
    .map((id) => allQuestions.find((q) => q.id === id))
    .filter((q): q is Question => !!q)

  const currentQuestion = sampledQuestions[store.currentIndex]

  return (
    <>
      {view === 'landing' && (
        <LandingPage
          store={store}
          totalQuestionCount={allQuestions.length}
          onStart={handleStart}
          onResume={() => setView('quiz')}
          onSeeResults={() => setView('results')}
          onReset={handleFullReset}
          onOpenSettings={() => setSettingsOpen(true)}
          lang={store.language}
        />
      )}

      {view === 'quiz' && currentQuestion && (
        <QuizScreen
          key={currentQuestion.id}
          question={currentQuestion}
          questionNumber={store.currentIndex + 1}
          totalQuestions={store.sampledIds.length}
          existingAnswer={store.answers[currentQuestion.id] ?? null}
          onAnswer={handleAnswer}
          onPrev={store.currentIndex > 0 ? handlePrev : null}
          onNextNav={store.currentIndex < store.sampledIds.length - 1 ? handleNextNav : (store.answers[currentQuestion.id] ? handleNextNav : null)}
          onOpenSettings={() => setSettingsOpen(true)}
          lang={store.language}
        />
      )}

      {view === 'quiz' && !currentQuestion && sampledQuestions.length === 0 && (
        <LandingPage
          store={store}
          totalQuestionCount={allQuestions.length}
          onStart={handleStart}
          onResume={() => setView('quiz')}
          onSeeResults={() => setView('results')}
          onReset={handleFullReset}
          onOpenSettings={() => setSettingsOpen(true)}
          lang={store.language}
        />
      )}

      {view === 'results' && (
        <ResultScreen
          questions={sampledQuestions}
          answers={store.answers}
          onPlayAgain={handleReset}
          onNewRound={handleNewRound}
          onOpenSettings={() => setSettingsOpen(true)}
          lang={store.language}
        />
      )}

      {settingsOpen && (
        <SettingsModal
          lang={store.language}
          onSetLang={handleSetLang}
          onReset={handleReset}
          onNewRound={handleNewRound}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </>
  )
}
