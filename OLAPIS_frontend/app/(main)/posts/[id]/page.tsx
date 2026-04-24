"use client"

import { use, useState, useCallback, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import useSWRInfinite from "swr/infinite"
import { formatDistanceToNow } from "date-fns"
import { ArrowLeft, BookOpen, Sparkles, Send, RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { VoteButtons } from "@/components/vote-buttons"
import { CommentCard } from "@/components/comment-card"
import { AskAIModal } from "@/components/ask-ai-modal"
import { useAuthStore } from "@/lib/store"
import {
  getDiscussionPost,
  getComments,
  createComment,
  votePost,
  removeVotePost,
  voteComment,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Comment, PaginatedResponse, VoteType } from "@/lib/types"

const levelColors = {
  beginner: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  intermediate: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  expert: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

export default function PostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const { user } = useAuthStore()
  
  const [postVote, setPostVote] = useState<VoteType>(null)
  const [commentVotes, setCommentVotes] = useState<Record<string, VoteType>>({})
  const [newComment, setNewComment] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [askAIOpen, setAskAIOpen] = useState(false)

  // Fetch post
  const { data: post, error: postError, isLoading: postLoading } = useSWR(
    `post-${id}`,
    () => getDiscussionPost(id),
    { revalidateOnFocus: false }
  )

  // Fetch comments with infinite scroll
  const getCommentsKey = (
    pageIndex: number,
    previousPageData: PaginatedResponse<Comment> | null
  ) => {
    if (previousPageData && !previousPageData.has_more) return null
    if (pageIndex === 0) return `comments-${id}-0`
    return `comments-${id}-${pageIndex}-${previousPageData?.cursor}`
  }

  const {
    data: commentsData,
    error: commentsError,
    size: commentsSize,
    setSize: setCommentsSize,
    isLoading: commentsLoading,
    isValidating: commentsValidating,
    mutate: mutateComments,
  } = useSWRInfinite(
    getCommentsKey,
    async (key) => {
      const cursor = key.split("-").pop()
      return getComments(id, cursor === "0" ? undefined : cursor)
    },
    { revalidateFirstPage: false, revalidateOnFocus: false }
  )

  const comments = commentsData?.flatMap((page) => page.items) ?? []
  const hasMoreComments = commentsData?.[commentsData.length - 1]?.has_more ?? false

  // Infinite scroll for comments
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 &&
        hasMoreComments &&
        !commentsValidating
      ) {
        setCommentsSize(commentsSize + 1)
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [hasMoreComments, commentsValidating, commentsSize, setCommentsSize])

  const handlePostVote = useCallback(
    async (vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = postVote
      setPostVote(vote)
      try {
        await votePost(id, vote)
      } catch {
        setPostVote(prevVote)
        toast.error("Failed to vote")
      }
    },
    [user, postVote, id]
  )

  const handleRemovePostVote = useCallback(async () => {
    const prevVote = postVote
    setPostVote(null)
    try {
      await removeVotePost(id)
    } catch {
      setPostVote(prevVote)
      toast.error("Failed to remove vote")
    }
  }, [postVote, id])

  const handleCommentVote = useCallback(
    async (commentId: string, vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = commentVotes[commentId]
      setCommentVotes((prev) => ({ ...prev, [commentId]: vote }))
      try {
        await voteComment(commentId, vote)
      } catch {
        setCommentVotes((prev) => ({ ...prev, [commentId]: prevVote }))
        toast.error("Failed to vote")
      }
    },
    [user, commentVotes]
  )

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) {
      toast.error("Please log in to comment")
      return
    }
    if (!newComment.trim()) return

    setIsSubmitting(true)
    try {
      await createComment(id, newComment.trim())
      setNewComment("")
      mutateComments()
      toast.success("Comment posted!")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to post comment")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (postLoading) {
    return (
      <div className="max-w-3xl mx-auto">
        <Skeleton className="h-8 w-24 mb-6" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    )
  }

  if (postError || !post) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <p className="text-muted-foreground mb-4">Post not found</p>
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go back
        </Button>
      </div>
    )
  }

  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true })

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <Button variant="ghost" className="mb-4" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      {/* Post */}
      <article>
        {/* Header */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
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
        <h1 className="text-2xl font-bold mb-4 text-balance">{post.title}</h1>

        {/* Tags */}
        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {post.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Linked paper */}
        {post.linked_paper && (
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <BookOpen className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-muted-foreground mb-1">Linked Paper</p>
                  <Link
                    href={`/papers/${post.linked_paper.id}`}
                    className="font-medium hover:text-primary transition-colors line-clamp-2"
                  >
                    {post.linked_paper.title}
                  </Link>
                  <p className="text-sm text-muted-foreground mt-1">
                    {post.linked_paper.authors.slice(0, 3).join(", ")}
                    {post.linked_paper.authors.length > 3 &&
                      ` +${post.linked_paper.authors.length - 3} more`}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={() => setAskAIOpen(true)}>
                  <Sparkles className="h-4 w-4 mr-1.5" />
                  Ask AI
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Content */}
        <div className="prose prose-neutral dark:prose-invert max-w-none mb-6">
          <p className="whitespace-pre-wrap">{post.content}</p>
        </div>

        {/* Vote buttons */}
        <div className="flex items-center gap-4 py-4 border-y">
          <VoteButtons
            upvotes={post.upvote_count}
            downvotes={post.downvote_count}
            userVote={postVote}
            onVote={handlePostVote}
            onRemoveVote={handleRemovePostVote}
          />
          <span className="text-sm text-muted-foreground">
            {post.comment_count} comments
          </span>
        </div>
      </article>

      {/* Comment form */}
      <div className="mt-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Comments</h2>
        {user ? (
          <form onSubmit={handleSubmitComment} className="space-y-3">
            <Textarea
              placeholder="Share your thoughts..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={!newComment.trim() || isSubmitting}>
                <Send className="h-4 w-4 mr-2" />
                Post Comment
              </Button>
            </div>
          </form>
        ) : (
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-muted-foreground mb-3">Log in to join the discussion</p>
              <Button asChild>
                <Link href="/login">Log in</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Comments list */}
      <div>
        {commentsLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="py-4 border-b">
                <div className="flex gap-3">
                  <Skeleton className="h-16 w-10" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : commentsError ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">Failed to load comments</p>
            <Button variant="outline" onClick={() => mutateComments()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try again
            </Button>
          </div>
        ) : comments.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">
            No comments yet. Be the first to share your thoughts!
          </p>
        ) : (
          <>
            {comments.map((comment) => (
              <CommentCard
                key={comment.id}
                comment={comment}
                userVote={commentVotes[comment.id]}
                onVote={(vote) => handleCommentVote(comment.id, vote)}
                onRemoveVote={() =>
                  setCommentVotes((prev) => ({ ...prev, [comment.id]: null }))
                }
              />
            ))}

            {commentsValidating && (
              <div className="flex justify-center py-4">
                <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}

            {!hasMoreComments && comments.length > 0 && (
              <p className="text-center text-sm text-muted-foreground py-6">
                End of comments
              </p>
            )}
          </>
        )}
      </div>

      {/* Ask AI Modal */}
      {post.linked_paper && (
        <AskAIModal
          paper={post.linked_paper}
          open={askAIOpen}
          onOpenChange={setAskAIOpen}
        />
      )}
    </div>
  )
}
