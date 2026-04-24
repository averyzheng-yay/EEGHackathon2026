"use client"

import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { useState, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { QUICK_FILTER_TOPICS } from "@/lib/types"
import { Badge } from "@/components/ui/badge"

interface SearchDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SearchDialog({ open, onOpenChange }: SearchDialogProps) {
  const router = useRouter()
  const [query, setQuery] = useState("")

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (query.trim()) {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`)
        onOpenChange(false)
        setQuery("")
      }
    },
    [query, router, onOpenChange]
  )

  const handleQuickFilter = useCallback(
    (topic: string) => {
      router.push(`/search?q=${encodeURIComponent(topic)}`)
      onOpenChange(false)
    },
    [router, onOpenChange]
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Search OLAPIS</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search papers and discussions..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Quick filters</p>
            <div className="flex flex-wrap gap-2">
              {QUICK_FILTER_TOPICS.map((topic) => (
                <Badge
                  key={topic}
                  variant="secondary"
                  className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                  onClick={() => handleQuickFilter(topic)}
                >
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
