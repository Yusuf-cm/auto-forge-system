// components/ContactForm.tsx
// Working contact form with validation, API submission, and feedback states.
// Demonstrates: controlled inputs, form validation, fetch to API route,
// loading state, success state, error state.
// Every form MUST follow this pattern — never a plain HTML form.

'use client'

import { useState } from 'react'
import { ContactFormData, ContactFormState } from '../types'

export default function ContactForm() {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    message: '',
  })

  const [formState, setFormState] = useState<ContactFormState>({
    status: 'idle',
    message: '',
  })

  const [errors, setErrors] = useState<Partial<ContactFormData>>({})

  // ── Client-side validation ────────────────────────────────
  const validate = (): boolean => {
    const newErrors: Partial<ContactFormData> = {}

    if (!formData.name.trim() || formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters.'
    }
    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'A valid email address is required.'
    }
    if (!formData.message.trim() || formData.message.trim().length < 20) {
      newErrors.message = 'Message must be at least 20 characters.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // ── Form submission ───────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    setFormState({ status: 'loading', message: '' })

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setFormState({ status: 'success', message: data.message })
        setFormData({ name: '', email: '', message: '' })
        setErrors({})
      } else {
        setFormState({
          status: 'error',
          message: data.errors?.join(' ') || 'Something went wrong. Please try again.',
        })
      }
    } catch {
      setFormState({
        status: 'error',
        message: 'Network error. Please check your connection and try again.',
      })
    }
  }

  // ── Input change handler ──────────────────────────────────
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear field error on change
    if (errors[name as keyof ContactFormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const inputStyle = (hasError: boolean): React.CSSProperties => ({
    width: '100%',
    padding: '14px 16px',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    border: `1px solid ${hasError ? '#ff4444' : 'rgba(204, 255, 0, 0.2)'}`,
    color: 'var(--text)',
    fontFamily: "'Inter', sans-serif",
    fontSize: '0.9375rem',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  })

  const errorStyle: React.CSSProperties = {
    color: '#ff4444',
    fontSize: '0.8125rem',
    marginTop: '4px',
    fontFamily: "'Inter', sans-serif",
  }

  // ── Success state ─────────────────────────────────────────
  if (formState.status === 'success') {
    return (
      <div style={{
        padding: '3rem',
        border: '1px solid var(--accent)',
        textAlign: 'center',
        backgroundColor: 'rgba(204, 255, 0, 0.05)',
      }}>
        <p style={{
          fontFamily: "'Bebas Neue', sans-serif",
          fontSize: '1.5rem',
          color: 'var(--accent)',
          marginBottom: '0.5rem',
        }}>
          Message Sent.
        </p>
        <p style={{ color: 'var(--text-muted)', fontFamily: "'Inter', sans-serif" }}>
          {formState.message}
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── Name ─────────────────────────────────────────── */}
      <div>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Your name"
          aria-label="Your name"
          disabled={formState.status === 'loading'}
          style={inputStyle(!!errors.name)}
        />
        {errors.name && <p style={errorStyle}>{errors.name}</p>}
      </div>

      {/* ── Email ────────────────────────────────────────── */}
      <div>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Your email"
          aria-label="Your email"
          disabled={formState.status === 'loading'}
          style={inputStyle(!!errors.email)}
        />
        {errors.email && <p style={errorStyle}>{errors.email}</p>}
      </div>

      {/* ── Message ──────────────────────────────────────── */}
      <div>
        <textarea
          name="message"
          value={formData.message}
          onChange={handleChange}
          placeholder="Your message (min. 20 characters)"
          aria-label="Your message"
          rows={5}
          disabled={formState.status === 'loading'}
          style={{ ...inputStyle(!!errors.message), resize: 'vertical', minHeight: '120px' }}
        />
        {errors.message && <p style={errorStyle}>{errors.message}</p>}
      </div>

      {/* ── API error ────────────────────────────────────── */}
      {formState.status === 'error' && (
        <p style={{ ...errorStyle, fontSize: '0.9375rem' }}>
          {formState.message}
        </p>
      )}

      {/* ── Submit ───────────────────────────────────────── */}
      <button
        type="submit"
        disabled={formState.status === 'loading'}
        style={{
          background: formState.status === 'loading'
            ? 'rgba(204, 255, 0, 0.5)'
            : 'var(--accent)',
          color: 'var(--bg)',
          border: 'none',
          padding: '16px 40px',
          fontFamily: "'Inter', sans-serif",
          fontWeight: 700,
          fontSize: '0.875rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          cursor: formState.status === 'loading' ? 'not-allowed' : 'pointer',
          alignSelf: 'flex-start',
          transition: 'background 0.2s',
        }}
      >
        {formState.status === 'loading' ? 'Sending...' : 'Send Message'}
      </button>

    </form>
  )
}
