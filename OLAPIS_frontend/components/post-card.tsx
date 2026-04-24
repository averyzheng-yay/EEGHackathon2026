"use client"

import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { MessageSquare, Sparkles, BookOpen } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { VoteButtons } from "@/components/vote-buttons"
import type { DiscussionPost, VoteType } from "@/lib/types"
import { cn } from "@/lib/utils"

interface PostCardProps {
  post: DiscussionPost
  userVote?: VoteType
  onVote?: (vote: "upvote" | "downvote") => void
  onRemoveVote?: () => void
  onAskAI?: () => void
}

const levelColors = {
  beginner: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  intermediate: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  expert: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

export function PostCard({
  post,
  userVote,
  onVote,
  onRemoveVote,
  onAskAI,
}: PostCardProps) {
  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true })

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <CardContent className="p-4">
        <div className="flex gap-3">
          {/* Vote buttons */}
          <VoteButtons
            upvotes={post.upvote_count}
            downvotes={post.downvote_count}
            userVote={userVote}
            onVote={onVote || (() => {})}
            onRemoveVote={onRemoveVote || (() => {})}
            disabled={!onVote}
            vertical
          />

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <Link
                href={`/u/${post.author.username}`}
                className="font-medium hover:text-foreground"
              >
                {post.author.username}
              </Link>
              <span>·</span>
              <time dateTime={post.created_at}>{timeAgo}</time>
              <Badge
                variant="secondary"
                className={cn("ml-auto text-xs", levelColors[post.technical_level])}
              >
                {post.technical_level}
              </Badge>
            </div>

            {/* Title */}
            <Link href={`/posts/${post.id}`}>
              <h3 className="text-lg font-semibold hover:text-primary transition-colors line-clamp-2 text-balance">
                {post.title}
              </h3>
            </Link>

            {/* Tags */}
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {post.tags.slice(0, 4).map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {post.tags.length > 4 && (
                  <Badge variant="outline" className="text-xs">
                    +{post.tags.length - 4}
                  </Badge>
                )}
              </div>
            )}

            {/* Linked paper indicator */}
            {post.linked_paper && (
              <Link
                href={`/papers/${post.linked_paper.id}`}
                className="mt-2 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span className="truncate">{post.linked_paper.title}</span>
              </Link>
            )}

            {/* Footer */}
            <div className="flex items-center gap-2 mt-3">
              <Link href={`/posts/${post.id}`}>
                <Button variant="ghost" size="sm" className="h-8 text-muted-foreground">
                  <MessageSquare className="h-4 w-4 mr-1.5" />
                  {post.comment_count} comments
                </Button>
              </Link>

              {post.linked_paper && onAskAI && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-muted-foreground"
                  onClick={onAskAI}
                >
                  <Sparkles className="h-4 w-4 mr-1.5" />
                  Ask AI
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
