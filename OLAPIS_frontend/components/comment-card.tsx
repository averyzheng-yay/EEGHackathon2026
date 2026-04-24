"use client"

import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { VoteButtons } from "@/components/vote-buttons"
import type { Comment, VoteType } from "@/lib/types"

interface CommentCardProps {
  comment: Comment
  userVote?: VoteType
  onVote?: (vote: "upvote" | "downvote") => void
  onRemoveVote?: () => void
}

export function CommentCard({
  comment,
  userVote,
  onVote,
  onRemoveVote,
}: CommentCardProps) {
  const timeAgo = formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })

  return (
    <div className="py-4 border-b last:border-b-0">
      <div className="flex gap-3">
        {/* Vote buttons */}
        <VoteButtons
          upvotes={comment.upvote_count}
          downvotes={comment.downvote_count}
          userVote={userVote}
          onVote={onVote || (() => {})}
          onRemoveVote={onRemoveVote || (() => {})}
          disabled={!onVote}
          vertical
          size="sm"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <Link
              href={`/u/${comment.author.username}`}
              className="font-medium hover:text-foreground"
            >
              {comment.author.username}
            </Link>
            <span>·</span>
            <time dateTime={comment.created_at}>{timeAgo}</time>
          </div>

          <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
        </div>
      </div>
    </div>
  )
}
