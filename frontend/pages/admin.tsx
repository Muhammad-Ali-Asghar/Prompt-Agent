import { useState, useEffect } from 'react'
import Head from 'next/head'

interface DocumentInfo {
    doc_id: string
    title: string
    doc_type: string
    version: string
    created_at: string
    chunk_count: number
    embedded: boolean
}

export default function Admin() {
    const [documents, setDocuments] = useState<DocumentInfo[]>([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    // Form state
    const [title, setTitle] = useState('')
    const [docType, setDocType] = useState('skill_card')
    const [content, setContent] = useState('')
    const [version, setVersion] = useState('1.0')

    const fetchDocuments = async () => {
        try {
            const response = await fetch('/api/admin/documents', {
                headers: { 'X-API-Key': 'dev-key-12345' }
            })
            if (response.ok) {
                const data = await response.json()
                setDocuments(data.documents || [])
            }
        } catch (err) {
            console.error('Failed to fetch documents:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDocuments()
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setUploading(true)
        setError(null)
        setSuccess(null)

        try {
            const response = await fetch('/api/admin/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'dev-key-12345',
                },
                body: JSON.stringify({ title, doc_type: docType, content, version }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to upload document')
            }

            const data = await response.json()
            setSuccess(`Successfully ingested "${title}" with ${data.chunk_count} chunks`)
            setTitle('')
            setContent('')
            fetchDocuments()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setUploading(false)
        }
    }

    const handleDelete = async (docId: string) => {
        if (!confirm(`Delete document ${docId}?`)) return

        try {
            const response = await fetch(`/api/admin/documents/${docId}`, {
                method: 'DELETE',
                headers: { 'X-API-Key': 'dev-key-12345' },
            })

            if (response.ok) {
                setSuccess('Document deleted successfully')
                fetchDocuments()
            } else {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to delete document')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        }
    }

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'skill_card': return 'badge-info'
            case 'prompt_pattern': return 'badge-success'
            case 'security_guideline': return 'badge-warning'
            default: return ''
        }
    }

    return (
        <>
            <Head>
                <title>Admin - Prompt RAG Agent</title>
            </Head>

            <div className="container">
                <div style={{ marginBottom: '40px' }}>
                    <h1 style={{ fontSize: '2rem', marginBottom: '8px' }}>Knowledge Base Admin</h1>
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Upload and manage documents for the RAG system
                    </p>
                </div>

                {(error || success) && (
                    <div
                        className={`badge ${error ? 'badge-error' : 'badge-success'}`}
                        style={{ padding: '12px 16px', marginBottom: '24px', display: 'block' }}
                    >
                        {error || success}
                    </div>
                )}

                <div className="grid grid-cols-2" style={{ gap: '32px', alignItems: 'start' }}>
                    {/* Upload Form */}
                    <div className="card">
                        <h2 style={{ marginBottom: '24px', fontSize: '1.25rem' }}>Upload Document</h2>

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">Title</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="Document title..."
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2" style={{ gap: '16px' }}>
                                <div className="form-group">
                                    <label className="form-label">Document Type</label>
                                    <select
                                        className="form-select"
                                        value={docType}
                                        onChange={(e) => setDocType(e.target.value)}
                                    >
                                        <option value="skill_card">Skill Card</option>
                                        <option value="prompt_pattern">Prompt Pattern</option>
                                        <option value="security_guideline">Security Guideline</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Version</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={version}
                                        onChange={(e) => setVersion(e.target.value)}
                                        placeholder="1.0"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Content (Markdown or YAML)</label>
                                <textarea
                                    className="form-textarea"
                                    value={content}
                                    onChange={(e) => setContent(e.target.value)}
                                    placeholder="Paste your document content here..."
                                    style={{ minHeight: '250px', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                className="btn btn-primary"
                                style={{ width: '100%' }}
                                disabled={uploading || !title.trim() || !content.trim()}
                            >
                                {uploading ? (
                                    <>
                                        <span className="spinner" />
                                        Uploading...
                                    </>
                                ) : (
                                    'Upload & Embed Document'
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Documents List */}
                    <div className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Documents</h2>
                            <button className="btn btn-secondary" onClick={fetchDocuments} style={{ padding: '8px 16px' }}>
                                Refresh
                            </button>
                        </div>

                        {loading ? (
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                <span className="spinner" style={{ width: '32px', height: '32px' }} />
                            </div>
                        ) : documents.length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                                No documents in the knowledge base yet.
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {documents.map((doc) => (
                                    <div key={doc.doc_id} className="list-item" style={{ justifyContent: 'space-between' }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 600, marginBottom: '4px' }}>{doc.title}</div>
                                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                <span className={`badge ${getTypeColor(doc.doc_type)}`}>
                                                    {doc.doc_type.replace('_', ' ')}
                                                </span>
                                                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                                    v{doc.version} • {doc.chunk_count} chunks
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            className="btn btn-secondary"
                                            onClick={() => handleDelete(doc.doc_id)}
                                            style={{ padding: '8px 12px', color: 'var(--error)' }}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}
