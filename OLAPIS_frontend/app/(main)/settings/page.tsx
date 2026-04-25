"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Check } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Spinner } from "@/components/ui/spinner"
import { useAuthStore } from "@/lib/store"
import { updateUserSettings } from "@/lib/api"
import { TOPIC_CATEGORIES, type ExpertiseLevel } from "@/lib/types"
import { cn } from "@/lib/utils"

// Mirrors the toSlug helper in lib/api.ts — converts "Artificial Intelligence" → "artificial-intelligence"
const toSlug = (label: string) =>
  label.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")

const EXPERTISE_LEVELS: { value: ExpertiseLevel; label: string; description: string }[] = [
  {
    value: "beginner",
    label: "Beginner",
    description: "Plain-language summaries only",
  },
  {
    value: "intermediate",
    label: "Intermediate",
    description: "Toggle between simple and technical",
  },
  {
    value: "expert",
    label: "Expert",
    description: "Technical summaries by default",
  },
]

export default function SettingsPage() {
  const router = useRouter()
  const { user, setUser } = useAuthStore()
  
  const [selectedTopics, setSelectedTopics] = useState<string[]>(user?.interests || [])
  const [selectedExpertise, setSelectedExpertise] = useState<ExpertiseLevel>(
    user?.expertise_level || "intermediate"
  )
  const [isLoading, setIsLoading] = useState(false)

  if (!user) {
    router.push("/login")
    return null
  }

  // State stores backend slugs; labels are converted on toggle
  const toggleTopic = (topic: string) => {
    const slug = toSlug(topic)
    setSelectedTopics((prev) =>
      prev.includes(slug)
        ? prev.filter((t) => t !== slug)
        : prev.length < 5
        ? [...prev, slug]
        : prev
    )
  }

  const handleSave = async () => {
    if (selectedTopics.length < 1) {
      toast.error("Please select at least 1 topic")
      return
    }

    setIsLoading(true)
    try {
      const updatedUser = await updateUserSettings({
        interests: selectedTopics,
        expertise_level: selectedExpertise,
      })
      setUser(updatedUser)
      toast.success("Settings saved!")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save settings")
    } finally {
      setIsLoading(false)
    }
  }

  const hasChanges =
    JSON.stringify(selectedTopics.sort()) !== JSON.stringify((user.interests || []).sort()) ||
    selectedExpertise !== user.expertise_level

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6">
        {/* Account info */}
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Username</label>
              <p className="text-foreground">{user.username}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">Email</label>
              <p className="text-foreground">{user.email}</p>
            </div>
          </CardContent>
        </Card>

        {/* Expertise level */}
        <Card>
          <CardHeader>
            <CardTitle>Expertise Level</CardTitle>
            <CardDescription>
              Controls which paper summaries you see by default
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              value={selectedExpertise}
              onValueChange={(value: ExpertiseLevel) => setSelectedExpertise(value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPERTISE_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    <div>
                      <span className="font-medium">{level.label}</span>
                      <span className="text-muted-foreground ml-2">
                        — {level.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* Interests */}
        <Card>
          <CardHeader>
            <CardTitle>Interests</CardTitle>
            <CardDescription>
              Select up to 5 topics to personalize your feed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {Object.entries(TOPIC_CATEGORIES).map(([category, topics]) => (
                <div key={category}>
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">
                    {category}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {topics.map((topic) => {
                      const isSelected = selectedTopics.includes(toSlug(topic))
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
                            !isSelected &&
                              selectedTopics.length >= 5 &&
                              "opacity-50 cursor-not-allowed"
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

              <p className="text-sm text-muted-foreground">
                {selectedTopics.length}/5 topics selected
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Save button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={!hasChanges || isLoading}>
            {isLoading ? <Spinner className="mr-2" /> : null}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  )
}
