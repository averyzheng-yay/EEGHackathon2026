"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { toast } from "sonner"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { TOPIC_CATEGORIES, type ExpertiseLevel } from "@/lib/types"
import { completeOnboarding } from "@/lib/api"
import { useAuthStore } from "@/lib/store"

const EXPERTISE_LEVELS: { value: ExpertiseLevel; label: string; description: string }[] = [
  {
    value: "beginner",
    label: "Beginner",
    description: "I'm curious about research but prefer plain-language explanations",
  },
  {
    value: "intermediate",
    label: "Intermediate",
    description: "I have some background and like both simplified and technical views",
  },
  {
    value: "expert",
    label: "Expert",
    description: "I'm comfortable with technical papers and want detailed summaries",
  },
]

export default function OnboardingPage() {
  const router = useRouter()
  const { setUser, setNeedsOnboarding } = useAuthStore()
  const [step, setStep] = useState<"interests" | "expertise">("interests")
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [selectedExpertise, setSelectedExpertise] = useState<ExpertiseLevel | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic)
        ? prev.filter((t) => t !== topic)
        : prev.length < 5
        ? [...prev, topic]
        : prev
    )
  }

  const handleContinue = () => {
    if (step === "interests") {
      if (selectedTopics.length < 1) {
        toast.error("Please select at least 1 topic")
        return
      }
      setStep("expertise")
    }
  }

  const handleComplete = async () => {
    if (!selectedExpertise) {
      toast.error("Please select your expertise level")
      return
    }

    setIsLoading(true)
    try {
      const user = await completeOnboarding(selectedTopics, selectedExpertise)
      setUser(user)
      setNeedsOnboarding(false)
      toast.success("You're all set! Enjoy exploring research.")
      router.push("/")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save preferences")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground font-bold text-xl">
            O
          </div>
          <CardTitle className="text-2xl">
            {step === "interests" ? "What interests you?" : "Your expertise level"}
          </CardTitle>
          <CardDescription>
            {step === "interests"
              ? "Select up to 5 topics to personalize your feed (you can change these later)"
              : "This helps us show you the right level of detail"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === "interests" ? (
            <div className="space-y-6">
              {Object.entries(TOPIC_CATEGORIES).map(([category, topics]) => (
                <div key={category}>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">
                    {category}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {topics.map((topic) => {
                      const isSelected = selectedTopics.includes(topic)
                      return (
                        <button
                          key={topic}
                          onClick={() => toggleTopic(topic)}
                          disabled={!isSelected && selectedTopics.length >= 5}
                          className={cn(
                            "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                            isSelected
                              ? "bg-primary text-primary-foreground"
                              : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
                            !isSelected && selectedTopics.length >= 5 && "opacity-50 cursor-not-allowed"
                          )}
                        >
                          {isSelected && <Check className="h-3 w-3" />}
                          {topic}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}

              <div className="flex items-center justify-between pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  {selectedTopics.length}/5 topics selected
                </p>
                <Button onClick={handleContinue} disabled={selectedTopics.length < 1}>
                  Continue
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {EXPERTISE_LEVELS.map((level) => {
                const isSelected = selectedExpertise === level.value
                return (
                  <button
                    key={level.value}
                    onClick={() => setSelectedExpertise(level.value)}
                    className={cn(
                      "w-full text-left rounded-lg border-2 p-4 transition-colors",
                      isSelected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{level.label}</span>
                      {isSelected && (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                          <Check className="h-3 w-3 text-primary-foreground" />
                        </div>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {level.description}
                    </p>
                  </button>
                )
              })}

              <div className="flex items-center justify-between pt-4 border-t">
                <Button variant="ghost" onClick={() => setStep("interests")}>
                  Back
                </Button>
                <Button
                  onClick={handleComplete}
                  disabled={!selectedExpertise || isLoading}
                >
                  {isLoading ? <Spinner className="mr-2" /> : null}
                  Get started
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
