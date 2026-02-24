import React, { useState, useEffect } from 'react'
import { Brain, ChevronRight, Calendar, User, CheckCircle, AlertTriangle, Award, XCircle } from 'lucide-react'
import { MockTask, quizQuestionsData, QuizQuestionData } from '../../data/mockTasks'
import { format } from 'date-fns'

interface QuizFlowProps {
  task: MockTask
  onComplete: (score: number) => void
  onStepChange?: (step: number) => void
}

export default function QuizFlow({ task, onComplete, onStepChange }: QuizFlowProps) {
  const [step, setStep] = useState(1)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [hasCheckedAnswer, setHasCheckedAnswer] = useState(false)
  const [answers, setAnswers] = useState<number[]>([])
  const [attempts, setAttempts] = useState(0)

  const totalSteps = 7 // 1 welcome + 5 questions + 1 results

  // Notify parent of step changes for progress bar
  useEffect(() => {
    onStepChange?.(step)
  }, [step, onStepChange])
  const passScore = 4
  const maxAttempts = 3

  const currentQuestion = quizQuestionsData[currentQuestionIndex]
  const score = answers.filter((answer, idx) => answer === quizQuestionsData[idx].correctAnswer).length
  const passed = score >= passScore

  // Step 1: Welcome
  if (step === 1) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center">
          <p className="text-sm text-gray-500 mb-1">Step {step} of {totalSteps}</p>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy-900 mb-2">
            Hi {task.employeeName.split(' ')[0]} 👋
          </h1>
          <p className="text-gray-600">
            {task.company} has assigned you a compliance task
          </p>
        </div>

        {/* Task Card */}
        <div className="bg-gradient-to-br from-purple-50 to-white border border-purple-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Brain size={28} className="text-purple-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-navy-900 mb-2">
                {task.taskName}
              </h2>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <User size={14} />
                  <span>Assigned by: <span className="font-medium text-gray-800">{task.assignedBy}</span></span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar size={14} />
                  <span>Due: <span className="font-medium text-gray-800">{format(new Date(task.dueDate), 'MMMM d, yyyy')}</span></span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-purple-200 space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 rounded-full bg-purple-500" />
              <span>Questions: <span className="font-medium text-gray-800">5 questions</span></span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 rounded-full bg-cyan-500" />
              <span>Pass mark: <span className="font-medium text-gray-800">4 out of 5</span></span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span>Estimated time: <span className="font-medium text-gray-800">Takes about 3 minutes</span></span>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={() => setStep(2)}
          className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
        >
          Start Quiz
          <ChevronRight size={18} />
        </button>
      </div>
    )
  }

  // Steps 2-6: Questions
  if (step >= 2 && step <= 6) {
    const questionNumber = step - 1

    const handleCheckAnswer = () => {
      setHasCheckedAnswer(true)
    }

    const handleNextQuestion = () => {
      if (selectedAnswer !== null) {
        setAnswers([...answers, selectedAnswer])
      }

      if (currentQuestionIndex < quizQuestionsData.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setSelectedAnswer(null)
        setHasCheckedAnswer(false)
        setStep(step + 1)
      } else {
        // Go to results
        setStep(7)
      }
    }

    const isCorrect = selectedAnswer === currentQuestion.correctAnswer

    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center">
          <p className="text-sm text-purple-600 font-semibold mb-1">
            Question {questionNumber} of 5
          </p>
          <h2 className="text-xl sm:text-2xl font-bold text-navy-900 mb-2 leading-snug">
            {currentQuestion.question}
          </h2>
        </div>

        {/* Answer Options */}
        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => {
            const isSelected = selectedAnswer === index
            const isCorrectOption = index === currentQuestion.correctAnswer
            const showCorrect = hasCheckedAnswer && isCorrectOption
            const showWrong = hasCheckedAnswer && isSelected && !isCorrect

            return (
              <button
                key={index}
                onClick={() => !hasCheckedAnswer && setSelectedAnswer(index)}
                disabled={hasCheckedAnswer}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                  showCorrect
                    ? 'bg-green-50 border-green-500 cursor-default'
                    : showWrong
                    ? 'bg-red-50 border-red-500 cursor-default'
                    : isSelected
                    ? 'bg-cyan-50 border-cyan-500 shadow-sm'
                    : 'bg-white border-gray-200 hover:border-cyan-300 hover:shadow-sm cursor-pointer'
                } ${hasCheckedAnswer && 'cursor-default'}`}
              >
                <div className="flex items-center gap-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                    showCorrect
                      ? 'bg-green-500 border-green-500'
                      : showWrong
                      ? 'bg-red-500 border-red-500'
                      : isSelected
                      ? 'bg-cyan-500 border-cyan-500'
                      : 'bg-white border-gray-300'
                  }`}>
                    {showCorrect ? (
                      <CheckCircle size={18} className="text-white" />
                    ) : showWrong ? (
                      <XCircle size={18} className="text-white" />
                    ) : (
                      <span className={`text-sm font-semibold ${
                        isSelected ? 'text-white' : 'text-gray-600'
                      }`}>
                        {String.fromCharCode(65 + index)}
                      </span>
                    )}
                  </div>
                  <span className={`flex-1 ${
                    showCorrect
                      ? 'text-green-900 font-medium'
                      : showWrong
                      ? 'text-red-900 font-medium'
                      : isSelected
                      ? 'text-cyan-900 font-medium'
                      : 'text-gray-700'
                  }`}>
                    {option}
                  </span>
                </div>
              </button>
            )
          })}
        </div>

        {/* Explanation (shown after checking) */}
        {hasCheckedAnswer && (
          <div className={`p-4 rounded-xl border-2 animate-fade-in ${
            isCorrect
              ? 'bg-green-50 border-green-200'
              : 'bg-blue-50 border-blue-200'
          }`}>
            <p className="text-sm text-gray-700 leading-relaxed">
              <span className="font-semibold">{isCorrect ? 'Correct!' : 'Correct answer: ' + currentQuestion.options[currentQuestion.correctAnswer]}</span>
              <br />
              {currentQuestion.explanation}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        {!hasCheckedAnswer ? (
          <button
            onClick={handleCheckAnswer}
            disabled={selectedAnswer === null}
            className={`w-full font-semibold py-4 px-6 rounded-xl transition-all ${
              selectedAnswer !== null
                ? 'bg-cyan-500 hover:bg-cyan-600 text-white shadow-sm hover:shadow-md'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            Check Answer
          </button>
        ) : (
          <button
            onClick={handleNextQuestion}
            className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
          >
            {currentQuestionIndex < quizQuestionsData.length - 1 ? 'Next Question' : 'See Results'}
            <ChevronRight size={18} />
          </button>
        )}
      </div>
    )
  }

  // Step 7: Results
  if (passed) {
    return (
      <div className="space-y-6 animate-fade-in text-center">
        <div>
          <p className="text-sm text-gray-500 mb-4">Results</p>
          <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6 animate-scale-in">
            <CheckCircle size={48} className="text-green-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3">
            Well done, {task.employeeName.split(' ')[0]}!
          </h1>
          <div className="inline-flex items-center gap-3 bg-green-100 px-6 py-3 rounded-full mb-4">
            <Award size={24} className="text-green-600" />
            <span className="text-2xl font-bold text-green-600">
              You scored {score}/5
            </span>
          </div>
          <div className="inline-block px-4 py-2 bg-green-500 text-white font-semibold rounded-lg mb-6">
            Training Passed ✓
          </div>
          <p className="text-lg text-gray-600 mb-8">
            Your training completion has been recorded. Thank you for helping keep {task.company} secure.
          </p>
        </div>

        {/* Completion Card */}
        <div className="bg-gradient-to-br from-green-50 to-white border border-green-200 rounded-2xl p-6 text-left shadow-sm">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Task</span>
              <span className="text-sm font-semibold text-gray-900">{task.taskName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Completed by</span>
              <span className="text-sm font-semibold text-gray-900">{task.employeeName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Date</span>
              <span className="text-sm font-semibold text-gray-900">{format(new Date(), 'MMM d, yyyy')}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Score</span>
              <span className="text-sm font-semibold text-gray-900">{score}/5</span>
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-green-200">
              <span className="text-sm font-medium text-gray-600">Status</span>
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-green-600" />
                <span className="text-sm font-semibold text-green-600">Passed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Note */}
        <div className="pt-4">
          <p className="text-sm text-gray-500">
            You can now close this tab
          </p>
        </div>
      </div>
    )
  }

  // Failed - show retry option
  return (
    <div className="space-y-6 animate-fade-in text-center">
      <div>
        <p className="text-sm text-gray-500 mb-4">Results</p>
        <div className="inline-flex items-center justify-center w-20 h-20 bg-amber-100 rounded-full mb-6 animate-scale-in">
          <AlertTriangle size={48} className="text-amber-600" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3">
          Almost there!
        </h1>
        <div className="inline-flex items-center gap-3 bg-amber-100 px-6 py-3 rounded-full mb-4">
          <Award size={24} className="text-amber-600" />
          <span className="text-2xl font-bold text-amber-600">
            You scored {score}/5
          </span>
        </div>
        <div className="inline-block px-4 py-2 bg-amber-500 text-white font-semibold rounded-lg mb-4">
          Review & Retake
        </div>
        <p className="text-lg text-gray-600 mb-6">
          {attempts < maxAttempts - 1
            ? `You need ${passScore} to pass. Don't worry — review the questions you missed and try again.`
            : attempts === maxAttempts - 1
            ? 'This is your last attempt. Please review carefully before retaking.'
            : 'You\'ve reached the maximum number of attempts. Please contact your IT team for assistance.'}
        </p>
      </div>

      {/* Show incorrect answers */}
      <div className="bg-gradient-to-br from-amber-50 to-white border border-amber-200 rounded-2xl p-6 text-left shadow-sm space-y-4">
        <h3 className="font-semibold text-gray-900 mb-3">Review your answers:</h3>
        {answers.map((answer, idx) => {
          const q = quizQuestionsData[idx]
          const isCorrect = answer === q.correctAnswer
          return (
            <div key={idx} className={`p-3 rounded-lg ${isCorrect ? 'bg-green-50' : 'bg-red-50'}`}>
              <div className="flex items-start gap-2 mb-2">
                {isCorrect ? (
                  <CheckCircle size={16} className="text-green-600 mt-0.5" />
                ) : (
                  <XCircle size={16} className="text-red-600 mt-0.5" />
                )}
                <p className="text-sm font-medium text-gray-900">{q.question}</p>
              </div>
              {!isCorrect && (
                <p className="text-xs text-gray-600 ml-6">
                  Correct answer: <span className="font-semibold">{q.options[q.correctAnswer]}</span>
                </p>
              )}
            </div>
          )
        })}
      </div>

      {/* Retry Button */}
      {attempts < maxAttempts ? (
        <button
          onClick={() => {
            setAttempts(attempts + 1)
            setStep(1)
            setCurrentQuestionIndex(0)
            setSelectedAnswer(null)
            setHasCheckedAnswer(false)
            setAnswers([])
          }}
          className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm hover:shadow-md"
        >
          Retake Quiz
          <ChevronRight size={18} />
        </button>
      ) : (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm text-red-700 text-center">
            Maximum attempts reached. Please contact {task.assignedBy} for help.
          </p>
        </div>
      )}
    </div>
  )
}
