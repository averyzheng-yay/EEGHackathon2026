"use client"

import { ArrowUp, ArrowDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { VoteType } from "@/lib/types"

interface VoteButtonsProps {
  upvotes: number
  downvotes: number
  userVote?: VoteType
  onVote: (vote: "upvote" | "downvote") => void
  onRemoveVote: () => void
  disabled?: boolean
  vertical?: boolean
  size?: "sm" | "default"
}

export function VoteButtons({
  upvotes,
  downvotes,
  userVote,
  onVote,
  onRemoveVote,
  disabled = false,
  vertical = false,
  size = "default",
}: VoteButtonsProps) {
  const score = upvotes - downvotes

  const handleUpvote = () => {
    if (userVote === "upvote") {
      onRemoveVote()
    } else {
      onVote("upvote")
    }
  }

  const handleDownvote = () => {
    if (userVote === "downvote") {
      onRemoveVote()
    } else {
      onVote("downvote")
    }
  }

  const iconSize = size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4"
  const buttonSize = size === "sm" ? "h-7 w-7" : "h-8 w-8"

  return (
    <div
      className={cn(
        "flex items-center gap-1",
        vertical && "flex-col"
      )}
    >
      <Button
        variant="ghost"
        size="icon"
        className={cn(
          buttonSize,
          userVote === "upvote" && "text-upvote bg-upvote/10"
        )}
        onClick={handleUpvote}
        disabled={disabled}
      >
        <ArrowUp className={iconSize} />
        <span className="sr-only">Upvote</span>
      </Button>
      
      <span
        className={cn(
          "text-sm font-medium tabular-nums min-w-[2ch] text-center",
          userVote === "upvote" && "text-upvote",
          userVote === "downvote" && "text-downvote"
        )}
      >
        {score}
      </span>
      
      <Button
        variant="ghost"
        size="icon"
        className={cn(
          buttonSize,
          userVote === "downvote" && "text-downvote bg-downvote/10"
        )}
        onClick={handleDownvote}
        disabled={disabled}
      >
        <ArrowDown className={iconSize} />
        <span className="sr-only">Downvote</span>
      </Button>
    </div>
  )
}
