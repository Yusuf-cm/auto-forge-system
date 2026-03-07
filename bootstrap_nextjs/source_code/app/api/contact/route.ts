// app/api/contact/route.ts
// API route for contact form submission.
// This is a Next.js App Router API route — it runs server-side.
// Pattern: validate input → process → return structured JSON response.
// Every form that submits data MUST have a corresponding API route.

import { NextRequest, NextResponse } from 'next/server'
import { ContactFormData } from '../../../types'

export async function POST(request: NextRequest) {
  try {
    const body: ContactFormData = await request.json()

    // ── Input validation ──────────────────────────────────────
    const errors: string[] = []

    if (!body.name || body.name.trim().length < 2) {
      errors.push('Name must be at least 2 characters.')
    }

    if (!body.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)) {
      errors.push('A valid email address is required.')
    }

    if (!body.message || body.message.trim().length < 20) {
      errors.push('Message must be at least 20 characters.')
    }

    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, errors },
        { status: 400 }
      )
    }

    // ── Process submission ────────────────────────────────────
    // In production: send email via Resend, Postmark, or similar.
    // For now: log and return success.
    console.log('Contact form submission:', {
      name: body.name.trim(),
      email: body.email.trim(),
      message: body.message.trim(),
      timestamp: new Date().toISOString(),
    })

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 500))

    return NextResponse.json(
      { success: true, message: 'Message received. We will be in touch within 24 hours.' },
      { status: 200 }
    )

  } catch {
    return NextResponse.json(
      { success: false, errors: ['Server error. Please try again.'] },
      { status: 500 }
    )
  }
}
