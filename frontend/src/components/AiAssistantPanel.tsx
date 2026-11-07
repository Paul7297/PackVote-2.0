import { useState } from 'react'
import { aiTripSummary } from '../api/intelligence'
import { Notice } from './Notice'
import type { AiResponse } from '../types/models'

interface Props {
  tripId: string
}

export function AiAssistantPanel({ tripId }: Props) {
  const [summaryResult, setSummaryResult] = useState<AiResponse | null>(null)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)

  async function handleTripSummary() {
    setIsLoadingSummary(true)
    setSummaryResult(null)
    try {
      const result = await aiTripSummary(tripId)
      setSummaryResult(result)
    } catch (err: unknown) {
      setSummaryResult({
        content: null,
        error: err instanceof Error ? err.message : 'AI service is temporarily unavailable.',
      })
    } finally {
      setIsLoadingSummary(false)
    }
  }

  return (
    <div className="ai-assistant-panel">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Powered by Gemini</span>
            <h3>AI Travel Assistant</h3>
          </div>
          <span className="ai-badge" aria-hidden="true">✨ AI</span>
        </div>

        <p className="ai-description">
          The AI assistant uses your group's ML recommendations, weather data, and cost estimates
          to generate evidence-grounded explanations. It will not invent prices or fabricate scores.
        </p>

        <div className="ai-actions">
          <div className="ai-action-card">
            <h4>📋 Group trip summary</h4>
            <p>Generate a complete summary of your group's preferences, top recommended destinations, and key trade-offs.</p>
            <button
              className="button button--primary"
              type="button"
              disabled={isLoadingSummary}
              onClick={() => void handleTripSummary()}
            >
              {isLoadingSummary ? (
                <>
                  <span className="spinner spinner--small" aria-hidden="true" />
                  {' '}Generating summary…
                </>
              ) : (
                'Generate trip summary'
              )}
            </button>
          </div>

          <div className="ai-action-card ai-action-card--hint">
            <h4>🔍 Destination explanations</h4>
            <p>Open the <strong>Recommendations</strong> tab, expand any destination, and click "Explain this recommendation" to get a detailed AI explanation for that specific destination.</p>
          </div>

          <div className="ai-action-card ai-action-card--hint">
            <h4>⚖ Destination comparison</h4>
            <p>In the <strong>Recommendations</strong> tab, use the "Compare two destinations" tool at the top to get an AI-powered side-by-side comparison.</p>
          </div>
        </div>

        {summaryResult && (
          <div className="ai-result-section">
            <span className="eyebrow">Trip summary</span>
            {summaryResult.error ? (
              <Notice tone="error">{summaryResult.error}</Notice>
            ) : summaryResult.content ? (
              <div className="ai-content ai-content--full">
                {summaryResult.content.split('\n\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            ) : (
              <Notice tone="info">No summary content was returned.</Notice>
            )}
          </div>
        )}

        <div className="ai-disclaimer">
          <strong>Important:</strong> AI-generated content is based only on the evidence provided by the ML engine,
          weather API, and cost model. Always verify important travel details independently.
          The AI does not influence your group's voting or final destination selection.
        </div>
      </div>
    </div>
  )
}
