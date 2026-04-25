"use client"

import { use, useState, useCallback } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { formatDistanceToNow } from "date-fns"
import { ArrowLeft, ExternalLink, Sparkles, Eye, EyeOff } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { VoteButtons } from "@/components/vote-buttons"
import { PostCard } from "@/components/post-card"
import { AskAIModal } from "@/components/ask-ai-modal"
import { useAuthStore } from "@/lib/store"
import { getPaper, votePaper, removeVotePaper } from "@/lib/api"
import type { VoteType } from "@/lib/types"

export default function PaperDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const { user } = useAuthStore()
  
  const [paperVote, setPaperVote] = useState<VoteType>(null)
  const [showTechnical, setShowTechnical] = useState(
    user?.expertise_level === "expert"
  )
  const [askAIOpen, setAskAIOpen] = useState(false)

  // Fetch paper
  const { data: paper, error: paperError, isLoading: paperLoading } = useSWR(
    `paper-${id}`,
    () => getPaper(id),
    { revalidateOnFocus: false }
  )

  // Linked posts come from the paper detail response itself
  const linkedPosts = paper?.linked_posts
  const postsLoading = paperLoading

  const handleVote = useCallback(
    async (vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }
      const prevVote = paperVote
      setPaperVote(vote)
      try {
        await votePaper(id, vote)
      } catch {
        setPaperVote(prevVote)
        toast.error("Failed to vote")
      }
    },
    [user, paperVote, id]
  )

  const handleRemoveVote = useCallback(async () => {
    const prevVote = paperVote
    setPaperVote(null)
    try {
      await removeVotePaper(id, prevVote!)
    } catch {
      setPaperVote(prevVote)
      toast.error("Failed to remove vote")
    }
  }, [paperVote, id])

  // Determine which summary to show based on user expertise
  const getSummaryDisplay = () => {
    if (!paper) return null

    const expertiseLevel = user?.expertise_level || "beginner"

    switch (expertiseLevel) {
      case "beginner":
        return (
          <div>
            <h3 className="font-semibold mb-2">Summary</h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {paper.plain_summary}
            </p>
          </div>
        )
      case "intermediate":
        return (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">Summary</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTechnical(!showTechnical)}
                >
                  {showTechnical ? (
                    <>
                      <EyeOff className="h-4 w-4 mr-1.5" />
                      Show Simple
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4 mr-1.5" />
                      Show Technical
                    </>
                  )}
                </Button>
              </div>
              <p className="text-muted-foreground whitespace-pre-wrap">
                {showTechnical ? paper.technical_summary : paper.plain_summary}
              </p>
            </div>
          </div>
        )
      case "expert":
        return (
          <div>
            <h3 className="font-semibold mb-2">Technical Summary</h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {paper.technical_summary}
            </p>
          </div>
        )
      default:
        return (
          <div>
            <h3 className="font-semibold mb-2">Summary</h3>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {paper.plain_summary}
            </p>
          </div>
        )
    }
  }

  if (paperLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <Skeleton className="h-8 w-24 mb-6" />
        <div className="space-y-4">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-3/4" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    )
  }

  if (paperError || !paper) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <p className="text-muted-foreground mb-4">Paper not found</p>
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go back
        </Button>
      </div>
    )
  }

  const ingestedAgo = formatDistanceToNow(new Date(paper.ingested_at), {
    addSuffix: true,
  })

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back button */}
      <Button variant="ghost" className="mb-4" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Paper header */}
          <article>
            {/* Meta info */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <span>{paper.year}</span>
              <span>·</span>
              <span>Added {ingestedAgo}</span>
              <span>·</span>
              <span className="font-mono text-xs">{paper.arxiv_id}</span>
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold mb-3 text-balance">{paper.title}</h1>

            {/* Authors */}
            <p className="text-muted-foreground mb-4">
              {paper.authors.join(", ")}
            </p>

            {/* Tags */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {paper.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4 py-4 border-y mb-6">
              <VoteButtons
                upvotes={paper.upvote_count}
                downvotes={paper.downvote_count}
                userVote={paperVote}
                onVote={handleVote}
                onRemoveVote={handleRemoveVote}
              />
              <Button variant="outline" size="sm" onClick={() => setAskAIOpen(true)}>
                <Sparkles className="h-4 w-4 mr-1.5" />
                Ask AI
              </Button>
              <Button variant="outline" size="sm" asChild>
                <a href={paper.arxiv_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-1.5" />
                  View on arXiv
                </a>
              </Button>
            </div>

            {/* Abstract */}
            <div className="mb-6">
              <h3 className="font-semibold mb-2">Abstract</h3>
              <p className="text-muted-foreground whitespace-pre-wrap">
                {paper.abstract}
              </p>
            </div>

            {/* AI Summary */}
            <div className="mb-6">{getSummaryDisplay()}</div>
          </article>
        </div>

        {/* Sidebar - Related Discussions */}
        <aside className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Related Discussions</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {postsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  ))}
                </div>
              ) : !linkedPosts || linkedPosts.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No discussions linked to this paper yet.
                </p>
              ) : (
                <div className="space-y-3">
                  {linkedPosts.slice(0, 5).map((post) => (
                    <Link
                      key={post.id}
                      href={`/posts/${post.id}`}
                      className="block group"
                    >
                      <p className="text-sm font-medium group-hover:text-primary transition-colors line-clamp-2">
                        {post.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {post.author_username ? `by ${post.author_username} · ` : ""}{post.comment_count} comments
                      </p>
                    </Link>
                  ))}
                  {linkedPosts.length > 5 && (
                    <p className="text-xs text-muted-foreground">
                      +{linkedPosts.length - 5} more discussions
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>

      {/* Ask AI Modal */}
      <AskAIModal paper={paper} open={askAIOpen} onOpenChange={setAskAIOpen} />
    </div>
  )
}
