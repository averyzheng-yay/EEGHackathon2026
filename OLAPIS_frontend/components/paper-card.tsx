"use client"

import Link from "next/link"
import { ExternalLink, Sparkles } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VoteButtons } from "@/components/vote-buttons"
import type { PaperCard as PaperCardType, VoteType } from "@/lib/types"

interface PaperCardProps {
  paper: PaperCardType
  userVote?: VoteType
  onVote?: (vote: "upvote" | "downvote") => void
  onRemoveVote?: () => void
  onAskAI?: () => void
  compact?: boolean
}

export function PaperCard({
  paper,
  userVote,
  onVote,
  onRemoveVote,
  onAskAI,
  compact = false,
}: PaperCardProps) {
  const authors = paper.authors.slice(0, 3).join(", ")
  const hasMoreAuthors = paper.authors.length > 3

  if (compact) {
    return (
      <Card className="hover:bg-accent/50 transition-colors">
        <CardContent className="p-4">
          <Link href={`/papers/${paper.id}`}>
            <h3 className="font-medium hover:text-primary transition-colors line-clamp-2 text-balance">
              {paper.title}
            </h3>
          </Link>
          <p className="text-sm text-muted-foreground mt-1">
            {authors}
            {hasMoreAuthors && ` +${paper.authors.length - 3} more`}
            {" · "}
            {paper.year}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <VoteButtons
              upvotes={paper.upvote_count}
              downvotes={paper.downvote_count}
              userVote={userVote}
              onVote={onVote || (() => {})}
              onRemoveVote={onRemoveVote || (() => {})}
              disabled={!onVote}
              size="sm"
            />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="hover:bg-accent/50 transition-colors h-full">
      <CardContent className="p-5 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-muted-foreground">
              {authors}
              {hasMoreAuthors && ` +${paper.authors.length - 3} more`}
            </p>
            <p className="text-xs text-muted-foreground">{paper.year}</p>
          </div>
          <VoteButtons
            upvotes={paper.upvote_count}
            downvotes={paper.downvote_count}
            userVote={userVote}
            onVote={onVote || (() => {})}
            onRemoveVote={onRemoveVote || (() => {})}
            disabled={!onVote}
          />
        </div>

        {/* Title */}
        <Link href={`/papers/${paper.id}`} className="group">
          <h3 className="text-lg font-semibold group-hover:text-primary transition-colors line-clamp-3 text-balance mb-3">
            {paper.title}
          </h3>
        </Link>

        {/* Summary preview */}
        <p className="text-sm text-muted-foreground line-clamp-4 flex-1 mb-4">
          {paper.summary_preview}
        </p>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {paper.tags.slice(0, 4).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {paper.tags.length > 4 && (
            <Badge variant="secondary" className="text-xs">
              +{paper.tags.length - 4}
            </Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-auto pt-2 border-t">
          <Button asChild variant="outline" size="sm" className="flex-1">
            <Link href={`/papers/${paper.id}`}>View Paper</Link>
          </Button>
          {onAskAI && (
            <Button variant="outline" size="sm" onClick={onAskAI}>
              <Sparkles className="h-4 w-4 mr-1.5" />
              Ask AI
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
