import { useState } from 'react'
import Head from 'next/head'

interface Citation {
    doc_id: string
    title: string
    section: string | null
    reason_used: string
}

interface SelectedSkill {
    id: string
    name: string
    description: string
    when_to_use: string
    relevance_score: number
}

interface SafetyCheck {
    check_name: string
    passed: boolean
    details: string | null
}

interface GenerateResponse {
    final_prompt: string | object
    assumptions: string[]
    safety_checks: SafetyCheck[]
    citations: Citation[]
    selected_skills: SelectedSkill[]
    metadata: Record<string, any>
}

export default function Home() {
    const [userRequest, setUserRequest] = useState('')
    const [targetModel, setTargetModel] = useState('gemini')
    const [promptStyle, setPromptStyle] = useState('detailed')
    const [constraints, setConstraints] = useState('')
    const [context, setContext] = useState('')
    const [outputFormat, setOutputFormat] = useState('plain')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<GenerateResponse | null>(null)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const response = await fetch('/api/generate-prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'dev-key-12345',
                },
                body: JSON.stringify({
                    user_request: userRequest,
                    target_model: targetModel,
                    prompt_style: promptStyle,
                    constraints: constraints.split('\n').filter(c => c.trim()),
                    context: context || null,
                    output_format: outputFormat,
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to generate prompt')
            }

            const data = await response.json()
            setResult(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            <Head>
                <title>Generate Prompt - Prompt RAG Agent</title>
            </Head>

            <div className="container">
                <div style={{ marginBottom: '40px', textAlign: 'center' }}>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '16px', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        Generate High-Quality Prompts
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto' }}>
                        Leverage RAG-powered prompt patterns, skill cards, and security guidelines to create effective prompts for any LLM.
                    </p>
                </div>

                <div className="grid grid-cols-2" style={{ gap: '32px', alignItems: 'start' }}>
                    {/* Form Section */}
                    <div className="card animate-fade-in">
                        <h2 style={{ marginBottom: '24px', fontSize: '1.25rem' }}>Request Details</h2>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">What prompt do you need?</label>
                                <textarea
                                    className="form-textarea"
                                    value={userRequest}
                                    onChange={(e) => setUserRequest(e.target.value)}
                                    placeholder="Describe what you want the prompt to accomplish..."
                                    style={{ minHeight: '150px' }}
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2" style={{ gap: '16px' }}>
                                <div className="form-group">
                                    <label className="form-label">Target Model</label>
                                    <select
                                        className="form-select"
                                        value={targetModel}
                                        onChange={(e) => setTargetModel(e.target.value)}
                                    >
                                        <option value="gemini">Google Gemini</option>
                                        <option value="claude">Anthropic Claude</option>
                                        <option value="gpt">OpenAI GPT</option>
                                        <option value="generic">Generic</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Prompt Style</label>
                                    <select
                                        className="form-select"
                                        value={promptStyle}
                                        onChange={(e) => setPromptStyle(e.target.value)}
                                    >
                                        <option value="concise">Concise</option>
                                        <option value="detailed">Detailed</option>
                                        <option value="step_by_step">Step-by-Step</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Constraints (one per line)</label>
                                <textarea
                                    className="form-textarea"
                                    value={constraints}
                                    onChange={(e) => setConstraints(e.target.value)}
                                    placeholder="Must handle edge cases&#10;Should be under 500 words&#10;Include error handling"
                                    style={{ minHeight: '80px' }}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Project Context (optional)</label>
                                <textarea
                                    className="form-textarea"
                                    value={context}
                                    onChange={(e) => setContext(e.target.value)}
                                    placeholder="Any additional context about your project..."
                                    style={{ minHeight: '80px' }}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Output Format</label>
                                <select
                                    className="form-select"
                                    value={outputFormat}
                                    onChange={(e) => setOutputFormat(e.target.value)}
                                >
                                    <option value="plain">Plain Text</option>
                                    <option value="json">JSON Structured</option>
                                </select>
                            </div>

                            <button
                                type="submit"
                                className="btn btn-primary"
                                style={{ width: '100%', padding: '16px' }}
                                disabled={loading || !userRequest.trim()}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner" />
                                        Generating...
                                    </>
                                ) : (
                                    'Generate Prompt'
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Results Section */}
                    <div className="card animate-fade-in" style={{ animationDelay: '0.1s' }}>
                        <h2 style={{ marginBottom: '24px', fontSize: '1.25rem' }}>Generated Prompt</h2>

                        {error && (
                            <div className="badge badge-error" style={{ padding: '12px 16px', marginBottom: '16px', display: 'block' }}>
                                {error}
                            </div>
                        )}

                        {!result && !error && (
                            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ marginBottom: '16px', opacity: 0.5 }}>
                                    <path d="M14.5 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V7.5L14.5 2z" />
                                    <polyline points="14,2 14,8 20,8" />
                                    <line x1="16" y1="13" x2="8" y2="13" />
                                    <line x1="16" y1="17" x2="8" y2="17" />
                                    <line x1="10" y1="9" x2="8" y2="9" />
                                </svg>
                                <p>Your generated prompt will appear here</p>
                            </div>
                        )}

                        {result && (
                            <div className="animate-fade-in">
                                {/* Final Prompt */}
                                <div style={{ marginBottom: '24px' }}>
                                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Final Prompt</h3>
                                    <div className="code-block" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                        <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                                            {typeof result.final_prompt === 'string'
                                                ? result.final_prompt
                                                : JSON.stringify(result.final_prompt, null, 2)}
                                        </pre>
                                    </div>
                                    <button
                                        className="btn btn-secondary mt-4"
                                        onClick={() => {
                                            const text = typeof result.final_prompt === 'string'
                                                ? result.final_prompt
                                                : JSON.stringify(result.final_prompt, null, 2)
                                            navigator.clipboard.writeText(text)
                                        }}
                                    >
                                        Copy to Clipboard
                                    </button>
                                </div>

                                {/* Selected Skills */}
                                {result.selected_skills.length > 0 && (
                                    <div style={{ marginBottom: '24px' }}>
                                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                            Selected Skills ({result.selected_skills.length})
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {result.selected_skills.map((skill) => (
                                                <div key={skill.id} className="list-item">
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ fontWeight: 600 }}>{skill.name}</div>
                                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                                            {skill.when_to_use}
                                                        </div>
                                                    </div>
                                                    <span className="badge badge-info">
                                                        {(skill.relevance_score * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Citations */}
                                {result.citations.length > 0 && (
                                    <div style={{ marginBottom: '24px' }}>
                                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                            Citations ({result.citations.length})
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {result.citations.map((citation, i) => (
                                                <div key={i} className="list-item">
                                                    <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>[{i + 1}]</span>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ fontWeight: 500 }}>{citation.title}</div>
                                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                                            {citation.reason_used}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Safety Checks */}
                                <div>
                                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                        Safety Checks
                                    </h3>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                        {result.safety_checks.map((check, i) => (
                                            <span
                                                key={i}
                                                className={`badge ${check.passed ? 'badge-success' : 'badge-warning'}`}
                                                title={check.details || undefined}
                                            >
                                                {check.passed ? '✓' : '!'} {check.check_name.replace('Quality: ', '')}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Assumptions */}
                                {result.assumptions.length > 0 && (
                                    <div style={{ marginTop: '24px' }}>
                                        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                            Assumptions
                                        </h3>
                                        <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-secondary)' }}>
                                            {result.assumptions.map((assumption, i) => (
                                                <li key={i} style={{ marginBottom: '4px' }}>{assumption}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}
