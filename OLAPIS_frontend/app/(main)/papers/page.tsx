"use client"

import { useEffect, useState, useCallback } from "react"
import useSWRInfinite from "swr/infinite"
import { RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PaperCard } from "@/components/paper-card"
import { AskAIModal } from "@/components/ask-ai-modal"
import { useAuthStore } from "@/lib/store"
import { getPapersFeed, votePaper, removeVotePaper } from "@/lib/api"
import type { PaperCard as PaperCardType, PaginatedResponse, VoteType } from "@/lib/types"

export default function PapersPage() {
  const { user } = useAuthStore()
  const [askAIPaper, setAskAIPaper] = useState<PaperCardType | null>(null)
  const [userVotes, setUserVotes] = useState<Record<string, VoteType>>({})
  const [voteCounts, setVoteCounts] = useState<Record<string, { upvote_count: number; downvote_count: number }>>({})

  const getKey = (
    pageIndex: number,
    previousPageData: PaginatedResponse<PaperCardType> | null
  ) => {
    if (previousPageData && !previousPageData.has_more) return null
    if (pageIndex === 0) return "papers-page-0"
    return `papers-page-${pageIndex}-${previousPageData?.cursor}`
  }

  const { data, error, size, setSize, isLoading, isValidating, mutate } = useSWRInfinite(
    getKey,
    async (key) => {
      const cursor = key.includes("-") ? key.split("-").pop() : undefined
      return getPapersFeed(cursor === "0" ? undefined : cursor)
    },
    {
      revalidateFirstPage: false,
      revalidateOnFocus: false,
    }
  )

  const papers = data?.flatMap((page) => page.items) ?? []
  const hasMore = data?.[data.length - 1]?.has_more ?? false
  const isEmpty = data?.[0]?.items.length === 0

  // Infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000 &&
        hasMore &&
        !isValidating
      ) {
        setSize(size + 1)
      }
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [hasMore, isValidating, size, setSize])

  const handleVote = useCallback(
    async (paperId: string, vote: "upvote" | "downvote") => {
      if (!user) {
        toast.error("Please log in to vote")
        return
      }

      const prevVote = userVotes[paperId]
      setUserVotes((prev) => ({ ...prev, [paperId]: vote }))
      try {
        const result = await votePaper(paperId, vote)
        setUserVotes((prev) => ({ ...prev, [paperId]: result.user_vote }))
        setVoteCounts((prev) => ({ ...prev, [paperId]: { upvote_count: result.upvote_count, downvote_count: result.downvote_count } }))
      } catch {
        setUserVotes((prev) => ({ ...prev, [paperId]: prevVote }))
        toast.error("Failed to vote")
      }
    },
    [user, userVotes]
  )

  const handleRemoveVote = useCallback(
    async (paperId: string) => {
      const prevVote = userVotes[paperId]
      setUserVotes((prev) => ({ ...prev, [paperId]: null }))
      try {
        const result = await removeVotePaper(paperId, prevVote!)
        setUserVotes((prev) => ({ ...prev, [paperId]: result.user_vote }))
        setVoteCounts((prev) => ({ ...prev, [paperId]: { upvote_count: result.upvote_count, downvote_count: result.downvote_count } }))
      } catch {
        setUserVotes((prev) => ({ ...prev, [paperId]: prevVote }))
        toast.error("Failed to remove vote")
      }
    },
    [userVotes]
  )

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Papers</h1>
        <p className="text-muted-foreground">
          {user
            ? "Latest papers tailored to your interests"
            : "Explore the latest research from arXiv"}
        </p>
      </div>

      {/* Papers grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-lg border p-5 space-y-3">
              <div className="flex justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="h-8 w-16" />
              </div>
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-20 w-full" />
              <div className="flex gap-2">
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-5 w-20 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">Failed to load papers</p>
          <Button variant="outline" onClick={() => mutate()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Try again
          </Button>
        </div>
      ) : isEmpty ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No papers available yet</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {papers.map((paper) => {
              const counts = voteCounts[paper.id]
              return <PaperCard
                key={paper.id}
                paper={{ ...paper, ...(counts ?? {}) }}
                userVote={userVotes[paper.id]}
                onVote={(vote) => handleVote(paper.id, vote)}
                onRemoveVote={() => handleRemoveVote(paper.id)}
                onAskAI={() => setAskAIPaper(paper)}
              />
            })}
          </div>

          {/* Loading more indicator */}
          {isValidating && (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* End of feed */}
          {!hasMore && papers.length > 0 && (
            <p className="text-center text-sm text-muted-foreground py-8">
              {"You've seen all the papers"}
            </p>
          )}
        </>
      )}

      {/* Ask AI Modal */}
      {askAIPaper && (
        <AskAIModal
          paper={askAIPaper}
          open={!!askAIPaper}
          onOpenChange={(open) => !open && setAskAIPaper(null)}
        />
      )}
    </div>
  )
}
