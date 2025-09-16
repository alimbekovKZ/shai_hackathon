"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { VideoIcon, BrainCircuitIcon, ArrowRightIcon } from "lucide-react"

export function HeroSection() {
  const [meetingUrl, setMeetingUrl] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const extractMeetingDetails = (url: string) => {
    try {
      const urlObj = new URL(url)

      // Extract meeting ID from path (e.g., /j/86096318216)
      const pathMatch = urlObj.pathname.match(/\/j\/(\d+)/)
      const meeting_id = pathMatch ? pathMatch[1] : null

      // Extract password from query parameter
      const meeting_password = urlObj.searchParams.get("pwd")

      return { meeting_id, meeting_password }
    } catch (error) {
      console.error("Invalid URL format:", error)
      return { meeting_id: null, meeting_password: null }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!meetingUrl.trim()) return

    setIsProcessing(true)
    setError(null)
    setResult(null)

    try {
      // Extract meeting details from URL
      const { meeting_id, meeting_password } = extractMeetingDetails(meetingUrl)

      if (!meeting_id) {
        throw new Error("Could not extract meeting ID from URL. Please check the URL format.")
      }

      console.log("[v0] Extracted meeting details:", { meeting_id, meeting_password })

      // Make API request
      const response = await fetch("https://hackathon.shai.pro/api/workflows/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization:
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzZDlhYjg3OC0zNDRmLTQ4YWUtOWU2My1mNDM1ZjA5NjYwYTYiLCJzdWIiOiJXZWIgQVBJIFBhc3Nwb3J0IiwiYXBwX2lkIjoiM2Q5YWI4NzgtMzQ0Zi00OGFlLTllNjMtZjQzNWYwOTY2MGE2IiwiYXBwX2NvZGUiOiJraEt5MkhHeVI0RzJOaWI3IiwiZW5kX3VzZXJfaWQiOiI5ZTcyZTczOS04OTgxLTQ0YjUtOWU3Yy00ZmRiMzllNWU0MWIifQ.wDF826KJswCt0FAHdKHxKTwsGjEdRZHhm5TBw-JUnuc",
        },
        body: JSON.stringify({
          inputs: {
            meeting_id,
            meeting_password,
          },
          response_mode: "streaming",
        }),
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.text()
      console.log("[v0] API response:", data)
      setResult("Meeting processing started successfully!")
    } catch (error) {
      console.error("[v0] Error processing meeting:", error)
      setError(error instanceof Error ? error.message : "An unexpected error occurred")
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <section className="relative py-20 px-4 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-card/50 to-background" />

      <div className="container mx-auto max-w-4xl relative">
        <div className="text-center space-y-8">
          {/* Hero headline */}
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-2 text-primary mb-4">
              <BrainCircuitIcon className="h-8 w-8" />
              <VideoIcon className="h-8 w-8" />
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-balance leading-tight">
              Transform Your Meetings with <span className="text-primary">AI-Powered</span> Insights
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
              Automatically extract action items, create Jira tickets, and generate meeting summaries from your Zoom
              recordings. Save hours of manual work.
            </p>
          </div>

          {/* Main input form */}
          <Card className="p-8 max-w-2xl mx-auto bg-card border-border">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="meeting-url" className="text-sm font-medium text-foreground">
                  Zoom Meeting Link
                </label>
                <Input
                  id="meeting-url"
                  type="url"
                  placeholder="https://us05web.zoom.us/j/86096318216?pwd=..."
                  value={meetingUrl}
                  onChange={(e) => setMeetingUrl(e.target.value)}
                  className="h-12 text-lg bg-input border-border"
                  required
                />
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full h-12 text-lg bg-accent hover:bg-accent/90 text-accent-foreground"
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-accent-foreground mr-2" />
                    Processing Meeting...
                  </>
                ) : (
                  <>
                    Process Now
                    <ArrowRightIcon className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </form>

            {result && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 text-sm">{result}</p>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            <div className="mt-4 text-sm text-muted-foreground text-center">
              Supports Zoom meeting links with meeting ID and password
            </div>
          </Card>

          {/* Trust indicators */}
          <div className="flex items-center justify-center space-x-8 text-muted-foreground text-sm">
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-accent rounded-full" />
              <span>Secure Processing</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-accent rounded-full" />
              <span>GDPR Compliant</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-accent rounded-full" />
              <span>Enterprise Ready</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
